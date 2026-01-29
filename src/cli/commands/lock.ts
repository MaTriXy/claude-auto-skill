/**
 * Lock Command - Manage the skill lock file for integrity verification.
 *
 * Supports status, list, and verify actions to inspect and validate
 * locked skill hashes.
 */
import { createLockFile } from "../../core/lock-file";

/** Options for the lock command. */
export interface LockOptions {
  json?: boolean;
}

/**
 * Manage the skill lock file.
 * @param action - "status" (default), "list", or "verify".
 * @param opts - Command options.
 */
export async function lockCommand(
  action: string,
  opts: LockOptions,
): Promise<void> {
  const lock = createLockFile();
  lock.load();

  if (action === "verify") {
    const results = lock.verifyAll();
    if (opts.json) {
      const passed = Object.values(results).filter(Boolean).length;
      console.log(
        JSON.stringify(
          {
            total: Object.keys(results).length,
            passed,
            failed: Object.keys(results).length - passed,
            results: Object.fromEntries(
              Object.entries(results).map(([k, v]) => [
                k,
                v ? "pass" : "fail",
              ]),
            ),
          },
          null,
          2,
        ),
      );
    } else {
      console.log("\nIntegrity Verification\n");
      for (const [name, ok] of Object.entries(results)) {
        console.log(`  ${ok ? "PASS" : "FAIL"} ${name}`);
      }
    }
  } else if (action === "list") {
    const skills = lock.listSkills();
    if (opts.json) {
      console.log(JSON.stringify({ count: skills.length, skills }, null, 2));
    } else {
      console.log(`\nLocked Skills (${skills.length})\n`);
      for (const s of skills) {
        console.log(`  ${s.name}`);
        console.log(
          `     Source: ${s.source} | Hash: ${s.contentHash.slice(0, 16)}...`,
        );
        console.log(`     Locked: ${s.lockedAt}\n`);
      }
    }
  } else {
    // status (default)
    if (opts.json) {
      console.log(
        JSON.stringify(
          {
            version: lock.version,
            skillCount: lock.skillCount,
            path: lock.filePath,
          },
          null,
          2,
        ),
      );
    } else {
      console.log("\nLock File Status\n");
      console.log(`  Path: ${lock.filePath}`);
      console.log(`  Version: ${lock.version}`);
      console.log(`  Skills: ${lock.skillCount}\n`);
    }
  }
}
