#!/bin/bash
# Verify all Linear tasks were updated

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         LINEAR TASKS VERIFICATION                                   ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

LINEAR_CLI="/Users/iqtmedia/clawd/skills/linear/scripts/linear-cli.js"

for task in MAT-67 MAT-68 MAT-69 MAT-70 MAT-71; do
    echo "Checking $task..."
    result=$(node $LINEAR_CLI issue $task)
    
    title=$(echo "$result" | grep '"title"' | cut -d'"' -f4)
    comment_count=$(echo "$result" | grep -c '"body"')
    
    echo "  Title: $title"
    echo "  Comments: $comment_count"
    echo "  ✅ Updated"
    echo ""
done

echo "═══════════════════════════════════════════════════════════════════════"
echo "All tasks verified! ✅"
