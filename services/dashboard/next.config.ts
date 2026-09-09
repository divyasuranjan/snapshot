import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a minimal, self-contained server build (only the deps each
  // page actually needs) so the Docker image doesn't ship the full
  // node_modules tree.
  output: "standalone",
};

export default nextConfig;
