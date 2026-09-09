package queue

import (
	"context"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
)

func newTestPublisher(t *testing.T) (*RedisStreamPublisher, *redis.Client) {
	t.Helper()
	mr, err := miniredis.Run()
	if err != nil {
		t.Fatalf("start miniredis: %v", err)
	}
	t.Cleanup(mr.Close)

	client := redis.NewClient(&redis.Options{Addr: mr.Addr()})
	t.Cleanup(func() { _ = client.Close() })

	return NewRedisStreamPublisher(client, "clicks", 1000), client
}

func TestRedisStreamPublisher_PublishAndDepth(t *testing.T) {
	pub, client := newTestPublisher(t)
	ctx := context.Background()

	depth, err := pub.Depth(ctx)
	if err != nil {
		t.Fatalf("Depth before publish returned error: %v", err)
	}
	if depth != 0 {
		t.Fatalf("Depth before publish = %d, want 0", depth)
	}

	event := ClickEvent{
		Code:      "abc1234",
		Timestamp: time.Now(),
		IP:        "203.0.113.5",
		UserAgent: "test-agent",
		Referrer:  "https://referrer.example",
	}
	if err := pub.PublishClick(ctx, event); err != nil {
		t.Fatalf("PublishClick returned error: %v", err)
	}

	depth, err = pub.Depth(ctx)
	if err != nil {
		t.Fatalf("Depth after publish returned error: %v", err)
	}
	if depth != 1 {
		t.Fatalf("Depth after publish = %d, want 1", depth)
	}

	entries, err := client.XRange(ctx, "clicks", "-", "+").Result()
	if err != nil {
		t.Fatalf("XRange returned error: %v", err)
	}
	if len(entries) != 1 {
		t.Fatalf("got %d stream entries, want 1", len(entries))
	}
	if entries[0].Values["code"] != "abc1234" {
		t.Fatalf("entry code = %v, want abc1234", entries[0].Values["code"])
	}
	if entries[0].Values["referrer"] != "https://referrer.example" {
		t.Fatalf("entry referrer = %v, want https://referrer.example", entries[0].Values["referrer"])
	}
}

func TestRedisStreamPublisher_Ping(t *testing.T) {
	pub, _ := newTestPublisher(t)
	if err := pub.Ping(context.Background()); err != nil {
		t.Fatalf("Ping returned error: %v", err)
	}
}
