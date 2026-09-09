package handlers

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"time"

	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/httpmw"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/shortcode"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/store"
	"github.com/divyasuranjan/snapshot/services/shortlink-api/internal/validation"
)

type createRequest struct {
	URL string `json:"url"`
}

type createResponse struct {
	Code      string    `json:"code"`
	ShortURL  string    `json:"short_url"`
	LongURL   string    `json:"long_url"`
	CreatedAt time.Time `json:"created_at"`
}

// CreateLink handles POST /api/links: it validates the submitted URL, rate
// limits by caller IP, and stores a newly generated short code for it.
func (s *Server) CreateLink(w http.ResponseWriter, r *http.Request) {
	ip := clientIP(r)

	allowed, err := s.Limiter.Allow(r.Context(), ip)
	if err != nil {
		s.Logger.Error("rate_limit_check_failed", "request_id", httpmw.RequestID(r.Context()), "error", err)
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}
	if !allowed {
		writeError(w, http.StatusTooManyRequests, "rate limit exceeded, try again later")
		return
	}

	var req createRequest
	if err := decodeJSON(w, r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}

	longURL, err := validation.ValidateURL(req.URL)
	if err != nil {
		writeError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}

	link, err := s.createWithUniqueCode(r.Context(), longURL)
	if err != nil {
		s.Logger.Error("create_link_failed", "request_id", httpmw.RequestID(r.Context()), "error", err)
		writeError(w, http.StatusInternalServerError, "internal server error")
		return
	}

	writeJSON(w, http.StatusCreated, createResponse{
		Code:      link.Code,
		ShortURL:  s.BaseURL + "/" + link.Code,
		LongURL:   link.LongURL,
		CreatedAt: link.CreatedAt,
	})
}

// createWithUniqueCode generates a random code and retries on collision up
// to CodeGenMaxAttempts times. Collisions are expected to be extremely rare
// at base62^7 keyspace, so a handful of attempts is a formality, not a real
// bottleneck.
func (s *Server) createWithUniqueCode(ctx context.Context, longURL string) (store.Link, error) {
	var lastErr error
	for attempt := 0; attempt < s.CodeGenMaxAttempts; attempt++ {
		code, err := shortcode.Generate(s.CodeLength)
		if err != nil {
			return store.Link{}, fmt.Errorf("generate code: %w", err)
		}

		link, err := s.Store.Create(ctx, code, longURL)
		if err == nil {
			return link, nil
		}
		if errors.Is(err, store.ErrCodeExists) {
			lastErr = err
			continue
		}
		return store.Link{}, err
	}
	return store.Link{}, fmt.Errorf("exhausted %d attempts generating a unique code: %w", s.CodeGenMaxAttempts, lastErr)
}
