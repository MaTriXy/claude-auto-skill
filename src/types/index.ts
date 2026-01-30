/**
 * Auto-Skill type definitions.
 *
 * Consolidated TypeScript interfaces ported from Python dataclasses
 * across all core modules, plus new qmd-inspired types for the
 * content-addressable skill store.
 */

// ---------------------------------------------------------------------------
// event_store.py → ToolEvent
// ---------------------------------------------------------------------------

/** Represents a single tool invocation event. */
export interface ToolEvent {
  id: string;
  sessionId: string;
  projectPath: string;
  toolName: string;
  toolInput: Record<string, unknown>;
  toolResponse: string | null;
  success: boolean;
  timestamp: string; // ISO-8601
  agentId?: string;
}

// ---------------------------------------------------------------------------
// pattern_detector.py → DetectedPattern
// ---------------------------------------------------------------------------

/** A detected workflow pattern with v1 + v2 metadata. */
export interface DetectedPattern {
  id: string;
  toolSequence: string[];
  occurrenceCount: number;
  confidence: number;
  sessionIds: string[];
  firstSeen: string; // ISO-8601
  lastSeen: string; // ISO-8601
  successRate: number;
  suggestedName: string;
  suggestedDescription: string;

  // V2 enhancements
  sessionContext?: Record<string, unknown> | null;
  codeContext?: Record<string, unknown> | null;
  designPatterns?: Record<string, unknown>[];
  problemSolvingApproach?: Record<string, unknown> | null;

