package shortcode

import (
	"strings"
	"testing"
)

func TestGenerate_LengthAndAlphabet(t *testing.T) {
	for _, n := range []int{1, 7, 16} {
		code, err := Generate(n)
		if err != nil {
			t.Fatalf("Generate(%d) returned error: %v", n, err)
		}
		if len(code) != n {
			t.Fatalf("Generate(%d) = %q, want length %d", n, code, n)
		}
		for _, r := range code {
			if !strings.ContainsRune(alphabet, r) {
				t.Fatalf("Generate(%d) = %q contains char %q not in alphabet", n, code, r)
			}
		}
	}
}

func TestGenerate_RejectsNonPositiveLength(t *testing.T) {
	for _, n := range []int{0, -1} {
		if _, err := Generate(n); err == nil {
			t.Fatalf("Generate(%d) = nil error, want error", n)
		}
	}
}

func TestGenerate_ProducesDistinctCodes(t *testing.T) {
	seen := make(map[string]bool)
	for i := 0; i < 1000; i++ {
		code, err := Generate(7)
		if err != nil {
			t.Fatalf("Generate returned error: %v", err)
		}
		if seen[code] {
			t.Fatalf("Generate produced duplicate code %q within 1000 draws", code)
		}
		seen[code] = true
	}
}
