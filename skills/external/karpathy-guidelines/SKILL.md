---
name: karpathy-guidelines
description: Behavioral guidelines to reduce common LLM coding mistakes based on Andrej Karpathy's observations
source: external
author: forrestchang
source-url: https://github.com/forrestchang/andrej-karpthy-skills
compatible-agents: [claude-code, opencode, codex, windsurf]
tags: [coding-guidelines, best-practices, behavioral, llm-pitfalls, simplicity, surgical-edits]
confidence: 0.5
derived-from: external-community
install-count: 0
---

# Karpathy Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Apply these principles to all coding tasks.

**Based on**: [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## The Four Principles

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

**Addresses**: Wrong assumptions, hidden confusion, missing tradeoffs

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

**Addresses**: Overcomplication, bloated abstractions

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

**Addresses**: Orthogonal edits, touching code you shouldn't

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

| Instead of... | Transform to... |
|--------------|-----------------|
| "Add validation" | "Write tests for invalid inputs, then make them pass" |
| "Fix the bug" | "Write a test that reproduces it, then make it pass" |
| "Refactor X" | "Ensure tests pass before and after" |

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

**Addresses**: Leverage through tests-first, verifiable success criteria

## Key Insight

From Andrej:

> "LLMs are exceptionally good at looping until they meet specific goals... Don't tell it what to do, give it success criteria and watch it go."

## When to Use

✅ **Use these guidelines when:**
- Working on non-trivial tasks
- Refactoring existing code
- Implementing new features
- Fixing complex bugs
- Making architectural decisions

⚠️ **Use judgment for:**
- Simple typo fixes
- Obvious one-liners
- Formatting changes
- Documentation updates

## How to Know It's Working

These guidelines are working if you see:

- **Fewer unnecessary changes in diffs** — Only requested changes appear
- **Fewer rewrites due to overcomplication** — Code is simple the first time
- **Clarifying questions come before implementation** — Not after mistakes
- **Clean, minimal PRs** — No drive-by refactoring or "improvements"

## Related Skills

- `tdd-workflow` - Complements Goal-Driven Execution
- `refactor-safe` - Complements Surgical Changes
- `code-review-checklist` - Validates adherence to these principles
