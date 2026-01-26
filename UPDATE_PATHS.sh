#!/bin/bash
# Update all documentation to reflect new location

OLD_PATH="/Users/iqtmedia/Dev/projects/claude-auto-skill"
NEW_PATH="/Users/iqtmedia/Dev/projects/claude-auto-skill"

echo "Updating paths in documentation..."

for file in *.md *.sh; do
    if [ -f "$file" ]; then
        sed -i.bak "s|$OLD_PATH|$NEW_PATH|g" "$file"
        rm -f "${file}.bak"
        echo "  Updated $file"
    fi
done

echo "Paths updated!"
