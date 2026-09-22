import { createApp } from "./app";
import { DemoProvider } from "./demo-provider";
import { seedDemo } from "./demo-seed";
import { token, atomic } from "./security";
import { join } from "node:path";
import { homedir } from "node:os";
import { mkdirSync, existsSync, readFileSync, unlinkSync } from "node:fs";
import { spawn } from "node:child_process";
process.umask(0o077);
const home =
    process.env.JEV_HOME ??
    join(
      homedir(),
      process.env.JEV_MODE === "demo"
        ? ".jev-workbench-demo"
        : ".jev-workbench",
    ),
  port = Number(
    process.env.JEV_PORT ?? (process.env.JEV_MODE === "demo" ? 17430 : 17420),
  ),
  instance = token(),
  controlToken = token();
if (!Number.isInteger(port) || port < 1024 || port > 65535)
  throw new Error("JEV_PORT must be 1024–65535");
mkdirSync(join(home, "runtime"), { recursive: true, mode: 0o700 });
const lock = join(home, "runtime/lock");
try {
  mkdirSync(lock, { mode: 0o700 });
} catch {
  console.error(
    "This data directory is already locked by a service. Run pnpm jev service status to check; after a crash, run pnpm jev service recover.",
  );
  process.exit(1);
}
let state: Awaited<ReturnType<typeof createApp>> | undefined;
let stopping = false;
async function shutdown() {
  if (stopping) return;
  stopping = true;
  const grace = setTimeout(() => state?.invoker.cancelAll(), 3000);
  grace.unref();
  await state?.app.close();
  clearTimeout(grace);
  const { rmSync } = await import("node:fs");
  rmSync(lock, { recursive: true, force: true });
  const path = join(home, "runtime/instance.json");
  if (
    existsSync(path) &&
    JSON.parse(readFileSync(path, "utf8")).instance === instance
  )
    unlinkSync(path);
  process.exit(0);
}
try {
  state = await createApp({
    home,
    port,
    instance,
    controlToken,
    shutdown,
    ...(process.env.JEV_MODE === "demo"
      ? { provider: new DemoProvider(), demoMode: true }
      : {}),
  });
  if (process.env.JEV_MODE === "demo") await seedDemo(state, home);
  await state.app.listen({ host: "127.0.0.1", port });
  atomic(
    join(home, "runtime/instance.json"),
    JSON.stringify({ instance, pid: process.pid, port, controlToken }),
  );
  console.log(
    `Jev Workbench: http://127.0.0.1:${port} · local control / cloud inference`,
  );
  if (!process.env.JEV_NO_OPEN) {
    const url = state.origin + "/#bootstrap=" + state.sessions.bootstrap();
    spawn(process.platform === "darwin" ? "open" : "xdg-open", [url], {
      stdio: "ignore",
    }).on("error", () =>
      console.error("Could not open a browser. Run pnpm jev service open."),
    );
  }
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
} catch (e: any) {
  state?.invoker.cancelAll();
  await state?.app.close();
  const { rmSync } = await import("node:fs");
  rmSync(lock, { recursive: true, force: true });
  console.error(
    e.code === "EADDRINUSE"
      ? `Port ${port} is already in use. Stop the other service or set JEV_PORT and restart, then update your client connections.`
      : "Startup failed: " + e.message,
  );
  process.exit(1);
}
