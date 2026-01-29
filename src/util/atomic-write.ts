/**
 * Atomic file write utility.
 *
 * Writes to a temporary file in the same directory, fsyncs the file
 * descriptor, then renames (atomic on POSIX). Retries transient
 * permission / busy errors with exponential backoff.
 */

import * as fs from "node:fs";
import * as path from "node:path";
import * as crypto from "node:crypto";

/** Errors that are worth retrying (transient OS-level issues). */
const RETRIABLE_CODES = new Set(["EBUSY", "ETXTBSY", "EPERM", "EACCES"]);

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 100;

/**
 * Write `content` to `filePath` atomically.
 *
 * 1. Write to a temp file (same directory, PID+timestamp suffix).
 * 2. fsync the file descriptor.
 * 3. Rename temp → target (atomic on POSIX).
 * 4. Retry on transient errors with exponential backoff.
 */
export function writeFileAtomic(filePath: string, content: string): void {
  const dir = path.dirname(filePath);
  const suffix = `.${process.pid}-${Date.now()}-${crypto.randomBytes(4).toString("hex")}.tmp`;
  const tmpPath = path.join(dir, path.basename(filePath) + suffix);

  // Ensure parent directory exists
  fs.mkdirSync(dir, { recursive: true });

  let lastError: unknown;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      // Open, write, fsync, close
      const fd = fs.openSync(tmpPath, "w");
      try {
        fs.writeFileSync(fd, content, "utf-8");
        fs.fsyncSync(fd);
      } finally {
        fs.closeSync(fd);
      }

      // Atomic rename
      fs.renameSync(tmpPath, filePath);
      return;
    } catch (err: unknown) {
      lastError = err;

      // Clean up temp file on failure (best-effort)
      try {
        fs.unlinkSync(tmpPath);
      } catch {
        // ignore cleanup errors
      }

      const code = (err as NodeJS.ErrnoException).code;
      if (code && RETRIABLE_CODES.has(code) && attempt < MAX_RETRIES) {
        // Exponential backoff: 100ms, 200ms, 400ms
        const delay = BASE_DELAY_MS * Math.pow(2, attempt);
        sleepSync(delay);
        continue;
      }

      // Non-retriable or exhausted retries
      break;
    }
  }

  throw lastError;
}

/**
 * Alias for writeFileAtomic, for convenience.
 */
export const atomicWrite = writeFileAtomic;

/** Synchronous sleep using Atomics (does not spin the CPU). */
function sleepSync(ms: number): void {
  const buf = new SharedArrayBuffer(4);
  const view = new Int32Array(buf);
  Atomics.wait(view, 0, 0, ms);
}
