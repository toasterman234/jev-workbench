import { join } from "node:path";
import { homedir } from "node:os";
import {
  existsSync,
  readFileSync,
  mkdirSync,
  openSync,
  statSync,
  renameSync,
  rmSync,
} from "node:fs";
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
const home = process.env.JEV_HOME ?? join(homedir(), ".jev-workbench"),
  file = join(home, "runtime/instance.json");
async function current() {
  if (!existsSync(file)) return undefined;
  const i = JSON.parse(readFileSync(file, "utf8"));
  try {
    const r = await fetch(`http://127.0.0.1:${i.port}/internal/instance`, {
      headers: { Authorization: "Bearer " + i.controlToken },
      signal: AbortSignal.timeout(1200),
    });
    const b = await r.json();
    if (b.instance === i.instance && b.pid === i.pid) return i;
  } catch {}
  return undefined;
}
const action =
  process.argv[2] === "service" ? process.argv[3] : process.argv[2];
async function open(i: any) {
  const r = await fetch(`http://127.0.0.1:${i.port}/internal/open`, {
    method: "POST",
    headers: { Authorization: "Bearer " + i.controlToken },
  });
  const b = await r.json();
  if (!r.ok) throw new Error("Could not create a bootstrap page");
  spawn(process.platform === "darwin" ? "open" : "xdg-open", [b.url], {
    stdio: "ignore",
  }).on("error", () => console.error("Could not start a browser"));
}
try {
  if (action === "start") {
    if (await current()) {
      console.log("Jev Workbench is already running");
      process.exit(0);
    }
    mkdirSync(join(home, "logs"), { recursive: true, mode: 0o700 });
    const log = join(home, "logs/server.log");
    if (existsSync(log) && statSync(log).size > 2 * 1024 * 1024)
      renameSync(log, log + ".1");
    const fd = openSync(log, "a", 0o600),
      child = spawn(
        process.execPath,
        [join(process.cwd(), "dist/server/main.js")],
        {
          cwd: process.cwd(),
          env: { ...process.env, JEV_NO_OPEN: "1" },
          detached: true,
          stdio: ["ignore", fd, fd],
        },
      );
    child.unref();
    let i;
    for (let n = 0; n < 30; n++) {
      await delay(150);
      i = await current();
      if (i) break;
    }
    if (!i) throw new Error("Background start failed; see " + log);
    console.log(`Started http://127.0.0.1:${i.port}`);
    if (!process.env.JEV_NO_OPEN) await open(i);
  } else if (action === "status") {
    const i = await current();
    console.log(
      i
        ? `Running · PID ${i.pid} · http://127.0.0.1:${i.port}`
        : "Not running, or the instance could not be verified",
    );
  } else if (action === "open") {
    const i = await current();
    if (!i)
      throw new Error(
        "The background service is not running. Run pnpm jev service start first.",
      );
    await open(i);
    console.log("Opened the admin page");
  } else if (action === "stop") {
    const i = await current();
    if (!i)
      throw new Error("No verifiable instance; no signal was sent to any PID");
    await fetch(`http://127.0.0.1:${i.port}/internal/stop`, {
      method: "POST",
      headers: { Authorization: "Bearer " + i.controlToken },
    });
    for (let n = 0; n < 30; n++) {
      await delay(100);
      if (!(await current())) break;
    }
    if (await current())
      throw new Error("The service has not stopped. Check its status.");
    console.log("Background service stopped");
  } else if (action === "recover") {
    if (await current())
      throw new Error(
        "The service is still running; the lock cannot be cleared",
      );
    if (existsSync(file)) {
      const i = JSON.parse(readFileSync(file, "utf8"));
      try {
        process.kill(i.pid, 0);
        throw new Error(
          "The recorded PID still exists. Check the process yourself before recovering.",
        );
      } catch (e: any) {
        if (e.code !== "ESRCH") throw e;
      }
    } else
      throw new Error(
        "No instance file, so the lock holder is unknown. Check the startup log and the process list.",
      );
    rmSync(join(home, "runtime/lock"), { recursive: true, force: true });
    rmSync(file, { force: true });
    console.log(
      "Cleared the crashed instance lock. The next start will mark leftover calls interrupted.",
    );
  } else console.log("pnpm jev service start | status | open | stop | recover");
} catch (e: any) {
  console.error(e.message);
  process.exitCode = 1;
}
