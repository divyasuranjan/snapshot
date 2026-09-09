// Package queue publishes click events for analytics-worker to consume.
package queue

import (
	"context"
	"time"
)

// ClickEvent describes a single redirect, as observed by shortlink-api.
type ClickEvent struct {
	Code      string
	Timestamp time.Time
	IP        string
	UserAgent string
	Referrer  string
}

// Publisher publishes click events to a queue.
type Publisher interface {
	PublishClick(ctx context.Context, event ClickEvent) error
	// Depth reports the current number of unacknowledged entries in the
	// queue, for exposing as a metric. It returns an error if the queue
	// backend is unreachable.
	Depth(ctx context.Context) (int64, error)
	Ping(ctx context.Context) error
}
