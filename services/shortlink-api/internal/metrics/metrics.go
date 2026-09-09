// Package metrics defines the Prometheus metrics exposed by shortlink-api
// and the middleware that records them.
package metrics

import (
	"net/http"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
)

var (
	// RequestsTotal counts requests by route, method and status class, the
	// basis for request rate and error rate panels.
	RequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "shortlink_api_http_requests_total",
			Help: "Total HTTP requests handled, by route, method and status.",
		},
		[]string{"route", "method", "status"},
	)

	// RequestDuration tracks request latency by route, the basis for
	// latency panels.
	RequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "shortlink_api_http_request_duration_seconds",
			Help:    "HTTP request latency in seconds, by route and method.",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"route", "method"},
	)

	// QueueDepth mirrors the length of the Redis click-events stream, as
	// observed from the producer side.
	QueueDepth = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "shortlink_api_click_queue_depth",
			Help: "Approximate number of entries in the click-events stream.",
		},
	)
)

func init() {
	prometheus.MustRegister(RequestsTotal, RequestDuration, QueueDepth)
}

// statusRecorder captures the status code written by the wrapped handler,
// since http.ResponseWriter doesn't expose it after the fact.
type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (r *statusRecorder) WriteHeader(status int) {
	r.status = status
	r.ResponseWriter.WriteHeader(status)
}

// Middleware records request count and latency for the given route label.
// The route label should be the route pattern (e.g. "/api/links"), not the
// raw path, to keep cardinality bounded.
func Middleware(route string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}

			next.ServeHTTP(rec, r)

			duration := time.Since(start).Seconds()
			RequestDuration.WithLabelValues(route, r.Method).Observe(duration)
			RequestsTotal.WithLabelValues(route, r.Method, strconv.Itoa(rec.status)).Inc()
		})
	}
}
