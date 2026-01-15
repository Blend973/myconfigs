#!/usr/bin/env bash
export CLI_PREVIEW_IMAGES_CACHE_DIR="/home/user/.cache/yt-browser/preview_images"
export CLI_PREVIEW_SCRIPTS_DIR="/home/user/.cache/yt-browser/preview_text"
export IMAGE_RENDERER="chafa"

generate_sha256() {
  local input
  if [ -n "$1" ]; then input="$1"; else input=$(cat); fi
  if command -v sha256sum &>/dev/null; then echo -n "$input" | sha256sum | awk '{print $1}'
  elif command -v shasum &>/dev/null; then echo -n "$input" | shasum -a 256 | awk '{print $1}'
  else echo -n "$input" | base64 | tr '/+' '_-' | tr -d '\n'; fi
}

fzf_preview() {
  file=$1
  dim=${FZF_PREVIEW_COLUMNS}x${FZF_PREVIEW_LINES}
  if [ "$dim" = x ]; then dim=$(stty size </dev/tty | awk "{print \$2 \"x\" \$1}"); fi

  if ! [ "$IMAGE_RENDERER" = "icat" ] && [ -z "$KITTY_WINDOW_ID" ]; then
     dim=${FZF_PREVIEW_COLUMNS}x$((FZF_PREVIEW_LINES - 1))
  fi

  if [ "$IMAGE_RENDERER" = "icat" ] || [ -n "$KITTY_WINDOW_ID" ]; then
    if command -v kitten >/dev/null 2>&1; then
      kitten icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\$d" | sed "$(printf "\$s/\$/\033[m/")"
    elif command -v icat >/dev/null 2>&1; then
      icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\$d" | sed "$(printf "\$s/\$/\033[m/")"
    else
      kitty icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\$d" | sed "$(printf "\$s/\$/\033[m/")"
    fi
  elif command -v chafa >/dev/null 2>&1; then
    chafa -s "$dim" "$file"; echo
  elif command -v imgcat >/dev/null; then
    imgcat -W "${dim%%x*}" -H "${dim##*x}" "$file"
  else
    echo "No image renderer found"
  fi
}
export -f generate_sha256
export -f fzf_preview
