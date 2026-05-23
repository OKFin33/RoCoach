import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import net from "node:net";
import os from "node:os";
import path from "node:path";

export type BackendStatus =
  | {
      status: "running";
      baseUrl: string;
      managedByDesktop: boolean;
      message: string;
    }
  | {
      status: "starting";
      baseUrl: string;
      managedByDesktop: boolean;
      message: string;
    }
  | {
      status: "failed";
      baseUrl: string;
      managedByDesktop: boolean;
      message: string;
    };

export class BackendManager {
  private child: ChildProcessWithoutNullStreams | null = null;
  private startPromise: Promise<BackendStatus> | null = null;
  private readonly host = "127.0.0.1";
  private readonly port = 8000;
  private readonly repoRoot: string;
  private readonly appDataDir: string;
  private lastStatus: BackendStatus;

  constructor(repoRoot: string, appDataDir: string) {
    this.repoRoot = repoRoot;
    this.appDataDir = appDataDir;
    this.lastStatus = {
      status: "starting",
      baseUrl: this.baseUrl,
      managedByDesktop: false,
      message: "Backend not checked yet.",
    };
  }

  get baseUrl() {
    return `http://${this.host}:${this.port}`;
  }

  status(): BackendStatus {
    return this.lastStatus;
  }

  async ensureStarted(): Promise<BackendStatus> {
    if (this.startPromise) {
      return this.startPromise;
    }
    this.startPromise = this.ensureStartedOnce();
    try {
      return await this.startPromise;
    } finally {
      this.startPromise = null;
    }
  }

  private async ensureStartedOnce(): Promise<BackendStatus> {
    if (await isPortOpen(this.host, this.port)) {
      this.lastStatus = {
        status: "running",
        baseUrl: this.baseUrl,
        managedByDesktop: false,
        message: "Connected to existing local Product API.",
      };
      return this.lastStatus;
    }

    const python = this.resolvePython();
    this.child = spawn(
      python,
      ["-m", "uvicorn", "api.main:app", "--host", this.host, "--port", String(this.port)],
      {
        cwd: this.repoRoot,
        env: {
          ...process.env,
          PYTHONPATH: path.join(this.repoRoot, "src"),
          ROCO_MANAGED_PERSONA_SCOPE: process.env.ROCO_MANAGED_PERSONA_SCOPE ?? "internal_only_runtime",
          ROCO_DESKTOP_APP_DATA_DIR: process.env.ROCO_DESKTOP_APP_DATA_DIR ?? this.appDataDir,
        },
      },
    );

    this.child.stdout.on("data", (chunk) => {
      console.log(`[roco-backend] ${chunk.toString().trimEnd()}`);
    });
    this.child.stderr.on("data", (chunk) => {
      console.error(`[roco-backend] ${chunk.toString().trimEnd()}`);
    });
    this.child.once("exit", (code) => {
      if (code !== 0 && this.lastStatus.status !== "running") {
        this.lastStatus = {
          status: "failed",
          baseUrl: this.baseUrl,
          managedByDesktop: true,
          message: `Backend exited before ready. code=${String(code)}`,
        };
      }
      this.child = null;
    });

    this.lastStatus = {
      status: "starting",
      baseUrl: this.baseUrl,
      managedByDesktop: true,
      message: "Starting local Product API.",
    };

    const ready = await waitForPort(this.host, this.port, 15_000);
    this.lastStatus = ready
      ? {
          status: "running",
          baseUrl: this.baseUrl,
          managedByDesktop: true,
          message: "Local Product API started by RoCoach.",
        }
      : {
          status: "failed",
          baseUrl: this.baseUrl,
          managedByDesktop: true,
          message: "Timed out while waiting for local Product API. Check Python dependencies.",
        };
    return this.lastStatus;
  }

  stop(): void {
    if (!this.child) {
      return;
    }
    if (os.platform() === "win32") {
      spawn("taskkill", ["/pid", String(this.child.pid), "/f", "/t"]);
    } else {
      this.child.kill("SIGTERM");
    }
    this.child = null;
  }

  private resolvePython(): string {
    const envPython = process.env.ROCO_DESKTOP_PYTHON?.trim();
    if (envPython) {
      return envPython;
    }
    return os.platform() === "win32"
      ? path.join(this.repoRoot, ".venv", "Scripts", "python.exe")
      : path.join(this.repoRoot, ".venv", "bin", "python");
  }
}

function isPortOpen(host: string, port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host, port });
    socket.setTimeout(600);
    socket.once("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.once("timeout", () => {
      socket.destroy();
      resolve(false);
    });
    socket.once("error", () => resolve(false));
  });
}

async function waitForPort(host: string, port: number, timeoutMs: number): Promise<boolean> {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (await isPortOpen(host, port)) {
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  return false;
}
