# Examples

This directory contains examples demonstrating Auto-Skill features.

## Hybrid Discovery Example

**File:** `hybrid_discovery_example.py`

Demonstrates the hybrid skill discovery system (Phase 1 & 2 of MAT-92):

### Features Shown

1. **Basic Discovery** - Get suggestions from all sources
2. **Pattern Integration** - Combine local patterns with external skills
3. **Adoption Tracking** - Track usage and confidence evolution
4. **Domain Suggestions** - Mental model-based skill hints
5. **Graduation** - External skills graduating to local

### Run It

```bash
cd ~/Dev/projects/auto-skill
python3 examples/hybrid_discovery_example.py
```

### What It Does

- Demonstrates UnifiedSuggester combining Mental + Skills.sh + local patterns
- Shows confidence evolution (50% → 75% → 85%)
- Simulates skill adoption lifecycle
- Examples domain-based suggestions
- Shows graduation candidates

### Example Output

```
============================================================
Example 3: Track Adoption & Confidence Evolution
============================================================

Simulating external skill usage:

  Use 1: Confidence = 53% (Success Rate: 100%)
  Use 2: Confidence = 56% (Success Rate: 100%)
  Use 3: Confidence = 60% (Success Rate: 100%)
  Use 4: Confidence = 63% (Success Rate: 100%)
  Use 5: Confidence = 67% (Success Rate: 100%)
  Use 6: Confidence = 70% (Success Rate: 100%)
  Use 7: Confidence = 85% (Success Rate: 86%)

✨ 'stripe-integration' is ready to graduate to local skill!

Graduation criteria met:
  ✅ Confidence ≥ 85%
  ✅ Used ≥ 5 times
  ✅ Success rate ≥ 80%
```

## More Examples Coming

Future examples will cover:
- V2 session analysis
- LSP code structure detection
- Design pattern recognition
- Custom skill generation
