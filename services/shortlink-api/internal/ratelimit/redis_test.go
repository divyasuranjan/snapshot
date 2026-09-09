package ratelimit

import (
	"context"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
)

func newTestClient(t *testing.T) (*redis.Client, *miniredis.Miniredis) {
	t.Helper()
	mr, err := miniredis.Run()
	if err != nil {
		t.Fatalf("start miniredis: %v", err)
	}
	t.Cleanup(mr.Close)

	client := redis.NewClient(&redis.Options{Addr: mr.Addr()})
	t.Cleanup(func() { _ = client.Close() })
	return client, mr
}

func TestRedisFixedWindow_AllowsUpToLimit(t *testing.T) {
	client, _ := newTestClient(t)
	limiter := NewRedisFixedWindow(client, 3, time.Minute, "test")
	ctx := context.Background()

	for i := 0; i < 3; i++ {
		allowed, err := limiter.Allow(ctx, "1.2.3.4")
		if err != nil {
			t.Fatalf("Allow returned error: %v", err)
		}
		if !allowed {
			t.Fatalf("call %d: got not allowed, want allowed", i+1)
		}
	}

	allowed, err := limiter.Allow(ctx, "1.2.3.4")
	if err != nil {
		t.Fatalf("Allow returned error: %v", err)
	}
	if allowed {
		t.Fatal("4th call within the window: got allowed, want rate limited")
	}
}

func TestRedisFixedWindow_KeysAreIndependent(t *testing.T) {
	client, _ := newTestClient(t)
	limiter := NewRedisFixedWindow(client, 1, time.Minute, "test")
	ctx := context.Background()

	allowedA, err := limiter.Allow(ctx, "client-a")
	if err != nil || !allowedA {
		t.Fatalf("client-a first call: allowed=%v err=%v, want allowed", allowedA, err)
	}

	allowedB, err := limiter.Allow(ctx, "client-b")
	if err != nil || !allowedB {
		t.Fatalf("client-b first call: allowed=%v err=%v, want allowed (different key)", allowedB, err)
	}

	allowedA2, err := limiter.Allow(ctx, "client-a")
	if err != nil {
		t.Fatalf("client-a second call returned error: %v", err)
	}
	if allowedA2 {
		t.Fatal("client-a second call: got allowed, want rate limited")
	}
}

func TestRedisFixedWindow_ResetsAfterWindow(t *testing.T) {
	client, mr := newTestClient(t)
	limiter := NewRedisFixedWindow(client, 1, time.Second, "test")
	ctx := context.Background()

	allowed, err := limiter.Allow(ctx, "1.2.3.4")
	if err != nil || !allowed {
		t.Fatalf("first call: allowed=%v err=%v, want allowed", allowed, err)
	}

	allowed, err = limiter.Allow(ctx, "1.2.3.4")
	if err != nil {
		t.Fatalf("second call returned error: %v", err)
	}
	if allowed {
		t.Fatal("second call within window: got allowed, want rate limited")
	}

	mr.FastForward(2 * time.Second)

	allowed, err = limiter.Allow(ctx, "1.2.3.4")
	if err != nil {
		t.Fatalf("call after window expiry returned error: %v", err)
	}
	if !allowed {
		t.Fatal("call after window expiry: got rate limited, want allowed")
	}
}
