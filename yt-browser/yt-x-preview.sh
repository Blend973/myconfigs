#!/usr/bin/env bash
source "/home/user/.config/yt-browser/yt-x-helper.sh"
MODE="$1"; shift; SELECTION="$*"

if [ "$MODE" = "video" ]; then
  title="$SELECTION"
  # Remove the numbering (e.g. "01 ") before hashing
  clean_title=$(echo "$title" | sed -E 's/^[0-9]+ //g')
  id=$(generate_sha256 "$clean_title")
  if [ -f "/home/user/.cache/yt-browser/preview_text/${id}.txt" ]; then
    . "/home/user/.cache/yt-browser/preview_text/${id}.txt"
  else
    echo "Loading Preview..."
  fi
fi
