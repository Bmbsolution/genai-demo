import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./", import.meta.url)) },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    include: ["__tests__/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary"],
      // The modules added/changed this session — AC-2 targets these.
      include: [
        "lib/format-date.ts",
        "hooks/use-notifications.ts",
        "components/notification-bell.tsx",
        "app/notifications/page.tsx",
      ],
    },
  },
});
