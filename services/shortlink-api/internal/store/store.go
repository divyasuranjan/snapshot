// Package store defines the persistence interface for short links and the
// Postgres-backed implementation used in production.
package store

import (
	"context"
	"errors"
	"time"
)

// ErrNotFound is returned when a code has no matching link.
var ErrNotFound = errors.New("link not found")

// ErrCodeExists is returned when attempting to create a link whose code is
// already taken, so callers can retry with a new code.
var ErrCodeExists = errors.New("code already exists")

// Link is a short code mapped to a destination URL.
type Link struct {
	Code      string
	LongURL   string
	CreatedAt time.Time
}

// LinkStore persists and retrieves short links.
type LinkStore interface {
	// Create inserts a new link. It returns ErrCodeExists if code is taken.
	Create(ctx context.Context, code, longURL string) (Link, error)
	// Get looks up a link by code. It returns ErrNotFound if none exists.
	Get(ctx context.Context, code string) (Link, error)
	// Ping verifies connectivity to the underlying store.
	Ping(ctx context.Context) error
	// Close releases any underlying resources.
	Close()
}
