/**
 * Mental Model Analyzer - Integrates @mentalmodel/cli for codebase understanding.
 *
 * Provides semantic layer for skill suggestions based on Mental model:
 * - Domains: Core entities (User, Order, Payment)
 * - Capabilities: Actions (Checkout, ProcessPayment)
 * - Aspects: Cross-cutting concerns (Auth, Validation)
 * - Decisions: Architecture decisions with rationale
 *
 * Ported from Python core/mental_analyzer.py.
 */

import { execSync } from "node:child_process";

// ---------------------------------------------------------------------------
// Mental model types
// ---------------------------------------------------------------------------

/** A domain from Mental model (core entity). */
export interface MentalDomain {
  name: string;
  description: string;
  refs: string[];
}

/** A capability from Mental model (action/verb). */
export interface MentalCapability {
  name: string;
  description: string;
  operatesOn: string[];
}

/** A cross-cutting aspect from Mental model. */
export interface MentalAspect {
  name: string;
  description: string;
  appliesTo: string[];
}

/** An architecture decision from Mental model. */
export interface MentalDecision {
  id: string;
  what: string;
  why: string;
  relatesTo: string[];
  docs: string[];
}

/** Complete Mental model of the codebase. */
export interface MentalModel {
  domains: MentalDomain[];
  capabilities: MentalCapability[];
  aspects: MentalAspect[];
  decisions: MentalDecision[];
}

/** A skill suggestion hint derived from a capability. */
export interface SkillHint {
  name: string;
  source: string;
  capability: string;
  confidence: number;
}

// ---------------------------------------------------------------------------
// Keyword-based skill hints map
// ---------------------------------------------------------------------------

const SKILL_HINTS: Record<string, string[]> = {
  checkout: ["payment-processing", "cart-management", "order-validation"],
  payment: ["stripe-integration", "payment-retry", "refund-processing"],
  auth: ["jwt-validation", "oauth-flow", "session-management"],
  notification: [
    "email-sending",
    "push-notifications",
    "sms-gateway",
  ],
  search: [
    "elasticsearch-query",
    "full-text-search",
    "faceted-search",
  ],
  upload: ["file-upload", "image-processing", "s3-upload"],
  export: ["csv-export", "pdf-generation", "report-builder"],
  import: ["csv-import", "data-validation", "bulk-insert"],
  sync: ["data-sync", "webhook-handler", "event-bus"],
};

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/**
 * Create a Mental model analyzer.
 *
 * The Mental model provides semantic understanding of the codebase that goes
 * beyond file structure and tool sequences. It captures what exists (domains),
 * what it does (capabilities), how it is governed (aspects), and why decisions
 * were made (decisions).
 *
 * @param projectPath - Path to project with Mental model (defaults to cwd).
 * @returns Analyzer object exposing Mental model queries.
 */
