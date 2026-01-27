"""
Mental Model Analyzer - Integrates @mentalmodel/cli for codebase understanding.

Provides semantic layer for skill suggestions based on Mental model:
- Domains: Core entities (User, Order, Payment)
- Capabilities: Actions (Checkout, ProcessPayment)
- Aspects: Cross-cutting concerns (Auth, Validation)
- Decisions: Architecture decisions with rationale
"""

import json
import subprocess
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class MentalDomain:
    """A domain from Mental model (core entity)."""

    name: str
    description: str
    refs: list[str] = field(default_factory=list)  # Related domains


@dataclass
class MentalCapability:
    """A capability from Mental model (action/verb)."""

    name: str
    description: str
    operates_on: list[str] = field(default_factory=list)  # Domains it operates on


@dataclass
class MentalAspect:
    """A cross-cutting aspect from Mental model."""

    name: str
    description: str
    applies_to: list[str] = field(default_factory=list)  # Capabilities it applies to


@dataclass
class MentalDecision:
    """An architecture decision from Mental model."""

    id: str
    what: str
    why: str
    relates_to: list[str] = field(default_factory=list)  # Related domains/capabilities
    docs: list[str] = field(default_factory=list)  # Documentation links


@dataclass
class MentalModel:
    """Complete Mental model of the codebase."""

    domains: list[MentalDomain]
    capabilities: list[MentalCapability]
    aspects: list[MentalAspect]
    decisions: list[MentalDecision]


