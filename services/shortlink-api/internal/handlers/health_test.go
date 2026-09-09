package handlers

import (
	"errors"
	"net/http/httptest"
	"testing"
)

func TestHealthz_AlwaysOK(t *testing.T) {
	srv := newTestServer(newFakeStore(), newFakePublisher(), &fakeLimiter{allow: true})

	req := httptest.NewRequest("GET", "/healthz", nil)
	w := httptest.NewRecorder()
	srv.Healthz(w, req)

	if w.Code != 200 {
		t.Fatalf("status = %d, want 200", w.Code)
	}
}

func TestReadyz_AllDependenciesUp(t *testing.T) {
	srv := newTestServer(newFakeStore(), newFakePublisher(), &fakeLimiter{allow: true})

	req := httptest.NewRequest("GET", "/readyz", nil)
	w := httptest.NewRecorder()
	srv.Readyz(w, req)

	if w.Code != 200 {
		t.Fatalf("status = %d, want 200, body=%s", w.Code, w.Body.String())
	}
}

func TestReadyz_DatabaseDown(t *testing.T) {
	fs := newFakeStore()
	fs.pingErr = errors.New("connection refused")
	srv := newTestServer(fs, newFakePublisher(), &fakeLimiter{allow: true})

	req := httptest.NewRequest("GET", "/readyz", nil)
	w := httptest.NewRecorder()
	srv.Readyz(w, req)

	if w.Code != 503 {
		t.Fatalf("status = %d, want 503, body=%s", w.Code, w.Body.String())
	}
}

func TestReadyz_RedisDown(t *testing.T) {
	pub := newFakePublisher()
	pub.pingErr = errors.New("connection refused")
	srv := newTestServer(newFakeStore(), pub, &fakeLimiter{allow: true})

	req := httptest.NewRequest("GET", "/readyz", nil)
	w := httptest.NewRecorder()
	srv.Readyz(w, req)

	if w.Code != 503 {
		t.Fatalf("status = %d, want 503, body=%s", w.Code, w.Body.String())
	}
}
