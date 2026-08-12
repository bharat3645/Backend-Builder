import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Separate from vite.config.ts so the app build config stays untouched by
// test-only concerns. Picked up automatically by the `vitest` CLI.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    // `threads` (the default) crashes with "Worker exited unexpectedly" in
    // some sandboxed/Windows shells; `forks` is slightly slower but reliable
    // everywhere, including plain CI runners.
    pool: 'forks',
  },
});
