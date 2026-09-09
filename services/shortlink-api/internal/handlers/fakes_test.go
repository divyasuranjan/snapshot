package handlers

import (
	"context"
	"sync"
	"time"

	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/queue"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/store"
)

// fakeStore is an in-memory LinkStore for handler tests.
type fakeStore struct {
	mu    sync.Mutex
	links map[string]store.Link

	pingErr   error
	createErr error
}

func newFakeStore() *fakeStore {
	return &fakeStore{links: make(map[string]store.Link)}
}

func (f *fakeStore) Create(ctx context.Context, code, longURL string) (store.Link, error) {
	f.mu.Lock()
	defer f.mu.Unlock()

	if f.createErr != nil {
		return store.Link{}, f.createErr
	}
	if _, exists := f.links[code]; exists {
		return store.Link{}, store.ErrCodeExists
	}
	link := store.Link{Code: code, LongURL: longURL, CreatedAt: time.Now()}
	f.links[code] = link
	return link, nil
}

func (f *fakeStore) Get(ctx context.Context, code string) (store.Link, error) {
	f.mu.Lock()
	defer f.mu.Unlock()

	link, ok := f.links[code]
	if !ok {
		return store.Link{}, store.ErrNotFound
	}
	return link, nil
}

func (f *fakeStore) Ping(ctx context.Context) error { return f.pingErr }
func (f *fakeStore) Close()                         {}

// alwaysCollideStore is a LinkStore stub whose Create always reports a code
// collision, used to test that code generation gives up after a bounded
// number of attempts instead of retrying forever.
type alwaysCollideStore struct {
	attempts int
}

func (s *alwaysCollideStore) Create(ctx context.Context, code, longURL string) (store.Link, error) {
	s.attempts++
	return store.Link{}, store.ErrCodeExists
}

func (s *alwaysCollideStore) Get(ctx context.Context, code string) (store.Link, error) {
	return store.Link{}, store.ErrNotFound
}

func (s *alwaysCollideStore) Ping(ctx context.Context) error { return nil }
func (s *alwaysCollideStore) Close()                         {}

// fakePublisher is an in-memory queue.Publisher for handler tests.
// Redirect handles publishing on a background goroutine, so tests observe
// completion through the buffered `published` channel rather than a sleep.
type fakePublisher struct {
	mu     sync.Mutex
	events []queue.ClickEvent

	publishErr error
	pingErr    error
	depth      int64

	published chan queue.ClickEvent
}

func newFakePublisher() *fakePublisher {
	return &fakePublisher{published: make(chan queue.ClickEvent, 16)}
}

func (f *fakePublisher) PublishClick(ctx context.Context, event queue.ClickEvent) error {
	if f.publishErr != nil {
		return f.publishErr
	}
	f.mu.Lock()
	f.events = append(f.events, event)
	f.mu.Unlock()

	select {
	case f.published <- event:
	default:
	}
	return nil
}

func (f *fakePublisher) Depth(ctx context.Context) (int64, error) {
	return f.depth, nil
}

func (f *fakePublisher) Ping(ctx context.Context) error { return f.pingErr }

func (f *fakePublisher) publishedEvents() []queue.ClickEvent {
	f.mu.Lock()
	defer f.mu.Unlock()
	out := make([]queue.ClickEvent, len(f.events))
	copy(out, f.events)
	return out
}

// fakeLimiter is a controllable ratelimit.Limiter for handler tests.
type fakeLimiter struct {
	allow bool
	err   error
}

func (f *fakeLimiter) Allow(ctx context.Context, key string) (bool, error) {
	return f.allow, f.err
}
