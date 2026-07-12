// Clean build artifacts. Adapted from the reference project's clean script
// with one deliberate difference: it must NEVER delete package-lock.json —
// npm is this repo's package manager and the lockfile is its source of
// truth (the reference is a yarn project, where nuking package-lock.json
// is intentional).
import { rimraf } from "rimraf";

const globs = [
  "node_modules",
  "dist",
  "storybook-static",
  ".vite",
  ".cache",
];

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function clean() {
  for (const path of globs) {
    let attempts = 3;
    while (attempts > 0) {
      try {
        await rimraf(path, { glob: true, maxRetries: 10 });
        console.log(`Deleted: ${path}`);
        break;
      } catch (err) {
        attempts--;
        if (attempts === 0) {
          console.error(`Failed to delete ${path}:`, err.message);
          break;
        }
        console.log(`Retrying ${path}... (${attempts} attempts left)`);
        await sleep(2000);
      }
    }
  }
}

process.on("unhandledRejection", (err) => {
  console.error("Unhandled promise rejection:", err);
  process.exit(1);
});

clean().catch((err) => {
  console.error("Clean script failed:", err);
  process.exit(1);
});
