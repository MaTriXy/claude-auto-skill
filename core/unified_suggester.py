"""
Unified Skill Suggester - Combines Mental, Skills.sh, and local patterns.

This is the main discovery layer that integrates:
1. Mental Model - Codebase semantic understanding
2. Skills.sh - External community skills
3. Auto-Skill V2 - Local pattern detection

Provides ranked skill suggestions with confidence scores and context.
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from .mental_analyzer import MentalAnalyzer, MentalModel, MentalCapability
from .skillssh_client import SkillsShClient, ExternalSkill
from .skill_tracker import SkillTracker, SkillAdoption


@dataclass
class SkillSuggestion:
    """
    A suggested skill with context and confidence.
    
    Combines information from multiple sources to provide a complete
    picture of why a skill is being suggested and how reliable it is.
    """

    name: str
    description: str
    source: str  # "local", "external", "mental-hint"
    confidence: float
    tags: list[str] = field(default_factory=list)

    # Context information
    mental_context: Optional[dict] = None  # From Mental model
    pattern_match: Optional[dict] = None  # From pattern detector
    external_metadata: Optional[dict] = None  # From skills.sh

    # Usage statistics (if adopted)
    adoption: Optional[SkillAdoption] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "confidence": self.confidence,
            "tags": self.tags
        }

        if self.mental_context:
            result["mental_context"] = self.mental_context
        if self.pattern_match:
            result["pattern_match"] = self.pattern_match
        if self.external_metadata:
            result["external_metadata"] = self.external_metadata
        if self.adoption:
            result["adoption"] = self.adoption.to_dict()

        return result


class UnifiedSuggester:
    """
    Unified skill suggester combining all discovery sources.
    
    This is the main entry point for skill discovery. It:
    1. Queries Mental model for codebase context
    2. Searches Skills.sh for external skills
    3. Incorporates local pattern detection results
    4. Ranks and deduplicates suggestions
    5. Tracks adoption and confidence evolution
    """

    def __init__(
        self,
        project_path: Optional[Path] = None,
        enable_mental: bool = True,
        enable_external: bool = True
    ):
        """
        Initialize unified suggester.

        Args:
            project_path: Path to project (default: current directory)
            enable_mental: Enable Mental model integration
            enable_external: Enable Skills.sh integration
        """
        self.project_path = project_path or Path.cwd()

        # Initialize analyzers
        self.mental = MentalAnalyzer(project_path) if enable_mental else None
        self.skillssh = SkillsShClient() if enable_external else None
        self.tracker = SkillTracker()

        # Cache for Mental model (loaded once)
        self._mental_model: Optional[MentalModel] = None

    def suggest_for_context(
        self,
        detected_patterns: list = None,
        session_context: Optional[dict] = None,
        file_paths: list[str] = None
    ) -> list[SkillSuggestion]:
        """
        Suggest skills based on current context.

        Combines suggestions from:
        - Local patterns (highest confidence)
        - Mental model hints (medium confidence)
        - External skills (variable confidence based on adoption)

        Args:
            detected_patterns: List of DetectedPattern objects from pattern detector
            session_context: Session context from session analyzer
            file_paths: List of file paths being worked on

        Returns:
            List of SkillSuggestion objects, sorted by confidence
        """
        suggestions = []

        # 1. Local patterns (highest confidence)
        if detected_patterns:
            local_suggestions = self._suggest_from_local(detected_patterns)
            suggestions.extend(local_suggestions)

        # 2. Mental-based suggestions
        if self.mental and (file_paths or session_context):
            mental_suggestions = self._suggest_from_mental(
                file_paths or [],
                session_context
            )
            suggestions.extend(mental_suggestions)

        # 3. External skills (with adoption tracking)
        if self.skillssh and session_context:
            external_suggestions = self._suggest_from_external(session_context)
            suggestions.extend(external_suggestions)

        # Deduplicate and sort by confidence
        unique_suggestions = self._deduplicate(suggestions)
        unique_suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return unique_suggestions

    def suggest_for_files(
        self,
        file_paths: list[str],
        limit: int = 10
    ) -> list[SkillSuggestion]:
        """
        Suggest skills based on file paths.

        Uses Mental model to understand what domains/capabilities are involved
        and suggests relevant skills.

        Args:
            file_paths: List of file paths
            limit: Maximum number of suggestions

        Returns:
            List of SkillSuggestion objects
        """
        if not self.mental:
            return []

        suggestions = self._suggest_from_mental(file_paths, None)
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return suggestions[:limit]

    def suggest_for_domain(
        self,
        domain_name: str,
        limit: int = 10
    ) -> list[SkillSuggestion]:
        """
        Suggest skills for a specific Mental domain.

        Args:
            domain_name: Name of domain (e.g., "Payment", "User")
            limit: Maximum number of suggestions

        Returns:
            List of SkillSuggestion objects
        """
        if not self.mental:
            return []

        # Load Mental model
        mental_model = self._get_mental_model()
        if not mental_model:
            return []

        # Find domain
        domain = next(
            (d for d in mental_model.domains if d.name.lower() == domain_name.lower()),
            None
        )
        if not domain:
            return []

        # Get capabilities for this domain
        capabilities = self.mental.get_capabilities_for_domains([domain])

        # Generate suggestions
        suggestions = []
        for capability in capabilities:
            skill_hints = self.mental.suggest_skills_for_capability(capability)
            for hint in skill_hints:
                suggestions.append(SkillSuggestion(
                    name=hint["name"],
                    description=f"Skill for {capability.name}: {capability.description}",
                    source="mental-hint",
                    confidence=hint.get("confidence", 0.6),
                    mental_context={
                        "domain": domain.name,
                        "capability": capability.name
                    }
                ))

        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:limit]

    def _suggest_from_local(
        self,
        detected_patterns: list
    ) -> list[SkillSuggestion]:
        """
        Create suggestions from local detected patterns.

        Args:
            detected_patterns: List of DetectedPattern objects

        Returns:
            List of SkillSuggestion objects
        """
        suggestions = []

        for pattern in detected_patterns:
            if pattern.confidence >= 0.7:  # Only suggest high-confidence patterns
                suggestions.append(SkillSuggestion(
                    name=pattern.suggested_name,
                    description=pattern.suggested_description,
                    source="local",
                    confidence=pattern.confidence,
                    pattern_match={
                        "tool_sequence": pattern.tool_sequence,
                        "occurrences": pattern.occurrence_count,
                        "success_rate": pattern.success_rate
                    }
                ))

        return suggestions

    def _suggest_from_mental(
        self,
        file_paths: list[str],
        session_context: Optional[dict]
    ) -> list[SkillSuggestion]:
        """
        Create suggestions from Mental model.

        Args:
            file_paths: List of file paths being worked on
            session_context: Session context (intent, domains, etc.)

        Returns:
            List of SkillSuggestion objects
        """
        if not self.mental:
            return []

        suggestions = []

        # Load Mental model
        mental_model = self._get_mental_model()
        if not mental_model:
            return []

        # Get relevant domains from file paths
        relevant_domains = self.mental.get_relevant_domains(file_paths)
        if not relevant_domains:
            return []

        # Get capabilities for these domains
        capabilities = self.mental.get_capabilities_for_domains(relevant_domains)

        # Generate skill hints for each capability
        for capability in capabilities:
            skill_hints = self.mental.suggest_skills_for_capability(capability)

            for hint in skill_hints:
                suggestions.append(SkillSuggestion(
                    name=hint["name"],
                    description=f"Skill for {capability.name}: {capability.description}",
                    source="mental-hint",
                    confidence=hint.get("confidence", 0.6),
                    mental_context={
                        "domains": [d.name for d in relevant_domains],
                        "capability": capability.name,
                        "operates_on": capability.operates_on
                    }
                ))

        return suggestions

    def _suggest_from_external(
        self,
        session_context: dict
    ) -> list[SkillSuggestion]:
        """
        Create suggestions from Skills.sh based on context.

        Args:
            session_context: Session context (intent, domains, etc.)

        Returns:
            List of SkillSuggestion objects
        """
        if not self.skillssh:
            return []

        suggestions = []

        # Build search query from session context
        query = self._build_search_query(session_context)
        if not query:
            return []

        # Search Skills.sh
        external_skills = self.skillssh.search(query, limit=5)

        for ext_skill in external_skills:
            # Check if already adopted
            adoption = self.tracker.get_adoption(ext_skill.id)

            # Determine confidence
            if adoption:
                confidence = adoption.current_confidence
            else:
                confidence = 0.5  # Default for new external skills

            suggestions.append(SkillSuggestion(
                name=ext_skill.name,
                description=ext_skill.description,
                source="external",
                confidence=confidence,
                tags=ext_skill.tags,
                external_metadata={
                    "id": ext_skill.id,
                    "author": ext_skill.author,
                    "install_count": ext_skill.install_count,
                    "source_url": ext_skill.source_url,
                    "compatible_agents": ext_skill.compatible_agents
                },
                adoption=adoption
            ))

        return suggestions

    def _build_search_query(self, session_context: dict) -> str:
        """
        Build Skills.sh search query from session context.

        Args:
            session_context: Session context

        Returns:
            Search query string
        """
        query_parts = []

        # Add primary intent
        if "primary_intent" in session_context:
            query_parts.append(session_context["primary_intent"])

        # Add problem domains (limit to 2)
        if "problem_domains" in session_context:
            domains = session_context["problem_domains"]
            if isinstance(domains, list):
                query_parts.extend(domains[:2])

        # Add workflow type if relevant
        if "workflow_type" in session_context:
            workflow = session_context["workflow_type"]
            if workflow not in ["unknown", "general"]:
                query_parts.append(workflow)

        return " ".join(query_parts)

    def _deduplicate(
        self,
        suggestions: list[SkillSuggestion]
    ) -> list[SkillSuggestion]:
        """
        Remove duplicate suggestions (prefer higher confidence).

        Args:
            suggestions: List of suggestions (may have duplicates)

        Returns:
            Deduplicated list
        """
        seen = {}

        for suggestion in suggestions:
            # Normalize key (lowercase, replace hyphens with underscores)
            key = suggestion.name.lower().replace("-", "_").replace(" ", "_")

            # Keep highest confidence version
            if key not in seen or suggestion.confidence > seen[key].confidence:
                seen[key] = suggestion

        return list(seen.values())

    def _get_mental_model(self) -> Optional[MentalModel]:
        """
        Get Mental model (cached).

        Returns:
            MentalModel if available, None otherwise
        """
        if not self.mental:
            return None

        if self._mental_model is None:
            self._mental_model = self.mental.load_model()

        return self._mental_model

    def record_skill_usage(
        self,
        skill_name: str,
        skill_source: str,
        success: bool
    ) -> bool:
        """
        Record that a skill was used.

        Updates adoption tracking and checks for graduation eligibility.

        Args:
            skill_name: Name of skill
            skill_source: Source ("local", "external", "mental-hint")
            success: Whether usage was successful

        Returns:
            True if skill is ready to graduate, False otherwise
        """
        # Generate skill ID from name
        skill_id = skill_name.lower().replace(" ", "-").replace("_", "-")

        # Record usage
        self.tracker.record_skill_usage(
            skill_id=skill_id,
            skill_name=skill_name,
            source=skill_source,
            success=success
        )

        # Check if should graduate to local
        if skill_source == "external" and self.tracker.should_graduate_to_local(skill_id):
            return True

        return False

    def get_graduation_candidates(self) -> list[SkillAdoption]:
        """
        Get skills that are ready to graduate to local.

        Returns:
            List of SkillAdoption objects ready for graduation
        """
        return self.tracker.get_graduation_candidates()

    def graduate_skill(self, skill_id: str):
        """
        Graduate an external skill to local.

        Args:
            skill_id: Skill identifier
        """
        self.tracker.mark_graduated(skill_id)

    def get_adoption_stats(self, min_confidence: float = 0.0) -> list[SkillAdoption]:
        """
        Get adoption statistics for all tracked skills.

        Args:
            min_confidence: Minimum confidence threshold

        Returns:
            List of SkillAdoption objects
        """
        return self.tracker.get_all_adoptions(min_confidence=min_confidence)
