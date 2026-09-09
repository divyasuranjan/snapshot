// Command server runs shortlink-api: it creates short links, redirects
// visitors, and publishes click events for analytics-worker to consume.
package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/redis/go-redis/v9"

	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/config"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/handlers"
	appmetrics "github.com/divyasuranjan/snapshot/services/shortlink-api/internal/metrics"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/queue"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/ratelimit"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/store"
)

// clickPublishTimeout bounds the best-effort background publish of a click
// event, so a stalled Redis connection can't leak goroutines.
const clickPublishTimeout = 3 * time.Second

// queueDepthPollInterval controls how often the click-queue-depth gauge is
// refreshed; it's a coarse observability signal, not a hot path.
const queueDepthPollInterval = 10 * time.Second

func main() {
	// The distroless base image this binary ships in has no shell, so a
	// Docker/Compose HEALTHCHECK can't exec curl or wget. This flag gives
	// the binary itself a self-check mode instead of trading away the
	// no-shell image for one with a shell just to satisfy HEALTHCHECK.
	if len(os.Args) > 1 && os.Args[1] == "healthcheck" {
		os.Exit(runHealthcheck())
	}

	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	if err := run(logger); err != nil {
		logger.Error("fatal", "error", err)
		os.Exit(1)
	}
}

func runHealthcheck() int {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	client := http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get("http://127.0.0.1:" + port + "/healthz")
	if err != nil {
		return 1
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return 1
	}
	return 0
}

func run(logger *slog.Logger) error {
	cfg, err := config.Load()
	if err != nil {
		return err
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	pgStore, err := store.NewPostgresStore(ctx, cfg.DatabaseURL)
	if err != nil {
		return err
	}
	defer pgStore.Close()

	redisClient := redis.NewClient(&redis.Options{
		Addr:     cfg.RedisAddr,
		Password: cfg.RedisPassword,
		DB:       cfg.RedisDB,
	})
	defer redisClient.Close()

	pingCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	err = redisClient.Ping(pingCtx).Err()
	cancel()
	if err != nil {
		return err
	}

	publisher := queue.NewRedisStreamPublisher(redisClient, cfg.RedisStream, cfg.RedisStreamMaxLen)
	limiter := ratelimit.NewRedisFixedWindow(redisClient, cfg.RateLimitPerMinute, time.Minute, "ratelimit:create")

	srv := &handlers.Server{
		Store:               pgStore,
		Publisher:           publisher,
		Limiter:             limiter,
		Logger:              logger,
		BaseURL:             cfg.BaseURL,
		CodeLength:          cfg.CodeLength,
		CodeGenMaxAttempts:  cfg.CodeGenMaxAttempts,
		ClickPublishTimeout: clickPublishTimeout,
	}

	go pollQueueDepth(ctx, publisher, logger)

	httpServer := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           srv.Routes(),
		ReadHeaderTimeout: 5 * time.Second,
	}

	serveErr := make(chan error, 1)
	go func() {
		logger.Info("starting", "port", cfg.Port, "base_url", cfg.BaseURL)
		if err := httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			serveErr <- err
			return
		}
		serveErr <- nil
	}()

	select {
	case err := <-serveErr:
		return err
	case <-ctx.Done():
		logger.Info("shutdown_signal_received")
	}

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), cfg.ShutdownTimeout)
	defer shutdownCancel()

	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		return err
	}

	logger.Info("shutdown_complete")
	return nil
}

// pollQueueDepth periodically refreshes the click-queue-depth gauge until
// ctx is cancelled. A failed read is logged and skipped rather than
// treated as fatal — metrics collection must never take the service down.
func pollQueueDepth(ctx context.Context, publisher queue.Publisher, logger *slog.Logger) {
	ticker := time.NewTicker(queueDepthPollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			depth, err := publisher.Depth(ctx)
			if err != nil {
				logger.Warn("queue_depth_poll_failed", "error", err)
				continue
			}
			appmetrics.QueueDepth.Set(float64(depth))
		}
	}
}