export function createMentalAnalyzer(projectPath?: string): {
  /**
   * Check if the mental CLI is installed and accessible.
   */
  isMentalAvailable(): boolean;

  /**
   * Load Mental model from project using `mental show --json`.
   *
   * @returns MentalModel if successful, null otherwise.
   */
  loadModel(): MentalModel | null;

  /**
   * Get domains relevant to given file paths.
   *
   * Uses a simple heuristic: matches domain names in file paths
   * (case-insensitive).
   *
   * @param filePaths - List of file paths from tool calls.
   * @returns List of relevant MentalDomain objects.
   */
  getRelevantDomains(filePaths: string[]): MentalDomain[];

  /**
   * Get capabilities that operate on given domains.
   *
   * @param domains - Domains to find capabilities for.
   * @returns Capabilities operating on these domains.
   */
  getCapabilitiesForDomains(domains: MentalDomain[]): MentalCapability[];

  /**
   * Suggest potential skills for a capability using keyword matching.
   *
   * @param capability - Capability to suggest skills for.
   * @returns List of skill hints with metadata.
   */
  suggestSkillsForCapability(capability: MentalCapability): SkillHint[];

  /**
   * Get aspects (cross-cutting concerns) that apply to a capability.
   *
   * @param capability - Capability to find aspects for.
   * @returns Applicable aspects.
   */
  getAspectsForCapability(capability: MentalCapability): MentalAspect[];

  /**
   * Get architecture decisions related to a domain.
   *
   * @param domain - Domain to find decisions for.
   * @returns Related decisions.
   */
  getDecisionsForDomain(domain: MentalDomain): MentalDecision[];

  /**
   * Convert loaded Mental model to a plain dictionary.
   */
  toDict(): Record<string, unknown>;
} {
  const cwd = projectPath ?? process.cwd();
  let model: MentalModel | null = null;

  function ensureModel(): void {
    if (model === null) {
      // Attempt to load if not yet loaded
      loadModel();
    }
  }

  function isMentalAvailable(): boolean {
    try {
      execSync("mental --version", {
        timeout: 5000,
        stdio: "pipe",
      });
      return true;
    } catch {
      return false;
    }
  }

  function loadModel(): MentalModel | null {
    if (!isMentalAvailable()) {
      return null;
    }

    try {
      const output = execSync("mental show --json", {
        cwd,
        timeout: 10_000,
        encoding: "utf-8",
        stdio: ["pipe", "pipe", "pipe"],
      });

      const data = JSON.parse(output) as Record<string, unknown>;

      const rawDomains = Array.isArray(data.domains)
        ? (data.domains as Record<string, unknown>[])
        : [];
      const rawCapabilities = Array.isArray(data.capabilities)
        ? (data.capabilities as Record<string, unknown>[])
        : [];
      const rawAspects = Array.isArray(data.aspects)
        ? (data.aspects as Record<string, unknown>[])
        : [];
      const rawDecisions = Array.isArray(data.decisions)
        ? (data.decisions as Record<string, unknown>[])
        : [];

      model = {
        domains: rawDomains.map((d) => ({
          name: String(d.name ?? ""),
          description: String(d.description ?? ""),
          refs: Array.isArray(d.refs) ? (d.refs as string[]) : [],
        })),
        capabilities: rawCapabilities.map((c) => ({
          name: String(c.name ?? ""),
          description: String(c.description ?? ""),
          operatesOn: Array.isArray(c.operatesOn)
            ? (c.operatesOn as string[])
            : [],
        })),
        aspects: rawAspects.map((a) => ({
          name: String(a.name ?? ""),
          description: String(a.description ?? ""),
          appliesTo: Array.isArray(a.appliesTo)
            ? (a.appliesTo as string[])
            : [],
        })),
        decisions: rawDecisions.map((dec) => ({
          id: String(dec.id ?? ""),
          what: String(dec.what ?? ""),
          why: String(dec.why ?? ""),
          relatesTo: Array.isArray(dec.relatesTo)
            ? (dec.relatesTo as string[])
            : [],
          docs: Array.isArray(dec.docs) ? (dec.docs as string[]) : [],
        })),
      };

      return model;
    } catch (err) {
      console.warn(`[Mental] Failed to load model: ${err}`);
      return null;
    }
  }

  function getRelevantDomains(filePaths: string[]): MentalDomain[] {
    ensureModel();
    if (!model) {
      return [];
    }

    const relevant: MentalDomain[] = [];
    for (const domain of model.domains) {
      const domainLower = domain.name.toLowerCase();
      for (const fp of filePaths) {
        if (fp.toLowerCase().includes(domainLower)) {
          relevant.push(domain);
          break;
        }
      }
    }
    return relevant;
  }

  function getCapabilitiesForDomains(
    domains: MentalDomain[],
  ): MentalCapability[] {
    if (!model) {
      return [];
    }

    const domainNames = new Set(domains.map((d) => d.name));
    return model.capabilities.filter((cap) =>
      cap.operatesOn.some((dom) => domainNames.has(dom)),
    );
  }

  function suggestSkillsForCapability(
    capability: MentalCapability,
  ): SkillHint[] {
    const suggestions: SkillHint[] = [];
    const capLower = capability.name.toLowerCase();

    for (const [keyword, skills] of Object.entries(SKILL_HINTS)) {
      if (capLower.includes(keyword)) {
        for (const skill of skills) {
          suggestions.push({
            name: skill,
            source: "mental-hint",
            capability: capability.name,
            confidence: 0.6,
          });
        }
      }
    }

    return suggestions;
  }

  function getAspectsForCapability(
    capability: MentalCapability,
  ): MentalAspect[] {
    if (!model) {
      return [];
    }

    return model.aspects.filter((aspect) =>
      aspect.appliesTo.includes(capability.name),
    );
  }

  function getDecisionsForDomain(domain: MentalDomain): MentalDecision[] {
    if (!model) {
      return [];
    }

    const domainRef = `domain:${domain.name}`;
    return model.decisions.filter((dec) =>
      dec.relatesTo.includes(domainRef),
    );
  }

  function toDict(): Record<string, unknown> {
    if (!model) {
      return {};
    }

    return {
      domains: model.domains.map((d) => ({
        name: d.name,
        description: d.description,
        refs: d.refs,
      })),
      capabilities: model.capabilities.map((c) => ({
        name: c.name,
        description: c.description,
        operatesOn: c.operatesOn,
      })),
      aspects: model.aspects.map((a) => ({
        name: a.name,
        description: a.description,
        appliesTo: a.appliesTo,
      })),
      decisions: model.decisions.map((dec) => ({
        id: dec.id,
        what: dec.what,
        why: dec.why,
        relatesTo: dec.relatesTo,
        docs: dec.docs,
      })),
    };
  }

  return {
    isMentalAvailable,
    loadModel,
    getRelevantDomains,
    getCapabilitiesForDomains,
    suggestSkillsForCapability,
    getAspectsForCapability,
    getDecisionsForDomain,
    toDict,
  };
}
