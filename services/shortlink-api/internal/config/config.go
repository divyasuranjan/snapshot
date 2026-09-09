// Package config loads shortlink-api's configuration from environment
// variables, the only configuration source in a container/Kubernetes
// deployment.
package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

// Config holds all runtime configuration for shortlink-api.
type Config struct {
	Port        string
	BaseURL     string
	DatabaseURL string

	RedisAddr     string
	RedisPassword string
	RedisDB       int
	RedisStream   string
	// RedisStreamMaxLen approximately caps the click-events stream length.
	RedisStreamMaxLen int64

	CodeLength         int
	CodeGenMaxAttempts int

	RateLimitPerMinute int64

	ShutdownTimeout time.Duration
}

// Load reads configuration from the environment, applying defaults for
// anything optional and returning an error for anything required but
// missing.
func Load() (Config, error) {
	cfg := Config{
		Port:               getEnv("PORT", "8080"),
		BaseURL:            getEnv("BASE_URL", "http://localhost:8080"),
		DatabaseURL:        os.Getenv("DATABASE_URL"),
		RedisAddr:          getEnv("REDIS_ADDR", "localhost:6379"),
		RedisPassword:      os.Getenv("REDIS_PASSWORD"),
		RedisStream:        getEnv("REDIS_STREAM", "clicks"),
		CodeLength:         7,
		CodeGenMaxAttempts: 5,
		ShutdownTimeout:    10 * time.Second,
	}

	var err error
	if cfg.DatabaseURL == "" {
		return Config{}, fmt.Errorf("DATABASE_URL is required")
	}

	if cfg.RedisDB, err = getEnvInt("REDIS_DB", 0); err != nil {
		return Config{}, err
	}
	if cfg.RedisStreamMaxLen, err = getEnvInt64("REDIS_STREAM_MAXLEN", 100_000); err != nil {
		return Config{}, err
	}
	if cfg.RateLimitPerMinute, err = getEnvInt64("RATE_LIMIT_PER_MINUTE", 20); err != nil {
		return Config{}, err
	}

	return cfg, nil
}

func getEnv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func getEnvInt(key string, def int) (int, error) {
	v := os.Getenv(key)
	if v == "" {
		return def, nil
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return 0, fmt.Errorf("invalid %s: %w", key, err)
	}
	return n, nil
}

func getEnvInt64(key string, def int64) (int64, error) {
	v := os.Getenv(key)
	if v == "" {
		return def, nil
	}
	n, err := strconv.ParseInt(v, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("invalid %s: %w", key, err)
	}
	return n, nil
}