  // Hybrid Phase 3
  mentalContext?: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// sequence_matcher.py → SequenceMatch
// ---------------------------------------------------------------------------

/** A matched subsequence with occurrence information. */
export interface SequenceMatch {
  sequence: string[];
  occurrences: number;
  sessionIndices: number[];
}

// ---------------------------------------------------------------------------
// session_analyzer.py → ConversationTurn, SessionContext, ProblemSolvingPattern
// ---------------------------------------------------------------------------

/** A single turn in the conversation (user message + Claude response). */
export interface ConversationTurn {
  sessionId: string;
  timestamp: string; // ISO-8601
  userMessage: string | null;
  claudeResponse: string | null;
  toolsUsed: string[];
  intentCategory?: string | null;
  problemDomain?: string | null;
  outcome?: string | null;
}

/** Rich context for a complete session. */
export interface SessionContext {
  sessionId: string;
  startTime: string; // ISO-8601
  endTime: string; // ISO-8601
  projectPath: string;
  turns: ConversationTurn[];
  primaryIntent?: string | null;
  problemDomains: string[];
  workflowType?: string | null;
  successIndicators: Record<string, unknown>;
  keyDecisions: string[];
}

/** A detected problem-solving approach pattern. */
export interface ProblemSolvingPattern {
  patternId: string;
  patternType: string;
  description: string;
  workflowSteps: string[];
  successRate: number;
  occurrenceCount: number;
  exampleSessions: string[];
  contextualIndicators: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// lock_file.py → LockedSkill
// ---------------------------------------------------------------------------

/** A skill entry in the lock file. */
export interface LockedSkill {
  name: string;
  path: string;
  contentHash: string;
  source: string; // "auto" | "graduated" | "manual"
  lockedAt: string; // ISO-8601
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// config.py → DetectionConfig, AgentSettings, ProviderSettings, Config
// ---------------------------------------------------------------------------

/** Configuration for pattern detection. */
export interface DetectionConfig {
  minOccurrences: number;
  minSequenceLength: number;
  maxSequenceLength: number;
  lookbackDays: number;
  minConfidence: number;
  ignoredTools: string[];
}

/** Configuration for multi-agent support. */
export interface AgentSettings {
  autoDetect: boolean;
  targetAgents: string[];
  symlinkSkills: boolean;
}

/** Configuration for skill providers. */
export interface ProviderSettings {
  enabledProviders: string[];
  wellknownDomains: string[];
}

/** Full configuration for Auto-Skill. */
export interface Config {
  detection: DetectionConfig;
  agents: AgentSettings;
  providers: ProviderSettings;
  dbPath: string | null;
  skillsOutputDir: string | null;
  enabled: boolean;
}

// ---------------------------------------------------------------------------
// spec_validator.py → SpecViolation, SpecValidationResult
// ---------------------------------------------------------------------------

/** A single spec violation. */
export interface SpecViolation {
  field: string;
  message: string;
  severity: "error" | "warning";
}

/** Result of spec validation. */
export interface SpecValidationResult {
  violations: SpecViolation[];
  isValid: boolean;
  errors: SpecViolation[];
  warnings: SpecViolation[];
}

// ---------------------------------------------------------------------------
// skill_generator.py → SkillCandidate
// ---------------------------------------------------------------------------

/** A skill candidate ready for user review. */
export interface SkillCandidate {
  name: string;
  description: string;
  steps: string[];
  outputPath: string;
  yamlFrontmatter: Record<string, unknown>;
  useFork: boolean;
  agentType: string | null;
  allowedTools: string[];
  pattern: DetectedPattern;
  v2Content?: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// skill_tracker.py → SkillAdoption
// ---------------------------------------------------------------------------

/** Tracks adoption of a skill (external or local). */
export interface SkillAdoption {
  skillId: string;
  skillName: string;
  source: string; // "external" | "local" | "mental-hint"
  initialConfidence: number;
  currentConfidence: number;
  usageCount: number;
  successCount: number;
  failureCount: number;
  firstUsed: string; // ISO-8601
  lastUsed: string; // ISO-8601
  graduatedToLocal: boolean;
}

// ---------------------------------------------------------------------------
// graduation_manager.py → GraduationCandidate
// ---------------------------------------------------------------------------

/** Represents a skill eligible for graduation. */
export interface GraduationCandidate {
  skillName: string;
  currentConfidence: number;
  usageCount: number;
  successCount: number;
  successRate: number;
  firstUsed: string; // ISO-8601
  lastUsed: string; // ISO-8601
  source: string; // "external" | "mental-hint"
  metadata?: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// agent_registry.py → AgentConfig
// ---------------------------------------------------------------------------

/** Configuration for a known AI coding agent. */
export interface AgentConfig {
  id: string;
  name: string;
  skillDir: string;
  envVar?: string | null;
  configFile?: string | null;
  description: string;
}

// ---------------------------------------------------------------------------
// design_pattern_detector.py → DesignPattern, PatternContext
// ---------------------------------------------------------------------------

/** Represents a detected design pattern. */
export interface DesignPattern {
  patternId: string;
  patternType: string; // "architectural" | "coding" | "workflow"
  patternName: string;
  confidence: number;
  description: string;
  indicators: string[];
  affectedFiles?: string[];
  codeExamples?: string[];
  metadata?: Record<string, unknown>;
}

/** Context about when/why a pattern is appropriate. */
export interface PatternContext {
  patternName: string;
  whenToUse: string;
  benefits: string[];
  tradeOffs: string[];
  commonMistakes?: string[];
}

// ---------------------------------------------------------------------------
// providers/base.py → SkillSearchResult
// ---------------------------------------------------------------------------

/** A single skill result from a provider search. */
export interface SkillSearchResult {
  id: string;
  name: string;
  description: string;
  source: string; // provider id, e.g. "skillssh" | "local" | "wellknown"
  confidence: number;
  author: string;
  tags: string[];
  installCount: number;
  sourceUrl: string;
  compatibleAgents: string[];
  metadata?: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// unified_suggester.py → SkillSuggestion
// ---------------------------------------------------------------------------

/** A suggested skill with context and confidence. */
export interface SkillSuggestion {
  name: string;
  description: string;
  source: string; // "local" | "external" | "mental-hint"
  confidence: number;
  tags: string[];
  mentalContext?: Record<string, unknown> | null;
  patternMatch?: Record<string, unknown> | null;
  externalMetadata?: Record<string, unknown> | null;
  adoption?: SkillAdoption | null;
}

// ---------------------------------------------------------------------------
// skillssh_client.py → ExternalSkill
// ---------------------------------------------------------------------------

/** An external skill from skills.sh registry. */
export interface ExternalSkill {
  id: string;
  name: string;
  description: string;
  author: string;
  installCount: number;
  tags: string[];
  sourceUrl: string;
  compatibleAgents: string[];
  createdAt?: string | null;
  updatedAt?: string | null;
}

// ---------------------------------------------------------------------------
// skillssh_publisher.py → PublishStatus
// ---------------------------------------------------------------------------

/** Represents publishing status for a skill. */
export interface PublishStatus {
  skillName: string;
  published: boolean;
  skillId?: string | null;
  publishedAt?: string | null;
  lastSynced?: string | null;
  communityInstalls: number;
  communityRating?: number | null;
  externalUrl?: string | null;
}

// ---------------------------------------------------------------------------
// NEW: qmd-inspired content-addressable skill store types
// ---------------------------------------------------------------------------

/** Content-addressable skill content record. */
export interface SkillContent {
  hash: string; // SHA-256
  body: string;
  frontmatter: Record<string, unknown>;
  createdAt: string; // ISO-8601
}

/** Skill metadata record in the index database. */
export interface SkillRecord {
  id: string; // ULID
  name: string;
  collection: string;
  filepath: string;
  hash: string; // FK → SkillContent.hash
  description: string;
  tags: string[];
  confidence: number;
  agentType: string | null;
  active: boolean;
  sourceUrl: string;
  author: string;
  createdAt: string; // ISO-8601
  updatedAt: string; // ISO-8601
}

/** Information about a skill collection. */
export interface CollectionInfo {
  name: string;
  count: number;
  avgConfidence: number;
}

/** Options for searching the skill store. */
export interface SearchOptions {
  collection?: string;
  limit?: number;
  minScore?: number;
  activeOnly?: boolean;
}

/** A skill search result with relevance score. */
export interface SearchResult extends SkillRecord {
  score: number;
}

/** Interface for the content-addressable skill store. */
export interface SkillStore {
  insertContent(body: string, frontmatter: Record<string, unknown>): string; // returns hash
  getContent(hash: string): SkillContent | null;

