package handlers

import (
	"encoding/json"
	"io"
	"log/slog"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func testLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

func newTestServer(store *fakeStore, pub *fakePublisher, limiter *fakeLimiter) *Server {
	return &Server{
		Store:               store,
		Publisher:           pub,
		Limiter:             limiter,
		Logger:              testLogger(),
		BaseURL:             "http://short.test",
		CodeLength:          7,
		CodeGenMaxAttempts:  5,
		ClickPublishTimeout: time.Second,
	}
}

func TestCreateLink_Success(t *testing.T) {
	srv := newTestServer(newFakeStore(), newFakePublisher(), &fakeLimiter{allow: true})

	body := strings.NewReader(`{"url":"https://example.com/some/page"}`)
	req := httptest.NewRequest("POST", "/api/links", body)
	w := httptest.NewRecorder()

	srv.CreateLink(w, req)

	if w.Code != 201 {
		t.Fatalf("status = %d, want 201, body=%s", w.Code, w.Body.String())
	}

	var resp createResponse
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if resp.LongURL != "https://example.com/some/page" {
		t.Fatalf("LongURL = %q, want original URL", resp.LongURL)
	}
	if len(resp.Code) != 7 {
		t.Fatalf("Code = %q, want length 7", resp.Code)
	}
	if resp.ShortURL != "http://short.test/"+resp.Code {
		t.Fatalf("ShortURL = %q, want composed from BaseURL and code", resp.ShortURL)
	}
}

func TestCreateLink_InvalidURL(t *testing.T) {
	srv := newTestServer(newFakeStore(), newFakePublisher(), &fakeLimiter{allow: true})

	body := strings.NewReader(`{"url":"not-a-url"}`)
	req := httptest.NewRequest("POST", "/api/links", body)
	w := httptest.NewRecorder()

	srv.CreateLink(w, req)

	if w.Code != 422 {
		t.Fatalf("status = %d, want 422, body=%s", w.Code, w.Body.String())
	}
}

func TestCreateLink_MalformedJSON(t *testing.T) {
	srv := newTestServer(newFakeStore(), newFakePublisher(), &fakeLimiter{allow: true})

	body := strings.NewReader(`{"url":`)
	req := httptest.NewRequest("POST", "/api/links", body)
	w := httptest.NewRecorder()

	srv.CreateLink(w, req)

	if w.Code != 400 {
		t.Fatalf("status = %d, want 400, body=%s", w.Code, w.Body.String())
	}
}

func TestCreateLink_RateLimited(t *testing.T) {
	srv := newTestServer(newFakeStore(), newFakePublisher(), &fakeLimiter{allow: false})

	body := strings.NewReader(`{"url":"https://example.com"}`)
	req := httptest.NewRequest("POST", "/api/links", body)
	w := httptest.NewRecorder()

	srv.CreateLink(w, req)

	if w.Code != 429 {
		t.Fatalf("status = %d, want 429, body=%s", w.Code, w.Body.String())
	}
}

func TestCreateLink_GivesUpAfterMaxAttemptsOnPersistentCollision(t *testing.T) {
	// Codes are random, so we can't reliably force a collision through the
	// real store. Instead, a stub that always reports ErrCodeExists proves
	// createWithUniqueCode gives up after CodeGenMaxAttempts rather than
	// retrying forever.
	always := &alwaysCollideStore{}
	srv := newTestServer(newFakeStore(), newFakePublisher(), &fakeLimiter{allow: true})
	srv.CodeGenMaxAttempts = 3
	srv.Store = always

	body := strings.NewReader(`{"url":"https://example.com"}`)
	req := httptest.NewRequest("POST", "/api/links", body)
	w := httptest.NewRecorder()

	srv.CreateLink(w, req)

	if w.Code != 500 {
		t.Fatalf("status = %d, want 500 after exhausting retries, body=%s", w.Code, w.Body.String())
	}
	if always.attempts != 3 {
		t.Fatalf("attempts = %d, want 3 (CodeGenMaxAttempts)", always.attempts)
	}
}
