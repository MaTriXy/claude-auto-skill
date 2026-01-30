import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createLockFile } from "../src/core/lock-file";

describe("LockFile", () => {
  let tmpDir: string;
  let lockPath: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "lock-test-"));
    lockPath = path.join(tmpDir, "skills.lock.json");
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("creates new lock file", () => {
    const lock = createLockFile(lockPath);
    lock.addSkill("test", "/path/to/SKILL.md", "content here", "auto");
    lock.save();
    expect(fs.existsSync(lockPath)).toBe(true);
  });

  it("loads existing lock file", () => {
    const lock1 = createLockFile(lockPath);
    lock1.addSkill("test", "/path", "content", "auto");
    lock1.save();

    const lock2 = createLockFile(lockPath);
    lock2.load();
    expect(lock2.skillCount).toBe(1);
  });

  it("verifies integrity", () => {
    const lock = createLockFile(lockPath);
    lock.addSkill("test", "/path", "content", "auto");
    expect(lock.verifyIntegrity("test", "content")).toBe(true);
    expect(lock.verifyIntegrity("test", "tampered")).toBe(false);
  });

  it("removes skills", () => {
    const lock = createLockFile(lockPath);
    lock.addSkill("test", "/path", "content", "auto");
    expect(lock.removeSkill("test")).toBe(true);
    expect(lock.removeSkill("nonexistent")).toBe(false);
  });

  it("increments version on save", () => {
    const lock = createLockFile(lockPath);
    lock.save();
    lock.load();
    const v1 = lock.version;
    lock.save();
    lock.load();
    expect(lock.version).toBe(v1 + 1);
  });
});
