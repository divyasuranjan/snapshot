#!/usr/bin/env bash
# Creates the snapshot-secrets Secret directly in the cluster -- never
# committed to git, never templated into a manifest. Run this once before
# the first Argo CD sync (or any time you need to rotate the password);
# Argo CD only manages the Deployments/ConfigMap/etc., not this Secret.
#
# Usage:
#   ./scripts/create-secrets.sh
#   POSTGRES_PASSWORD=mysecret ./scripts/create-secrets.sh   # pin instead of generate

set -euo pipefail

NAMESPACE="${NAMESPACE:-snapshot}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)}"
GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)}"

DATABASE_URL="postgres://snapshot:${POSTGRES_PASSWORD}@postgres:5432/snapshot?sslmode=disable"

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic snapshot-secrets \
  --namespace "$NAMESPACE" \
  --from-literal=postgres-password="$POSTGRES_PASSWORD" \
  --from-literal=shortlink-database-url="$DATABASE_URL" \
  --from-literal=analytics-database-url="$DATABASE_URL" \
  --from-literal=grafana-admin-password="$GRAFANA_ADMIN_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Grafana admin password: $GRAFANA_ADMIN_PASSWORD"

echo "Secret 'snapshot-secrets' applied in namespace '$NAMESPACE'."
