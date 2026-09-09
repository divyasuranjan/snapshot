package handlers

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus/promhttp"

	appmetrics "github.com/divyasuranjan/snapshot/services/shortlink-api/internal/metrics"
)

// metricsHandler exposes metrics in the Prometheus exposition format.
func metricsHandler() http.Handler {
	return promhttp.Handler()
}

// withMetrics wraps h so requests to it are recorded under the given route
// label (the route pattern, not the raw path, to keep metric cardinality
// bounded).
func (s *Server) withMetrics(route string, h http.HandlerFunc) http.HandlerFunc {
	wrapped := appmetrics.Middleware(route)(h)
	return wrapped.ServeHTTP
}
