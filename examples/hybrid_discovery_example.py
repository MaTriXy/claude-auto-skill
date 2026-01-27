#!/usr/bin/env python3
"""
Hybrid Discovery Example - Shows how to use UnifiedSuggester with pattern detection.

This example demonstrates the full hybrid discovery flow:
1. Detect patterns from local tool usage
2. Analyze Mental model context
3. Search external skills from Skills.sh
4. Combine and rank suggestions
5. Track adoption and confidence evolution
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    EventStore,
    PatternDetector,
    SessionAnalyzer,
    UnifiedSuggester,
)


def example_1_basic_discovery():
    """Example 1: Basic skill discovery."""
    print("=" * 70)
    print("Example 1: Basic Skill Discovery")
    print("=" * 70)
    print()

    # Initialize suggester
    suggester = UnifiedSuggester(
        project_path=Path.cwd(),
        enable_mental=True,
        enable_external=True
    )

    # Get suggestions (in real use, would come from pattern detector)
    suggestions = suggester.suggest_for_context(
        detected_patterns=[],
        session_context={
            "primary_intent": "implement",
            "problem_domains": ["payment", "authentication"]
        },
        file_paths=["src/payment/checkout.py", "src/auth/login.py"]
    )

    print(f"Found {len(suggestions)} suggestions:\n")

    for suggestion in suggestions:
        confidence_pct = int(suggestion.confidence * 100)
        print(f"• {suggestion.name} ({suggestion.source}) - {confidence_pct}%")
        print(f"  {suggestion.description}")
        print()


def example_2_with_pattern_detection():
    """Example 2: Integration with pattern detection."""
    print("=" * 70)
    print("Example 2: Integration with Pattern Detection")
    print("=" * 70)
    print()

    # Initialize components
    store = EventStore()
    detector = PatternDetector(store, enable_v2=True)
    suggester = UnifiedSuggester()

    # Detect patterns from local usage
    patterns = detector.detect_patterns(min_occurrences=2)

    print(f"Detected {len(patterns)} local patterns")
    print()

    # Get hybrid suggestions (combining local patterns with external)
    suggestions = suggester.suggest_for_context(
        detected_patterns=patterns,
        session_context={"primary_intent": "implement"}
    )

    print(f"Combined suggestions ({len(suggestions)} total):\n")

    for suggestion in suggestions:
        source_icon = {
            "local": "🏠",
            "external": "🌐",
            "mental-hint": "🧠"
        }.get(suggestion.source, "❓")

        confidence_pct = int(suggestion.confidence * 100)
        print(f"{source_icon} {suggestion.name} - {confidence_pct}%")
        print(f"   Source: {suggestion.source}")

        if suggestion.adoption:
            print(f"   Used: {suggestion.adoption.usage_count} times")

        print()


def example_3_track_adoption():
    """Example 3: Track skill adoption and confidence evolution."""
    print("=" * 70)
    print("Example 3: Track Adoption & Confidence Evolution")
    print("=" * 70)
    print()

    suggester = UnifiedSuggester()

    # Simulate using an external skill multiple times
    print("Simulating external skill usage:\n")

    skill_name = "stripe-integration"
    skill_source = "external"

    for i in range(7):
        success = i < 6  # 6 successes, 1 failure
        suggester.record_skill_usage(skill_name, skill_source, success)

        adoption = suggester.tracker.get_adoption(
            skill_name.lower().replace(" ", "-")
        )

        if adoption:
            confidence_pct = int(adoption.current_confidence * 100)
            print(f"  Use {i+1}: Confidence = {confidence_pct}% "
                  f"(Success Rate: {adoption.success_rate:.0%})")

    print()

    # Check if ready to graduate
    skill_id = skill_name.lower().replace(" ", "-")
    if suggester.tracker.should_graduate_to_local(skill_id):
        print(f"✨ '{skill_name}' is ready to graduate to local skill!")
        print()
        print("Graduation criteria met:")
        print("  ✅ Confidence ≥ 85%")
        print("  ✅ Used ≥ 5 times")
        print("  ✅ Success rate ≥ 80%")
    else:
        adoption = suggester.tracker.get_adoption(skill_id)
        print(f"'{skill_name}' not ready yet:")
        print(f"  Confidence: {adoption.current_confidence:.0%}")
        print(f"  Uses: {adoption.usage_count}")
        print(f"  Success Rate: {adoption.success_rate:.0%}")


def example_4_domain_suggestions():
    """Example 4: Suggest skills for a Mental domain."""
    print("=" * 70)
    print("Example 4: Domain-Based Suggestions")
    print("=" * 70)
    print()

    suggester = UnifiedSuggester(enable_mental=True, enable_external=False)

    # Suggest skills for Payment domain
    domain = "Payment"
    suggestions = suggester.suggest_for_domain(domain, limit=5)

    if suggestions:
        print(f"Skills for '{domain}' domain:\n")

        for suggestion in suggestions:
            confidence_pct = int(suggestion.confidence * 100)
            print(f"• {suggestion.name} - {confidence_pct}%")
            print(f"  {suggestion.description}")
            if suggestion.mental_context:
                print(f"  Capability: {suggestion.mental_context.get('capability', 'N/A')}")
            print()
    else:
        print(f"No Mental model found or domain '{domain}' not defined.")
        print("\nTo add a domain:")
        print(f"  mental add domain {domain} --desc 'Payment processing'")
        print(f"  mental add capability Checkout --operates-on {domain}")


def example_5_graduation_candidates():
    """Example 5: Show skills ready for graduation."""
    print("=" * 70)
    print("Example 5: Graduation Candidates")
    print("=" * 70)
    print()

    suggester = UnifiedSuggester()

    candidates = suggester.get_graduation_candidates()

    if candidates:
        print(f"Found {len(candidates)} skills ready to graduate:\n")

        for adoption in candidates:
            confidence_pct = int(adoption.current_confidence * 100)
            print(f"⭐ {adoption.skill_name}")
            print(f"   Confidence: {confidence_pct}%")
            print(f"   Usage: {adoption.usage_count} times")
            print(f"   Success Rate: {adoption.success_rate:.0%}")
            print()
    else:
        print("No skills ready for graduation yet.")
        print("\nGraduation happens when:")
        print("  • External skill is used successfully ≥5 times")
        print("  • Success rate ≥80%")
        print("  • Confidence reaches ≥85%")


def main():
    """Run all examples."""
    examples = [
        example_1_basic_discovery,
        example_2_with_pattern_detection,
        example_3_track_adoption,
        example_4_domain_suggestions,
        example_5_graduation_candidates,
    ]

    for i, example in enumerate(examples):
        if i > 0:
            print("\n" + "=" * 70)
            input("\nPress Enter to continue to next example...")
            print()

        try:
            example()
        except Exception as e:
            print(f"❌ Example failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("All examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
