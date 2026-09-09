package store

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
)

// pgUniqueViolation is the Postgres error code for a unique constraint
// violation (23505), used to translate low-level driver errors into
// ErrCodeExists without leaking pgx types to callers.
const pgUniqueViolation = "23505"

// PostgresStore is a LinkStore backed by a Postgres connection pool.
type PostgresStore struct {
	pool *pgxpool.Pool
}

// NewPostgresStore connects to Postgres using dsn and verifies the
// connection before returning.
func NewPostgresStore(ctx context.Context, dsn string) (*PostgresStore, error) {
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		return nil, fmt.Errorf("create postgres pool: %w", err)
	}

	pingCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	if err := pool.Ping(pingCtx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("ping postgres: %w", err)
	}

	return &PostgresStore{pool: pool}, nil
}

func (s *PostgresStore) Create(ctx context.Context, code, longURL string) (Link, error) {
	const q = `
		INSERT INTO links (code, long_url)
		VALUES ($1, $2)
		RETURNING code, long_url, created_at`

	var link Link
	err := s.pool.QueryRow(ctx, q, code, longURL).Scan(&link.Code, &link.LongURL, &link.CreatedAt)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == pgUniqueViolation {
			return Link{}, ErrCodeExists
		}
		return Link{}, fmt.Errorf("insert link: %w", err)
	}
	return link, nil
}

func (s *PostgresStore) Get(ctx context.Context, code string) (Link, error) {
	const q = `SELECT code, long_url, created_at FROM links WHERE code = $1`

	var link Link
	err := s.pool.QueryRow(ctx, q, code).Scan(&link.Code, &link.LongURL, &link.CreatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return Link{}, ErrNotFound
		}
		return Link{}, fmt.Errorf("select link: %w", err)
	}
	return link, nil
}

func (s *PostgresStore) Ping(ctx context.Context) error {
	return s.pool.Ping(ctx)
}

func (s *PostgresStore) Close() {
	s.pool.Close()
}
