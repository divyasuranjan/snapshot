package handlers

import (
	"context"
	"net/http"
	"sync"
	"time"
)

// Healthz is a liveness probe: it reports the process is up and serving,
// with no dependency checks. Kubernetes uses this to decide whether to
// restart the container.
func (s *Server) Healthz(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

// readyTimeout bounds how long a readiness check waits on each dependency,
// so a hung dependency fails the probe instead of hanging it.
const readyTimeout = 3 * time.Second

// Readyz is a readiness probe: it also checks Postgres and Redis
// connectivity, since shortlink-api can't usefully serve traffic without
// them. Kubernetes uses this to decide whether to route traffic to the pod.
func (s *Server) Readyz(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), readyTimeout)
	defer cancel()

	var wg sync.WaitGroup
	var dbErr, redisErr error

	wg.Add(2)
	go func() {
		defer wg.Done()
		dbErr = s.Store.Ping(ctx)
	}()
	go func() {
		defer wg.Done()
		redisErr = s.Publisher.Ping(ctx)
	}()
	wg.Wait()

	if dbErr != nil || redisErr != nil {
		body := map[string]string{"status": "not ready"}
		if dbErr != nil {
			body["database"] = dbErr.Error()
		}
		if redisErr != nil {
			body["redis"] = redisErr.Error()
		}
		writeJSON(w, http.StatusServiceUnavailable, body)
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"status": "ready"})
}
