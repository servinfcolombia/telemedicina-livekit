#!/bin/bash
PHASE=$1
STATUS=$2
TIMESTAMP=$(date -Iseconds)

if [ -z "$PHASE" ]; then
  echo "Usage: $0 <phase> <status>"
  exit 1
fi

PROGRESS_FILE=".opencode/PROGRESS.md"

if [ ! -f "$PROGRESS_FILE" ]; then
  echo "Error: $PROGRESS_FILE not found"
  exit 1
fi

sed -i "s/| 🔄 $PHASE.*/| ✅ $PHASE | ✔️ Done | $TIMESTAMP | ✔️ | Fase completada |/" "$PROGRESS_FILE"

echo "Phase $PHASE marked as completed at $TIMESTAMP"

if command -v notify-send &> /dev/null; then
  notify-send "✅ Fase completada" "$PHASE: $STATUS"
fi

exit 0
