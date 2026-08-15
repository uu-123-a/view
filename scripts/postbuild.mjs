import { mkdir, copyFile, writeFile } from "node:fs/promises";

await mkdir("dist/server", { recursive: true });
await mkdir("dist/.openai", { recursive: true });
await copyFile(".openai/hosting.json", "dist/.openai/hosting.json");
await writeFile(
  "dist/server/index.js",
  `export default {
  async fetch(request, env) {
    if (env.ASSETS && typeof env.ASSETS.fetch === "function") {
      return env.ASSETS.fetch(request);
    }
    return new Response("MOSS site assets are unavailable.", { status: 503 });
  }
};
`,
  "utf8"
);
