package handlers

import (
	"context"
	"errors"
	"net/http"
	"testing"
	"time"

	"github.com/go-chi/chi/v5"
)

var errPublishBoom = errors.New("boom: publish failed")

// withChiContext returns a context carrying rctx, matching how chi's router
// injects URL params in production so handlers under test can read them via
// chi.URLParam without running the full router.
func withChiContext(r *http.Request, rctx *chi.Context) context.Context {
	return context.WithValue(r.Context(), chi.RouteCtxKey, rctx)
}

// waitForPublish blocks until the publisher has recorded at least n events
// or the timeout elapses, avoiding a flaky sleep-based wait for the
// background click-publish goroutine started by Redirect.
func waitForPublish(t *testing.T, pub *fakePublisher, n int) {
	t.Helper()
	deadline := time.After(2 * time.Second)
	for {
		if len(pub.publishedEvents()) >= n {
			return
		}
		select {
		case <-pub.published:
		case <-deadline:
			t.Fatalf("timed out waiting for %d published event(s), got %d", n, len(pub.publishedEvents()))
		}
	}
}
