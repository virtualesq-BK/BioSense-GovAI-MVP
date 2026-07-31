import type { NextConfig } from 'next';

// Next.js loads env from the app directory by default.
// In this monorepo, `.env` lives at the repo root, so we load it here.
import fs from 'node:fs';
import path from 'node:path';

function loadRootEnv() {
  const rootEnvPath = path.join(__dirname, '..', '..', '.env');
  if (!fs.existsSync(rootEnvPath)) return;
  const raw = fs.readFileSync(rootEnvPath, 'utf8');
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const idx = trimmed.indexOf('=');
    if (idx <= 0) continue;
    const key = trimmed.slice(0, idx).trim();
    const value = trimmed.slice(idx + 1).trim();
    if (!process.env[key]) process.env[key] = value;
  }
}

loadRootEnv();

const apiUrl = process.env.API_URL ?? 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  output: 'standalone',
  transpilePackages: [],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/:path*`
      }
    ];
  }
};

export default nextConfig;
