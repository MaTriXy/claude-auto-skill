/**
 * FTS5 query sanitiser.
 *
 * SQLite FTS5 has a set of special characters and reserved words that
 * can cause query parse errors when passed verbatim. This module strips
 * or quotes them so user-supplied text can be safely used in MATCH
 * expressions.
 */

/**
 * Characters that have special meaning inside FTS5 MATCH expressions.
 *
 * - `*`  prefix/suffix wildcard
 * - `"`  phrase query delimiter
 * - `(`  / `)` grouping
 * - `+`  required term
 * - `-`  excluded term
 * - `^`  initial-token query
 * - `:`  column filter
 */
const FTS5_SPECIAL = /[*"()+\-^:{}[\]\\]/g;

/**
 * FTS5 reserved keywords that must be quoted when used as search terms.
 *
 * These are the column-filter / boolean operators recognised by FTS5.
 */
const FTS5_RESERVED = new Set([
  "AND",
  "OR",
  "NOT",
  "NEAR",
]);

/**
 * Sanitise a user-supplied string for safe use in an FTS5 MATCH clause.
 *
 * - Strips all FTS5 special characters.
 * - Quotes reserved words (AND, OR, NOT, NEAR) by wrapping in double quotes.
 * - Collapses multiple spaces into one and trims.
 *
 * @param query - Raw user input.
 * @returns A string safe to interpolate into `… MATCH ?`.
 */
export function sanitizeFTSQuery(query: string): string {
  // 1. Strip special characters
  let cleaned = query.replace(FTS5_SPECIAL, " ");

  // 2. Quote reserved words
  cleaned = cleaned
    .split(/\s+/)
    .filter((token) => token.length > 0)
    .map((token) =>
      FTS5_RESERVED.has(token.toUpperCase()) ? `"${token}"` : token,
    )
    .join(" ");

  return cleaned.trim();
}
