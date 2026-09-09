// Package shortcode generates random short codes for links.
package shortcode

import (
	"crypto/rand"
	"fmt"
)

// alphabet is base62: unambiguous, URL-safe, no separators to escape.
const alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

// Generate returns a random code of length n drawn from the base62
// alphabet, using a cryptographically secure random source so codes are
// unguessable.
func Generate(n int) (string, error) {
	if n <= 0 {
		return "", fmt.Errorf("shortcode length must be positive, got %d", n)
	}

	buf := make([]byte, n)
	if _, err := rand.Read(buf); err != nil {
		return "", fmt.Errorf("read random bytes: %w", err)
	}

	code := make([]byte, n)
	for i, b := range buf {
		code[i] = alphabet[int(b)%len(alphabet)]
	}
	return string(code), nil
}
