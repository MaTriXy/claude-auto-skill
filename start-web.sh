#!/bin/bash
# Start Auto-Skill Web UI (wrapper script)

cd "$(dirname "$0")/web"
./start-web.sh "$@"
