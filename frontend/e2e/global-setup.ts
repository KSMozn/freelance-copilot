import { execSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { ADMIN_EMAIL, ADMIN_PASSWORD } from "./helpers";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Idempotently create/reset the E2E admin account inside the running
 * backend container (app.scripts.create_admin upserts by email). Failing
 * here means the docker stack isn't up — surface a clear message instead
 * of letting every admin spec time out.
 */
export default function globalSetup(): void {
  const repoRoot = path.resolve(__dirname, "..", "..");
  try {
    execSync(
      `docker compose exec -T -e ADMIN_EMAIL=${ADMIN_EMAIL} -e ADMIN_PASSWORD=${ADMIN_PASSWORD} -e ADMIN_FULL_NAME="E2E Admin" backend python -m app.scripts.create_admin`,
      { cwd: repoRoot, stdio: "pipe", timeout: 60_000 },
    );
  } catch (err) {
    throw new Error(
      "Could not create the E2E admin via docker compose. Is the stack up? Run `make up` first.\n" +
        String(err),
    );
  }
}
