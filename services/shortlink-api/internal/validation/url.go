// Package validation validates and normalizes user-supplied input.
package validation

import (
	"errors"
	"net/url"
	"strings"
)

// MaxURLLength bounds submitted URLs to something a browser and Postgres
// text column can comfortably handle.
const MaxURLLength = 2048

var (
	ErrEmpty       = errors.New("url is required")
	ErrTooLong     = errors.New("url exceeds maximum length")
	ErrMalformed   = errors.New("url is not a valid absolute URL")
	ErrScheme      = errors.New("url must use http or https")
	ErrMissingHost = errors.New("url must include a host")
)

// ValidateURL checks that raw is a well-formed, absolute http(s) URL and
// returns its normalized (trimmed) form.
func ValidateURL(raw string) (string, error) {
	trimmed := strings.TrimSpace(raw)

	if trimmed == "" {
		return "", ErrEmpty
	}
	if len(trimmed) > MaxURLLength {
		return "", ErrTooLong
	}

	u, err := url.ParseRequestURI(trimmed)
	if err != nil {
		return "", ErrMalformed
	}

	switch u.Scheme {
	case "http", "https":
	default:
		return "", ErrScheme
	}

	if u.Host == "" {
		return "", ErrMissingHost
	}

	return trimmed, nil
}
