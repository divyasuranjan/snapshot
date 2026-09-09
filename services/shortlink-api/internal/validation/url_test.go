package validation

import (
	"errors"
	"strings"
	"testing"
)

func TestValidateURL(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		wantErr error
	}{
		{"valid https", "https://example.com/path?q=1", nil},
		{"valid http", "http://example.com", nil},
		{"trims whitespace", "  https://example.com  ", nil},
		{"empty", "", ErrEmpty},
		{"whitespace only", "   ", ErrEmpty},
		{"missing scheme", "example.com", ErrMalformed},
		{"unsupported scheme", "ftp://example.com", ErrScheme},
		{"javascript scheme rejected", "javascript:alert(1)", ErrScheme},
		{"malformed", "http://[::1", ErrMalformed},
		{"scheme only, no host", "https://", ErrMissingHost},
		{"too long", "https://example.com/" + strings.Repeat("a", MaxURLLength), ErrTooLong},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := ValidateURL(tt.input)
			if tt.wantErr == nil {
				if err != nil {
					t.Fatalf("ValidateURL(%q) = error %v, want nil", tt.input, err)
				}
				return
			}
			if !errors.Is(err, tt.wantErr) {
				t.Fatalf("ValidateURL(%q) = error %v, want %v", tt.input, err, tt.wantErr)
			}
		})
	}
}

func TestValidateURL_NormalizesWhitespace(t *testing.T) {
	got, err := ValidateURL("  https://example.com/foo  ")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "https://example.com/foo" {
		t.Fatalf("got %q, want trimmed URL", got)
	}
}