  insertSkill(record: Omit<SkillRecord, "id" | "createdAt" | "updatedAt">): string; // returns id
  updateSkill(id: string, updates: Partial<SkillRecord>): void;
  deactivateSkill(id: string): void;

  getSkill(id: string): SkillRecord | null;
  getSkillByHash(hash: string): SkillRecord | null;
  listSkills(collection?: string, activeOnly?: boolean): SkillRecord[];
  searchSkills(query: string, options?: SearchOptions): SearchResult[];

  getCollectionStats(): CollectionInfo[];
  vacuumDatabase(): void;
  cleanupOrphanedContent(): number; // returns count removed
}

// ---------------------------------------------------------------------------
// event_store.py → EventStoreStats
// ---------------------------------------------------------------------------

/** Statistics from the event store. */
export interface EventStoreStats {
  totalEvents: number;
  uniqueSessions: number;
  uniqueProjects: number;
  topTools: Array<{ tool: string; count: number }>;
}

// ---------------------------------------------------------------------------
// skill_tracker.py → SkillTrackerStats
// ---------------------------------------------------------------------------

/** Statistics from the skill tracker. */
export interface SkillTrackerStats {
  total_skills: number;
  avg_confidence: number;
  graduated_count: number;
  total_usage: number;
  by_source: Record<string, number>;
}

// ---------------------------------------------------------------------------
// telemetry.py → TelemetryEvent, EffectivenessReport
// ---------------------------------------------------------------------------

/** A telemetry event for tracking auto-skill usage. */
export interface TelemetryEvent {
  eventType: string;
  timestamp: string;
  sessionId?: string;
  projectPath?: string;
  metadata?: Record<string, unknown>;
}

/** Report on skill effectiveness. */
export interface EffectivenessReport {
  skillName: string;
  usageCount: number;
  successRate: number;
  avgConfidence: number;
  trend: "improving" | "stable" | "declining";
  recommendations: string[];
}

/** Output format for CLI rendering. */
export type OutputFormat = "json" | "csv" | "md" | "cli";
