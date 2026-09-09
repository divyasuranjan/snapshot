package handlers

import (
	"net/http/httptest"
	"testing"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/store"
)

func TestRedirect_Found(t *testing.T) {
	fs := newFakeStore()
	fs.links["abc1234"] = store.Link{Code: "abc1234", LongURL: "https://example.com/target", CreatedAt: time.Now()}
	pub := newFakePublisher()
	srv := newTestServer(fs, pub, &fakeLimiter{allow: true})

	req := httptest.NewRequest("GET", "/abc1234", nil)
	req.Header.Set("Referer", "https://google.com")
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("code", "abc1234")
	req = req.WithContext(withChiContext(req, rctx))
	w := httptest.NewRecorder()

	srv.Redirect(w, req)

	if w.Code != 302 {
		t.Fatalf("status = %d, want 302, body=%s", w.Code, w.Body.String())
	}
	if loc := w.Header().Get("Location"); loc != "https://example.com/target" {
		t.Fatalf("Location = %q, want https://example.com/target", loc)
	}

	waitForPublish(t, pub, 1)
	events := pub.publishedEvents()
	if events[0].Code != "abc1234" {
		t.Fatalf("published event code = %q, want abc1234", events[0].Code)
	}
	if events[0].Referrer != "https://google.com" {
		t.Fatalf("published event referrer = %q, want https://google.com", events[0].Referrer)
	}
}

func TestRedirect_NotFound(t *testing.T) {
	srv := newTestServer(newFakeStore(), newFakePublisher(), &fakeLimiter{allow: true})

	req := httptest.NewRequest("GET", "/doesnotexist", nil)
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("code", "doesnotexist")
	req = req.WithContext(withChiContext(req, rctx))
	w := httptest.NewRecorder()

	srv.Redirect(w, req)

	if w.Code != 404 {
		t.Fatalf("status = %d, want 404, body=%s", w.Code, w.Body.String())
	}
}

func TestRedirect_QueuePublishFailureDoesNotBreakRedirect(t *testing.T) {
	fs := newFakeStore()
	fs.links["abc1234"] = store.Link{Code: "abc1234", LongURL: "https://example.com/target", CreatedAt: time.Now()}
	pub := newFakePublisher()
	pub.publishErr = errPublishBoom
	srv := newTestServer(fs, pub, &fakeLimiter{allow: true})

	req := httptest.NewRequest("GET", "/abc1234", nil)
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("code", "abc1234")
	req = req.WithContext(withChiContext(req, rctx))
	w := httptest.NewRecorder()

	srv.Redirect(w, req)

	if w.Code != 302 {
		t.Fatalf("status = %d, want 302 even when publish fails, body=%s", w.Code, w.Body.String())
	}
}
