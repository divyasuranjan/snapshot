# Deploying to your k3s cluster

Point `kubectl`/`KUBECONFIG` at your cluster before starting.

## 1. Install Argo CD (skip if already installed)

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
```

## 2. Create the app secrets (never committed to git)

```bash
./scripts/create-secrets.sh
```

Prints the generated Grafana admin password once -- save it now, it isn't stored anywhere else.

## 3. Point Argo CD at this repo

```bash
kubectl apply -f argocd/application.yaml
```

Argo CD takes it from here: syncs `manifests/overlays/production`, auto-heals drift, and re-syncs whenever CI bumps an image tag on `main`.

## 4. Watch it come up

```bash
kubectl get pods -n snapshot -w
```

Expect 7 pods: `postgres`, `redis`, `shortlink-api`, `analytics-worker`, `dashboard`, `prometheus`, `grafana`.

## 5. Access it

No Ingress is wired up yet (not built as of this pass) -- for now:

```bash
kubectl port-forward -n snapshot svc/dashboard 3000:3000    # http://localhost:3000
kubectl port-forward -n snapshot svc/grafana 3001:3000      # http://localhost:3001 (admin / the password from step 2)
kubectl port-forward -n snapshot svc/shortlink-api 8080:8080
```

`BASE_URL` in `manifests/base/config/configmap.yaml` is currently `http://localhost:8080` -- update it (and re-sync, or just let Argo CD pick up the git change) to your real domain/IP once you expose the service externally, so `short_url` values in the API response are correct for actual visitors.

## Verified so far

Deployed and checked directly (not just written): all 7 pods reach `Running`/`Ready` via their real health probes, Postgres migrations apply automatically on first boot, Prometheus shows both app targets `up`, Grafana auto-provisions the "Snapshot — Service Health" dashboard. Not yet exercised on a live cluster: Argo CD's own sync loop against the real GitHub repo (the Application manifest is correct against Argo CD's schema, but I validated the underlying manifests directly with `kubectl apply -k`, not through Argo CD itself) -- watch its first sync for anything unexpected.