class MentalAnalyzer:
    """
    Analyzer that integrates Mental model data for context-aware skill suggestions.

    The Mental model provides semantic understanding of the codebase that goes beyond
    file structure and tool sequences. It captures:
    - What exists (domains)
    - What it does (capabilities)
    - How it's governed (aspects)
    - Why decisions were made (decisions)

    This context enhances skill suggestions by matching patterns to architectural intent.
    """

    def __init__(self, project_path: Optional[Path] = None):
        """
        Initialize Mental analyzer.

        Args:
            project_path: Path to project with Mental model (default: current directory)
        """
        self.project_path = project_path or Path.cwd()
        self._model: Optional[MentalModel] = None

    def is_mental_available(self) -> bool:
        """
        Check if mental CLI is installed and accessible.

        Returns:
            True if mental CLI is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["mental", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def load_model(self) -> Optional[MentalModel]:
        """
        Load Mental model from project using `mental show --json`.

        Returns:
            MentalModel if successful, None otherwise
        """
        if not self.is_mental_available():
            return None

        try:
            # Run: mental show --json
            result = subprocess.run(
                ["mental", "show", "--json"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)

            # Parse domains
            domains = [
                MentalDomain(
                    name=d["name"],
                    description=d.get("description", ""),
                    refs=d.get("refs", [])
                )
                for d in data.get("domains", [])
            ]

            # Parse capabilities
            capabilities = [
                MentalCapability(
                    name=c["name"],
                    description=c.get("description", ""),
                    operates_on=c.get("operatesOn", [])
                )
                for c in data.get("capabilities", [])
            ]

            # Parse aspects
            aspects = [
                MentalAspect(
                    name=a["name"],
                    description=a.get("description", ""),
                    applies_to=a.get("appliesTo", [])
                )
                for a in data.get("aspects", [])
            ]

            # Parse decisions
            decisions = [
                MentalDecision(
                    id=dec.get("id", ""),
                    what=dec.get("what", ""),
                    why=dec.get("why", ""),
                    relates_to=dec.get("relatesTo", []),
                    docs=dec.get("docs", [])
                )
                for dec in data.get("decisions", [])
            ]

            self._model = MentalModel(
                domains=domains,
                capabilities=capabilities,
                aspects=aspects,
                decisions=decisions
            )

            return self._model

        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as e:
            print(f"[Mental] Failed to load model: {e}")
            return None

    def get_relevant_domains(self, file_paths: list[str]) -> list[MentalDomain]:
        """
        Get domains relevant to given file paths.

        Uses simple heuristic: matches domain names in file paths.

        Args:
            file_paths: List of file paths from tool calls

        Returns:
            List of relevant MentalDomain objects
        """
        if not self._model:
            self.load_model()

        if not self._model:
            return []

        # Simple heuristic: match domain names in file paths
        relevant = []
        for domain in self._model.domains:
            domain_lower = domain.name.lower()
            for path in file_paths:
                if domain_lower in path.lower():
                    relevant.append(domain)
                    break

        return relevant

    def get_capabilities_for_domains(
        self,
        domains: list[MentalDomain]
    ) -> list[MentalCapability]:
        """
        Get capabilities that operate on given domains.

        Args:
            domains: List of domains to find capabilities for

        Returns:
            List of capabilities operating on these domains
        """
        if not self._model:
            return []

        domain_names = {d.name for d in domains}
        capabilities = []

        for capability in self._model.capabilities:
            # Check if any of the domains this capability operates on match
            if any(dom in domain_names for dom in capability.operates_on):
                capabilities.append(capability)

        return capabilities

    def suggest_skills_for_capability(
        self,
        capability: MentalCapability
    ) -> list[dict]:
        """
        Suggest potential skills for a capability.

        Uses keyword matching to suggest relevant skill patterns.
        This is a simple heuristic that can be enhanced with ML/NLP.

        Args:
            capability: Capability to suggest skills for

        Returns:
            List of skill suggestions with metadata
        """
        suggestions = []

        # Keyword-based skill hints
        cap_lower = capability.name.lower()

        skill_hints = {
            "checkout": ["payment-processing", "cart-management", "order-validation"],
            "payment": ["stripe-integration", "payment-retry", "refund-processing"],
            "auth": ["jwt-validation", "oauth-flow", "session-management"],
            "notification": ["email-sending", "push-notifications", "sms-gateway"],
            "search": ["elasticsearch-query", "full-text-search", "faceted-search"],
            "upload": ["file-upload", "image-processing", "s3-upload"],
            "export": ["csv-export", "pdf-generation", "report-builder"],
            "import": ["csv-import", "data-validation", "bulk-insert"],
            "sync": ["data-sync", "webhook-handler", "event-bus"],
        }

        for keyword, skills in skill_hints.items():
            if keyword in cap_lower:
                suggestions.extend([
                    {
                        "name": skill,
                        "source": "mental-hint",
                        "capability": capability.name,
                        "confidence": 0.6  # Medium confidence for hints
                    }
                    for skill in skills
                ])

        return suggestions

    def get_aspects_for_capability(
        self,
        capability: MentalCapability
    ) -> list[MentalAspect]:
        """
        Get aspects (cross-cutting concerns) that apply to a capability.

        Args:
            capability: Capability to find aspects for

        Returns:
            List of applicable aspects
        """
        if not self._model:
            return []

        aspects = []
        for aspect in self._model.aspects:
            # Check if this aspect applies to the capability
            if capability.name in aspect.applies_to:
                aspects.append(aspect)

        return aspects

    def get_decisions_for_domain(
        self,
        domain: MentalDomain
    ) -> list[MentalDecision]:
        """
        Get architecture decisions related to a domain.

        Args:
            domain: Domain to find decisions for

        Returns:
            List of related decisions
        """
        if not self._model:
            return []

        decisions = []
        domain_ref = f"domain:{domain.name}"

        for decision in self._model.decisions:
            if domain_ref in decision.relates_to:
                decisions.append(decision)

        return decisions

    def to_dict(self) -> dict:
        """
        Convert loaded Mental model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        if not self._model:
            return {}

        return {
            "domains": [
                {
                    "name": d.name,
                    "description": d.description,
                    "refs": d.refs
                }
                for d in self._model.domains
            ],
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description,
                    "operates_on": c.operates_on
                }
                for c in self._model.capabilities
            ],
            "aspects": [
                {
                    "name": a.name,
                    "description": a.description,
                    "applies_to": a.applies_to
                }
                for a in self._model.aspects
            ],
            "decisions": [
                {
                    "id": dec.id,
                    "what": dec.what,
                    "why": dec.why,
                    "relates_to": dec.relates_to,
                    "docs": dec.docs
                }
                for dec in self._model.decisions
            ]
        }
