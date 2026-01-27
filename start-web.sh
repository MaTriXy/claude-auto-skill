#!/bin/bash
# Start Claude Auto-Skill Web UI (wrapper script)

cd "$(dirname "$0")/web"
./start-web.sh "$@"
