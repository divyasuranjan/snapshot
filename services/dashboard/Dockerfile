FROM node:26-alpine AS deps
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci

FROM node:26-alpine AS builder
WORKDIR /src
COPY --from=deps /src/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:26-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# apk upgrade: the base image tag's package index lags Alpine's security
# repo, so patches (e.g. openssl) are already published upstream even when
# the base image was built before they landed -- same fix as
# analytics-worker's Dockerfile.
#
# Removing npm/npx/corepack: the container only ever runs `node
# server.js`, npm is never invoked at runtime. But it still ships (every
# node:*-alpine image bundles it) along with ITS OWN vendored
# node_modules (tar, pacote, sigstore, minimatch...) -- unreachable code
# that was nonetheless showing up as real Trivy findings. Deleting it
# removes that whole vulnerability category instead of chasing each CVE.
RUN apk update && apk upgrade --no-cache && \
    rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder /src/public ./public
COPY --from=builder --chown=nextjs:nodejs /src/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /src/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
