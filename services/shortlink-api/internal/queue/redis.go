package queue

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// RedisStreamPublisher publishes click events onto a Redis Stream.
type RedisStreamPublisher struct {
	client *redis.Client
	stream string
	// maxLen approximately caps the stream length (via MAXLEN ~) so an
	// idle consumer can't grow it unbounded on a memory-constrained node.
	maxLen int64
}

// NewRedisStreamPublisher wraps an existing Redis client to publish onto
// the given stream. The caller owns the client's lifecycle (it may be
// shared with other Redis-backed components, e.g. the rate limiter).
func NewRedisStreamPublisher(client *redis.Client, stream string, maxLen int64) *RedisStreamPublisher {
	return &RedisStreamPublisher{client: client, stream: stream, maxLen: maxLen}
}

func (p *RedisStreamPublisher) PublishClick(ctx context.Context, event ClickEvent) error {
	values := map[string]interface{}{
		"code":       event.Code,
		"timestamp":  event.Timestamp.UTC().Format(time.RFC3339Nano),
		"ip":         event.IP,
		"user_agent": event.UserAgent,
		"referrer":   event.Referrer,
	}

	err := p.client.XAdd(ctx, &redis.XAddArgs{
		Stream: p.stream,
		MaxLen: p.maxLen,
		Approx: true,
		Values: values,
	}).Err()
	if err != nil {
		return fmt.Errorf("xadd click event: %w", err)
	}
	return nil
}

func (p *RedisStreamPublisher) Depth(ctx context.Context) (int64, error) {
	n, err := p.client.XLen(ctx, p.stream).Result()
	if err != nil {
		return 0, fmt.Errorf("xlen: %w", err)
	}
	return n, nil
}

func (p *RedisStreamPublisher) Ping(ctx context.Context) error {
	return p.client.Ping(ctx).Err()
}
