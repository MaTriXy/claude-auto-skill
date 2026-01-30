/**
 * Lightweight ULID generator.
 *
 * Produces 26-character, lexicographically sortable identifiers
 * using Crockford Base32 encoding:
 *   - 48 bits of millisecond timestamp (10 chars)
 *   - 80 bits of cryptographic randomness (16 chars)
 *
 * No external dependencies — uses node:crypto for randomness.
 */

import * as crypto from "node:crypto";

/** Crockford Base32 alphabet (excludes I, L, O, U). */
const ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";

const ENCODING_LEN = ENCODING.length; // 32
const TIME_LEN = 10;
const RANDOM_LEN = 16;

/**
 * Generate a ULID string.
 *
 * @returns A 26-character uppercase ULID.
 */
export function ulid(): string {
  const now = Date.now();
  return encodeTime(now) + encodeRandom();
}

/**
 * Encode a millisecond timestamp into 10 Crockford Base32 characters.
 *
 * The timestamp occupies the high 48 bits so that ULIDs sort
 * lexicographically by creation time.
 */
function encodeTime(ms: number): string {
  const chars: string[] = new Array(TIME_LEN);
  let t = ms;

  for (let i = TIME_LEN - 1; i >= 0; i--) {
    chars[i] = ENCODING[t % ENCODING_LEN];
    t = Math.floor(t / ENCODING_LEN);
  }

  return chars.join("");
}

/**
 * Encode 80 bits of cryptographic randomness into 16 Crockford Base32
 * characters.
 */
function encodeRandom(): string {
  const bytes = crypto.randomBytes(10); // 80 bits
  const chars: string[] = new Array(RANDOM_LEN);

  // Convert 10 bytes (80 bits) into 16 base-32 digits.
  // Each base-32 digit is 5 bits, so 80 bits = 16 digits.
  // We process pairs of 5-bit groups from the byte array.

  // Bit-pack the 10 bytes into a BigInt for easy slicing.
  let value = BigInt(0);
  for (let i = 0; i < bytes.length; i++) {
    value = (value << BigInt(8)) | BigInt(bytes[i]);
  }

  for (let i = RANDOM_LEN - 1; i >= 0; i--) {
    chars[i] = ENCODING[Number(value & BigInt(0x1f))];
    value >>= BigInt(5);
  }

  return chars.join("");
}
