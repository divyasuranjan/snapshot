package handlers

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/httpmw"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/queue"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/store"
)

// Redirect handles GET /{code}: it looks up the destination URL, redirects
// the caller, and publishes a click event for analytics-worker. Publishing
// is best-effort — a queue outage must not turn into a broken redirect for
// the end user.
func (s *Server) Redirect(w http.ResponseWriter, r *http.Request) {
	code := chi.URLParam(r, "code")
	if code == "" {
		writeError(w, http.StatusNotFound, "not found")
		return
	}

	link, err := s.Store.Get(r.Context(), code)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			writeError(w, http.StatusNotFound, "short link not found")
			return
		}
		s.Logger.Error("lookup_failed", "request_id", httpmw.RequestID(r.Context()), "code", code, "error", err)
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	s.publishClickAsync(code, r)

	http.Redirect(w, r, link.LongURL, http.StatusFound)
}

func (s *Server) publishClickAsync(code string, r *http.Request) {
	event := queue.ClickEvent{
		Code:      code,
		Timestamp: time.Now(),
		IP:        clientIP(r),
		UserAgent: r.UserAgent(),
		Referrer:  r.Referer(),
	}
	requestID := httpmw.RequestID(r.Context())

	go func() {
		ctx, cancel := context.WithTimeout(context.Background(), s.ClickPublishTimeout)
		defer cancel()

		if err := s.Publisher.PublishClick(ctx, event); err != nil {
			s.Logger.Error("publish_click_failed", "request_id", requestID, "code", code, "error", err)
		}
	}()
}
