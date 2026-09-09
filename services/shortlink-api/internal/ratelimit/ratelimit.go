// Package ratelimit provides request rate limiting for the link-creation
// endpoint.
package ratelimit

import "context"

// Limiter decides whether a request identified by key should be allowed.
type Limiter interface {
	// Allow reports whether the caller identified by key may proceed. It
	// returns an error only on backend failure, never as a way to signal
	// "not allowed" (that's the bool).
	Allow(ctx context.Context, key string) (bool, error)
}
