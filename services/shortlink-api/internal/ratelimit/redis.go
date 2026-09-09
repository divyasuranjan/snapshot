package ratelimit

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// incrAndExpire atomically increments the counter and, only on the first
// increment within the window, sets its TTL. Running both steps in one
// script avoids a race where a crash between INCR and EXPIRE would leave a
// key that never expires.
const incrAndExpire = `
local count = redis.call("INCR", KEYS[1])
if count == 1 then
	redis.call("PEXPIRE", KEYS[1], ARGV[1])
end
return count
`

// RedisFixedWindow is a fixed-window rate limiter backed by Redis: each key
// gets at most `limit` allowed calls per `window`.
type RedisFixedWindow struct {
	client *redis.Client
	limit  int64
	window time.Duration
	prefix string
	script *redis.Script
}

// NewRedisFixedWindow builds a limiter allowing `limit` calls per `window`
// for any given key. keyPrefix namespaces the Redis keys it creates.
func NewRedisFixedWindow(client *redis.Client, limit int64, window time.Duration, keyPrefix string) *RedisFixedWindow {
	return &RedisFixedWindow{
		client: client,
		limit:  limit,
		window: window,
		prefix: keyPrefix,
		script: redis.NewScript(incrAndExpire),
	}
}

func (l *RedisFixedWindow) Allow(ctx context.Context, key string) (bool, error) {
	redisKey := l.prefix + ":" + key
	windowMs := l.window.Milliseconds()

	res, err := l.script.Run(ctx, l.client, []string{redisKey}, windowMs).Result()
	if err != nil {
		return false, fmt.Errorf("rate limit script: %w", err)
	}

	count, ok := res.(int64)
	if !ok {
		return false, fmt.Errorf("unexpected rate limit script result type %T", res)
	}

	return count <= l.limit, nil
}
