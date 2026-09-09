// Package handlers implements shortlink-api's HTTP surface: link creation,
// redirects, and health/metrics endpoints.
package handlers

import (
	"log/slog"
	"net/http"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/httpmw"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/queue"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/ratelimit"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/store"
)

// Server holds shortlink-api's dependencies and builds its HTTP routes.
type Server struct {
	Store     store.LinkStore
	Publisher queue.Publisher
	Limiter   ratelimit.Limiter
	Logger    *slog.Logger

	BaseURL             string
	CodeLength          int
	CodeGenMaxAttempts  int
	ClickPublishTimeout time.Duration
}

// Routes builds the HTTP handler tree.
func (s *Server) Routes() http.Handler {
	r := chi.NewRouter()
	r.Use(httpmw.RequestIDMiddleware)
	r.Use(httpmw.Recover(s.Logger))
	r.Use(httpmw.Logging(s.Logger))

	r.Get("/healthz", s.Healthz)
	r.Get("/readyz", s.Readyz)
	r.Handle("/metrics", metricsHandler())

	r.Post("/api/links", s.withMetrics("/api/links", s.CreateLink))
	r.Get("/{code}", s.withMetrics("/{code}", s.Redirect))

	return r
}

// clientIP extracts the caller's IP for rate limiting and click logging. It
// trusts X-Forwarded-For's first hop, which is only meaningful behind a
// reverse proxy/ingress that sets it; falling back to RemoteAddr keeps this
// safe when running directly.
func clientIP(r *http.Request) string {
	if fwd := r.Header.Get("X-Forwarded-For"); fwd != "" {
		parts := strings.Split(fwd, ",")
		if ip := strings.TrimSpace(parts[0]); ip != "" {
			return ip
		}
	}
	host := r.RemoteAddr
	if idx := strings.LastIndex(host, ":"); idx != -1 {
		return host[:idx]
	}
	return host
}
