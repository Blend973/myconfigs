#!/usr/bin/env python3
# A script converted to Python from Bash (original by Benexl)
# Fixed for Fish shell users by isolating Bash preview logic.

import os
import sys
import json
import time
import shutil
import subprocess
import hashlib
import argparse
import platform
import urllib.parse
import re
import shlex

# ==========================================
# GLOBAL VARIABLES & CONFIGURATION
# ==========================================

CLI_HEADER = r"""
██╗░░░██╗████████╗░░░░░░██╗░░██╗
╚██╗░██╔╝╚══██╔══╝░░░░░░╚██╗██╔╝
░╚████╔╝░░░░██║░░░█████╗░╚███╔╝░
░░╚██╔╝░░░░░██║░░░╚════╝░██╔██╗░
░░░██║░░░░░░██║░░░░░░░░░██╔╝╚██╗
░░░╚═╝░░░░░░╚═╝░░░░░░░░░╚═╝░░╚═╝
"""

CLI_NAME = os.environ.get("YT_X_APP_NAME", "yt-browser")
CLI_VERSION = "0.4.5"
CLI_AUTHOR = "Benexl"
CLI_DIR = os.path.dirname(os.path.realpath(__file__))

# XDG Base Directory specification
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache"))
XDG_VIDEOS_DIR = os.environ.get("XDG_VIDEOS_DIR", os.path.join(os.path.expanduser("~"), "Videos"))

CLI_CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, CLI_NAME)
CLI_EXTENSION_DIR = os.path.join(CLI_CONFIG_DIR, "extensions")
CLI_CACHE_DIR = os.path.join(XDG_CACHE_HOME, CLI_NAME)
CLI_PREVIEW_IMAGES_CACHE_DIR = os.path.join(CLI_CACHE_DIR, "preview_images")
CLI_YT_DLP_ARCHIVE = os.path.join(CLI_CACHE_DIR, "yt-dlp-archive")
CLI_AUTO_GEN_PLAYLISTS = os.path.join(CLI_CACHE_DIR, "playlists")
CLI_PREVIEW_SCRIPTS_DIR = os.path.join(CLI_CACHE_DIR, "preview_text")
CLI_HELPER_SCRIPT = os.path.join(CLI_CONFIG_DIR, "yt-x-helper.sh")
CLI_PREVIEW_DISPATCHER = os.path.join(CLI_CONFIG_DIR, "yt-x-preview.sh")
CLI_SUPPORT_PROJECT_URL = "https://buymeacoffee.com/benexl"

# Ensure directories exist
for d in [CLI_CONFIG_DIR, CLI_EXTENSION_DIR, CLI_PREVIEW_IMAGES_CACHE_DIR,
          CLI_PREVIEW_SCRIPTS_DIR, CLI_YT_DLP_ARCHIVE, CLI_AUTO_GEN_PLAYLISTS]:
    os.makedirs(d, exist_ok=True)

# Platform detection
uname = platform.uname().system.lower()
if "android" in uname or "android" in platform.release().lower():
    PLATFORM = "android"
elif "darwin" in uname:
    PLATFORM = "mac"
elif "windows" in uname or "microsoft" in platform.release().lower():
    PLATFORM = "windows"
else:
    PLATFORM = "linux"

# Default Config Dictionary
CONFIG = {
    "PRETTY_PRINT": "true",
    "IMAGE_RENDERER": "",
    "DISOWN_STREAMING_PROCESS": "true",
    "EDITOR": os.environ.get("EDITOR", "open"),
    "PREFERRED_SELECTOR": "fzf",
    "VIDEO_QUALITY": "1080",
    "ENABLE_PREVIEW": "false",
    "UPDATE_RECENT": "true",
    "NO_OF_RECENT": "30",
    "PLAYER": "mpv",
    "PREFERRED_BROWSER": "",
    "NO_OF_SEARCH_RESULTS": "30",
    "NOTIFICATION_DURATION": "5",
    "SEARCH_HISTORY": "true",
    "DOWNLOAD_DIRECTORY": os.path.join(XDG_VIDEOS_DIR, CLI_NAME),
    "UPDATE_CHECK": "true",
    "WELCOME_SCREEN": "true",
    "ROFI_THEME": "",
    "AUTO_LOADED_EXTENSIONS": ""
}

# Global State
PLAYLIST_START = 1
PLAYLIST_END = 30
CURRENT_TIME = int(time.time())

# Colors
RED = ""
MAGENTA = ""
CYAN = ""
BOLD = ""
RESET = ""

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def generate_sha256(text):
    if text is None:
        text = ""
    if isinstance(text, str):
        text = text.encode('utf-8')
    return hashlib.sha256(text).hexdigest()

def send_notification(message):
    sys.stderr.write(f"{message}\n")
    time.sleep(int(CONFIG["NOTIFICATION_DURATION"]))

def byebye(code=0):
    os.system('clear')
    user = os.environ.get("USER", "User")
    print(f"Have a good day {user}")
    sys.exit(code)

def init_pretty_print():
    global RED, MAGENTA, CYAN, BOLD, RESET
    if CONFIG["PRETTY_PRINT"] == "true":
        try:
            RED = subprocess.check_output(['tput', 'setaf', '1'], text=True).strip()
            MAGENTA = "\x1b[38;2;215;0;95m"
            CYAN = subprocess.check_output(['tput', 'setaf', '6'], text=True).strip()
            BOLD = subprocess.check_output(['tput', 'bold'], text=True).strip()
            RESET = subprocess.check_output(['tput', 'sgr0'], text=True).strip()
        except:
            RED = "\033[31m"
            MAGENTA = "\033[35m"
            CYAN = "\033[36m"
            BOLD = "\033[1m"
            RESET = "\033[0m"

def create_bash_helpers():
    """
    Creates bash scripts for fzf preview logic.
    This isolates Bash syntax from the user's shell (e.g., Fish).
    """

    # 1. Helper Functions Script
    helper_content = f"""#!/usr/bin/env bash
export CLI_PREVIEW_IMAGES_CACHE_DIR="{CLI_PREVIEW_IMAGES_CACHE_DIR}"
export CLI_PREVIEW_SCRIPTS_DIR="{CLI_PREVIEW_SCRIPTS_DIR}"
export CLI_CONFIG_DIR="{CLI_CONFIG_DIR}"
export IMAGE_RENDERER="{CONFIG['IMAGE_RENDERER']}"
export PLATFORM="{PLATFORM}"

generate_sha256() {{
  local input
  if [ -n "$1" ]; then input="$1"; else input=$(cat); fi
  if command -v sha256sum &>/dev/null; then echo -n "$input" | sha256sum | awk '{{print $1}}'
  elif command -v shasum &>/dev/null; then echo -n "$input" | shasum -a 256 | awk '{{print $1}}'
  elif command -v sha256 &>/dev/null; then echo -n "$input" | sha256 | awk '{{print $1}}'
  elif command -v openssl &>/dev/null; then echo -n "$input" | openssl dgst -sha256 | awk '{{print $2}}'
  else echo -n "$input" | base64 | tr '/+' '_-' | tr -d '\\n'; fi
}}

fzf_preview() {{
  file=$1
  dim=${{FZF_PREVIEW_COLUMNS}}x${{FZF_PREVIEW_LINES}}
  if [ "$dim" = x ]; then dim=$(stty size </dev/tty | awk "{{print \\$2 \\"x\\" \\$1}}"); fi

  if ! [ "$IMAGE_RENDERER" = "icat" ] && [ -z "$KITTY_WINDOW_ID" ]; then
     dim=${{FZF_PREVIEW_COLUMNS}}x$((FZF_PREVIEW_LINES - 1))
  fi

  if [ "$IMAGE_RENDERER" = "icat" ] || [ -n "$KITTY_WINDOW_ID" ]; then
    if command -v kitten >/dev/null 2>&1; then
      kitten icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\\$d" | sed "$(printf "\\$s/\\$/\\033[m/")"
    elif command -v icat >/dev/null 2>&1; then
      icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\\$d" | sed "$(printf "\\$s/\\$/\\033[m/")"
    else
      kitty icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\\$d" | sed "$(printf "\\$s/\\$/\\033[m/")"
    fi
  elif command -v chafa >/dev/null 2>&1; then
    case "$PLATFORM" in
    android) chafa -s "$dim" "$file" ;;
    windows) chafa -f sixel -s "$dim" "$file" ;;
    *) chafa -s "$dim" "$file" ;;
    esac
    echo
  elif command -v imgcat >/dev/null; then
    imgcat -W "${{dim%%x*}}" -H "${{dim##*x}}" "$file"
  else
    echo "No image renderer found"
  fi
}}
export -f generate_sha256
export -f fzf_preview
"""
    with open(CLI_HELPER_SCRIPT, 'w') as f:
        f.write(helper_content)
    os.chmod(CLI_HELPER_SCRIPT, 0o755)

    # 2. Preview Dispatcher Script
    # This script receives the mode and the selection string from fzf
    preview_content = f"""#!/usr/bin/env bash
source "{CLI_HELPER_SCRIPT}"

MODE="$1"
# Shift to get the rest of the arguments as the selection string
shift
SELECTION="$*"

MAGENTA='\\x1b[38;2;215;0;95m'
BOLD=$(tput bold)
RESET=$(tput sgr0)

if [ "$MODE" = "video" ]; then
  title="$SELECTION"
  id=$(echo "$title" | generate_sha256)
  if [ -f "{CLI_PREVIEW_SCRIPTS_DIR}/${{id}}.txt" ]; then
    . "{CLI_PREVIEW_SCRIPTS_DIR}/${{id}}.txt"
  else
    echo "Loading Preview..."
  fi

elif [ "$MODE" = "channel" ]; then
  if ! [ -z "$SELECTION" ] && ! [ "$SELECTION" = "Back" ] && ! [ "$SELECTION" = "Exit" ] && ! [ "$SELECTION" = "Main Menu" ]; then
    channels_data=$(cat "{CLI_CONFIG_DIR}/subscriptions.json")
    title="$(echo "$SELECTION" | sed 's/"/\\\\\\"/g')"
    video=$(echo "$channels_data" | jq -r ".entries | map(select(.title == \\"$title\\" )) | .[0]" 2>/dev/null)

    id=$(echo "$video" | jq '.thumbnails[-1].url' -r | generate_sha256)
    channel=$(echo "$video" | jq '.channel' -r)

    if [ -f "{CLI_PREVIEW_IMAGES_CACHE_DIR}/${{id}}.jpg" ]; then
      fzf_preview "{CLI_PREVIEW_IMAGES_CACHE_DIR}/${{id}}.jpg" 2>/dev/null
    else
      echo "loading preview image..."
    fi

    ll=1
    while [ $ll -le $FZF_PREVIEW_COLUMNS ]; do echo -n -e "─"; (( ll++ )); done
    printf "${{MAGENTA}}${{BOLD}}Channel: ${{RESET}}$channel\\n"
    ll=1
    while [ $ll -le $FZF_PREVIEW_COLUMNS ]; do echo -n -e "─"; (( ll++ )); done
  else
    echo "Loading..."
  fi

elif [ "$MODE" = "playlist" ]; then
  if ! [ -z "$SELECTION" ] && ! [ "$SELECTION" = "Back" ] && ! [ "$SELECTION" = "Exit" ] && ! [ "$SELECTION" = "Main Menu" ]; then
    title="$(echo "$SELECTION" | sed 's/"/\\\\\\"/g')"
    video=$(echo "$playlist_results" | jq -r ".entries | map(select(.title == \\"$title\\" )) | .[0]" 2>/dev/null)
    title="$(echo "$title" | sed 's/^.. //g')"
    id=$(echo "$video" | jq '.thumbnails[-1].url' -r | generate_sha256)

    if [ -f "{CLI_PREVIEW_IMAGES_CACHE_DIR}/${{id}}.jpg" ]; then
      fzf_preview "{CLI_PREVIEW_IMAGES_CACHE_DIR}/${{id}}.jpg" 2>/dev/null
    else
      echo "loading preview image..."
    fi

    ll=1
    while [ $ll -le $FZF_PREVIEW_COLUMNS ]; do echo -n -e "─"; (( ll++ )); done
    echo "$title"
    ll=1
    while [ $ll -le $FZF_PREVIEW_COLUMNS ]; do echo -n -e "─"; (( ll++ )); done
  else
    echo "Loading..."
  fi
fi
"""
    with open(CLI_PREVIEW_DISPATCHER, 'w') as f:
        f.write(preview_content)
    os.chmod(CLI_PREVIEW_DISPATCHER, 0o755)

def load_config():
    global CONFIG, PLAYLIST_END
    config_file = os.path.join(CLI_CONFIG_DIR, f"{CLI_NAME}.conf")

    if not os.path.exists(config_file):
        with open(config_file, 'w') as f:
            f.write(f"PRETTY_PRINT: true\nEDITOR: {os.environ.get('EDITOR', 'open')}\nPREFERRED_SELECTOR: fzf\n")

    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if ': ' in line:
                key, value = line.split(': ', 1)
                CONFIG[key] = value

    if not CONFIG["IMAGE_RENDERER"]:
        CONFIG["IMAGE_RENDERER"] = "icat" if os.environ.get("KITTY_WINDOW_ID") else "chafa"

    if CONFIG["PREFERRED_BROWSER"] and "--cookies-from-browser" not in CONFIG["PREFERRED_BROWSER"]:
        CONFIG["PREFERRED_BROWSER"] = f"--cookies-from-browser {CONFIG['PREFERRED_BROWSER']}"

    CONFIG["DOWNLOAD_DIRECTORY"] = os.path.expandvars(os.path.expanduser(CONFIG["DOWNLOAD_DIRECTORY"]))
    if not os.path.exists(CONFIG["DOWNLOAD_DIRECTORY"]):
        os.makedirs(CONFIG["DOWNLOAD_DIRECTORY"], exist_ok=True)

    PLAYLIST_END = int(CONFIG["NO_OF_SEARCH_RESULTS"])
    init_pretty_print()
    create_bash_helpers()

    os.environ["FZF_DEFAULT_OPTS"] = os.environ.get("YT_X_FZF_OPTS", """
    --color=fg:#d0d0d0,fg+:#d0d0d0,bg:#121212,bg+:#262626
    --color=hl:#5f87af,hl+:#5fd7ff,info:#afaf87,marker:#87ff00
    --color=prompt:#d7005f,spinner:#af5fff,pointer:#af5fff,header:#87afaf
    --color=border:#262626,label:#aeaeae,query:#d9d9d9
    --border="rounded" --border-label="" --preview-window="border-rounded" --prompt="> "
    --marker=">" --pointer="◆" --separator="─" --scrollbar="│"
    """)
    os.environ["PRETTY_PRINT"] = CONFIG["PRETTY_PRINT"]
    os.environ["PLATFORM"] = PLATFORM
    os.environ["IMAGE_RENDERER"] = CONFIG["IMAGE_RENDERER"]

def confirm(question):
    if shutil.which("gum"):
        return subprocess.call(["gum", "confirm", question]) == 0
    else:
        sys.stderr.write(f"{CLI_HEADER}\n")
        sys.stderr.write(f"{question} [y/N]: ")
        sys.stderr.flush()
        try:
            response = input().strip().lower()
            return response == 'y'
        except EOFError:
            return False

def prompt(text, value=""):
    history_file = os.path.join(CLI_CACHE_DIR, "search_history.txt")
    history_text = ""
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            lines = [l.strip() for l in f if l.strip()]
        lines = lines[-10:]
        lines.reverse()
        history_formatted = "\n".join([f"{i+1}. {l}" for i, l in enumerate(lines)])
        history_text = f"Search history:\n{history_formatted}\n(Enter !<n> to select from history. Example: !1)\n"

    if CONFIG["PREFERRED_SELECTOR"] == "rofi":
        cmd = ["rofi", "-dmenu", "-p", f"{text}: "]
        if CONFIG["SEARCH_HISTORY"] == "true" and history_text:
             cmd.extend(["-mesg", history_text])

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate(input="")
        return out.strip()

    elif shutil.which("gum"):
        header = CLI_HEADER
        if CONFIG["SEARCH_HISTORY"] == "true" and history_text:
            header += "\n" + history_text

        cmd = ["gum", "input", "--header", header, "--prompt", f"{text}: ", "--value", value]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return proc.stdout.strip()

    else:
        sys.stderr.write(f"{CLI_HEADER}\n")
        if CONFIG["SEARCH_HISTORY"] == "true" and history_text:
            sys.stderr.write(f"{history_text}\n")
        sys.stderr.write(f"{text}: ")
        sys.stderr.flush()
        try:
            return input().strip()
        except EOFError:
            return ""

def launcher(options_str, prompt_text, preview_mode=None):
    selector = CONFIG["PREFERRED_SELECTOR"].lower()

    if selector == "rofi":
        cmd = ["rofi", "-sort", "-matching", "fuzzy", "-dmenu", "-i", "-p", "", "-mesg", prompt_text, "-matching", "fuzzy", "-sorting-method", "fzf"]
        if CONFIG["ROFI_THEME"]:
            cmd[1:1] = ["-no-config", "-theme", CONFIG["ROFI_THEME"]]
        else:
            cmd.extend(["-width", "1500"])

        clean_options = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', options_str)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate(input=clean_options)
        res = out.strip()
        return res if res else "Exit"

    else: # fzf
        cmd = [
            "fzf",
            "--info=hidden",
            "--layout=reverse",
            "--height=100%",
            f"--prompt={prompt_text}: ",
            "--header-first",
            f"--header={CLI_HEADER}",
            "--exact", "--cycle", "--ansi"
        ]

        if preview_mode:
            # We call the bash dispatcher script explicitly.
            # {} is passed as the last argument.
            # This avoids Fish shell syntax errors because fzf executes 'bash ...' directly.
            cmd.extend([
                "--preview-window=left,35%,wrap",
                "--bind=right:accept",
                "--expect=shift-left,shift-right",
                "--tabstop=1",
                f"--preview=bash '{CLI_PREVIEW_DISPATCHER}' '{preview_mode}' {{}}"
            ])

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate(input=options_str)

        lines = out.splitlines()
        if not lines:
            return ""
        if preview_mode and len(lines) >= 2:
            return lines[1]
        return lines[0]

def run_yt_dlp(url, extra_args=None):
    cmd = ["yt-dlp", url, "-J", "--flat-playlist", "--extractor-args", "youtubetab:approximate_date",
           "--playlist-start", str(PLAYLIST_START), "--playlist-end", str(PLAYLIST_END)]

    if CONFIG["PREFERRED_BROWSER"]:
        cmd.extend(shlex.split(CONFIG["PREFERRED_BROWSER"]))

    if extra_args:
        cmd.extend(extra_args)

    if shutil.which("gum"):
        spin_cmd = ["gum", "spin", "--show-output", "--"] + cmd
        proc = subprocess.run(spin_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    else:
        sys.stderr.write("Loading...\n")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if proc.returncode != 0:
        send_notification("Failed to fetch data : (")
        return None

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None

# ==========================================
# PREVIEW GENERATION
# ==========================================

def generate_text_preview(data):
    if not data or "entries" not in data:
        return

    entries = data["entries"]
    for i, video in enumerate(entries):
        if not video: continue

        title = (video.get("title") or "").replace('"', '\\"').replace('%', '%%').replace('$', '\\$')
        title = re.sub(r'^.. ', '', title)

        filename_hash = generate_sha256(video.get("title", ""))

        thumbs = video.get("thumbnails", [])
        thumb_url = thumbs[-1]["url"] if thumbs else ""
        preview_image_hash = generate_sha256(thumb_url)

        vc = video.get("view_count")
        view_count = "{:,}".format(int(vc)) if vc is not None else "Unknown"

        ls = video.get("live_status")
        live_status = "Online" if ls == "is_live" else ("Offline" if ls == "was_live" else "False")

        description = (video.get("description") or "null").replace('"', '').replace('%', '')
        channel = video.get("channel", "")

        dur = video.get("duration")
        duration_str = "Unknown"
        if dur:
            try:
                dur = float(dur)
                if dur >= 3600: duration_str = f"{int(dur // 3600)} hours"
                elif dur >= 60: duration_str = f"{int(dur // 60)} mins"
                else: duration_str = f"{int(dur)} secs"
            except: pass

        ts = video.get("timestamp")
        timestamp_str = ""
        if ts:
            try:
                diff = CURRENT_TIME - int(ts)
                if diff < 60: timestamp_str = "just now"
                elif diff < 3600: timestamp_str = f"{diff // 60} minutes ago"
                elif diff < 86400: timestamp_str = f"{diff // 3600} hours ago"
                elif diff < 604800: timestamp_str = f"{diff // 86400} days ago"
                elif diff < 2635200: timestamp_str = f"{diff // 604800} weeks ago"
                elif diff < 31622400: timestamp_str = f"{diff // 2635200} months ago"
                else: timestamp_str = f"{diff // 31622400} years ago"
            except: pass

        content = f"""
if [ -f "{CLI_PREVIEW_IMAGES_CACHE_DIR}/{preview_image_hash}.jpg" ];then fzf_preview "{CLI_PREVIEW_IMAGES_CACHE_DIR}/{preview_image_hash}.jpg" 2>/dev/null;
else echo loading preview image...;
fi
ll=1
while [ $ll -le $FZF_PREVIEW_COLUMNS ];do echo -n -e "─" ;(( ll++ ));done;
echo

echo "{title}"

ll=1
while [ $ll -le $FZF_PREVIEW_COLUMNS ];do echo -n -e "─" ;(( ll++ ));done;
printf "${{MAGENTA}}${{BOLD}}Channel: ${{RESET}}{channel}\\n";
printf "${{MAGENTA}}${{BOLD}}Duration: ${{RESET}}{duration_str}\\n";
printf "${{MAGENTA}}${{BOLD}}View Count: ${{RESET}}{view_count} views\\n";
printf "${{MAGENTA}}${{BOLD}}Live Status: ${{RESET}}{live_status}\\n";
printf "${{MAGENTA}}${{BOLD}}Uploaded: ${{RESET}}{timestamp_str}\\n";

ll=1
while [ $ll -le $FZF_PREVIEW_COLUMNS ];do echo -n -e "─" ;(( ll++ ));done;
echo

! [ "{description}" = "null" ] && echo -n "{description}";
"""
        with open(os.path.join(CLI_PREVIEW_SCRIPTS_DIR, f"{filename_hash}.txt"), "w") as f:
            f.write(content)

def download_preview_images(data, prefix=""):
    if not data or "entries" not in data: return
    generate_text_preview(data)

    previews_file = os.path.join(CLI_PREVIEW_IMAGES_CACHE_DIR, "previews.txt")
    if os.path.exists(previews_file): os.remove(previews_file)

    entries_to_download = []
    for video in data["entries"]:
        if not video: continue
        thumbs = video.get("thumbnails", [])
        if not thumbs: continue
        url = thumbs[-1]["url"]
        filename = generate_sha256(url)

        if not os.path.exists(os.path.join(CLI_PREVIEW_IMAGES_CACHE_DIR, f"{filename}.jpg")):
            entries_to_download.append((url, filename))

    if entries_to_download:
        with open(previews_file, "w") as f:
            for url, filename in entries_to_download:
                f.write(f'url = "{prefix}{url}"\n')
                f.write(f'output = "{CLI_PREVIEW_IMAGES_CACHE_DIR}/{filename}.jpg"\n')

        subprocess.Popen(["curl", "-s", "-K", previews_file], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

# ==========================================
# CORE LOGIC
# ==========================================

def update_json_list(filename, video, add=True, limit=None):
    filepath = os.path.join(CLI_CONFIG_DIR, filename)
    data = {"entries": []}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f: data = json.load(f)
        except: pass

    vid_id = video.get("id")
    data["entries"] = [e for e in data["entries"] if e.get("id") != vid_id]

    if add:
        video_copy = video.copy()
        video_copy["title"] = re.sub(r'^[0-9]+ ', '', video_copy.get("title", ""))
        data["entries"].append(video_copy)

    if limit and len(data["entries"]) > limit:
        data["entries"] = data["entries"][-limit:]

    with open(filepath, 'w') as f: json.dump(data, f)

def update_recent(video):
    if CONFIG["UPDATE_RECENT"] != "true": return
    update_json_list("recent.json", video, add=True, limit=int(CONFIG["NO_OF_RECENT"]))

def playlist_explorer(search_results, url, urlForAll=None):
    global PLAYLIST_START, PLAYLIST_END
    download_images = False
    enumerate_playlist = ""

    while True:
        if not search_results or "entries" not in search_results: break

        entries = search_results.get("entries", [])
        titles = []
        
        # Only modify titles if we haven't already processed this batch (download_images is False)
        if not download_images:
            for i, entry in enumerate(entries):
                if not entry: continue
                num = str(i + 1)
                if len(entries) < 10 and len(num) < 2: num = "0" + num
                entry["title"] = f"{num} {entry.get('title', '')}"
                titles.append(entry["title"])
        else:
            # If already processed, just rebuild the titles list from the existing entries
            for entry in entries:
                if entry: titles.append(entry.get("title", ""))

        if CONFIG["ENABLE_PREVIEW"] == "true" and CONFIG["PREFERRED_SELECTOR"] == "fzf" and not download_images:
            download_preview_images(search_results)
            download_images = True

        if CONFIG["ENABLE_PREVIEW"] == "true":
            options_str = "\n".join(titles) + f"\nNext\nPrevious\n{CYAN}󰌍{RESET}  Back\n{CYAN}󰍜{RESET}  Main Menu\n{RED}󰈆{RESET}  Exit"
            selection = launcher(options_str, "select video", "video")
        else:
            options_str = "\n".join(titles + ["Next", "Previous", "Back", "Main Menu", "Exit"])
            selection = launcher(options_str, "select video")

        selection = re.sub(r'^[^0-9]*  ', '', selection)
        os.system('clear')

        if selection == "Next":
            PLAYLIST_START += int(CONFIG["NO_OF_SEARCH_RESULTS"])
            PLAYLIST_END += int(CONFIG["NO_OF_SEARCH_RESULTS"])
            search_results = run_yt_dlp(url)
            download_images = False
            continue
        elif selection == "Previous":
            PLAYLIST_START -= int(CONFIG["NO_OF_SEARCH_RESULTS"])
            if PLAYLIST_START <= 0: PLAYLIST_START = 1
            PLAYLIST_END -= int(CONFIG["NO_OF_SEARCH_RESULTS"])
            if PLAYLIST_END <= int(CONFIG["NO_OF_SEARCH_RESULTS"]): PLAYLIST_END = int(CONFIG["NO_OF_SEARCH_RESULTS"])
            search_results = run_yt_dlp(url)
            download_images = False
            continue
        elif selection == "Main Menu": return "Main Menu"
        elif selection in ["Back", "", "Exit"]:
            if selection == "Exit": byebye()
            break

        try:
            sel_id = int(selection.split(' ')[0])
            video = entries[sel_id - 1]
            clean_title = re.sub(r'^[0-9]+ ', '', video['title'])
        except (ValueError, IndexError): continue

        while True:
            media_actions = [
                f"{CYAN}{RESET}  Watch", f"{CYAN}{RESET}  Play All", f"{CYAN}󰎆{RESET}  Listen",
                f"{CYAN}{RESET}  Listen To All", f"{CYAN}{RESET}  Mix", f"{CYAN}{RESET}  Save",
                f"{CYAN}󰧎{RESET}  UnSave", f"{CYAN}󰐒{RESET}  Save Playlist", f"{CYAN}󰵀{RESET}  Subscribe To Channel",
                f"{CYAN}󱑤{RESET}  Download", f"{CYAN}󰦗{RESET}  Download All", f"{CYAN}󱑤{RESET}  Download (Audio Only)",
                f"{CYAN}󰦗{RESET}  Download All (Audio Only)", f"{CYAN}{RESET}  Open in Browser",
                f"{CYAN}{RESET}  Toggle Enumerate Downloads", f"{CYAN}{RESET}  Shell",
                f"{CYAN}󰌍{RESET}  Back", f"{RED}󰈆{RESET}  Exit"
            ]

            action_sel = launcher("\n".join(media_actions), "Select Media Action")
            action_sel = re.sub(r'.  ', '', action_sel)
            os.system('clear')

            if action_sel == "Exit": byebye()
            if action_sel in ["Back", ""]: break

            vid_url = video.get("url")

            if action_sel == "Watch":
                print(f"{MAGENTA}Now watching:{RESET} {clean_title}")
                if "list=RD" in vid_url:
                    vid_id = video.get("id", "").replace("RD", "")
                    mix_url = f"https://www.youtube.com/watch?v={vid_id}&list=RD{vid_id}"
                    cached_pl = os.path.join(CLI_AUTO_GEN_PLAYLISTS, f"{generate_sha256(mix_url)}.m3u8")
                    if not os.path.exists(cached_pl) or os.path.getsize(cached_pl) == 0:
                        mix_data = run_yt_dlp(mix_url)
                        if mix_data:
                            with open(cached_pl, 'w') as f:
                                f.write('#EXTM3U\n')
                                for entry in mix_data.get('entries', []):
                                    f.write(f"#EXTINF:-1,{entry.get('title')}\n{entry.get('url')}\n\n")
                    subprocess.Popen(["mpv", cached_pl], start_new_session=(CONFIG["DISOWN_STREAMING_PROCESS"]=="true"))
                else:
                    if CONFIG["PLAYER"] != "mpv" or PLATFORM == "android":
                        proc = subprocess.run(["yt-dlp", vid_url, "-q", "--no-warnings", "--get-url", "--format", f"best[height<={CONFIG['VIDEO_QUALITY']}]/best"], stdout=subprocess.PIPE, text=True)
                        vid_url = proc.stdout.strip().split('\n')[-1] if proc.stdout.strip() else ""

                    if CONFIG["PLAYER"] == "mpv":
                        subprocess.Popen(["mpv", vid_url], start_new_session=(CONFIG["DISOWN_STREAMING_PROCESS"]=="true"))
                    elif CONFIG["PLAYER"] == "vlc":
                        subprocess.Popen(["vlc", vid_url, "--video-title", clean_title], start_new_session=(CONFIG["DISOWN_STREAMING_PROCESS"]=="true"))
                update_recent(video)

            elif action_sel == "Listen":
                print(f"{MAGENTA}Now Listening to:{RESET} {clean_title}")
                if CONFIG["PLAYER"] != "mpv" or PLATFORM == "android":
                     proc = subprocess.run(["yt-dlp", vid_url, "-q", "--no-warnings", "--get-url", "--format", "bestaudio/best"], stdout=subprocess.PIPE, text=True)
                     vid_url = proc.stdout.strip().split('\n')[-1]
                if CONFIG["PLAYER"] == "mpv":
                    subprocess.Popen(["mpv", vid_url, "--no-video", "--force-window=no"], start_new_session=(CONFIG["DISOWN_STREAMING_PROCESS"]=="true"))
                update_recent(video)

            elif action_sel == "Download":
                out_tmpl = os.path.join(CONFIG["DOWNLOAD_DIRECTORY"], "videos/individual/%(channel)s/%(title)s.%(ext)s")
                cmd = ["yt-dlp", vid_url, "--output", out_tmpl]
                if CONFIG["PREFERRED_BROWSER"]: cmd.extend(shlex.split(CONFIG["PREFERRED_BROWSER"]))
                subprocess.Popen(cmd, start_new_session=True)
                send_notification(f"Started downloading {clean_title}")

            elif action_sel == "Download (Audio Only)":
                out_tmpl = os.path.join(CONFIG["DOWNLOAD_DIRECTORY"], "audio/individual/%(channel)s/%(title)s.%(ext)s")
                cmd = ["yt-dlp", vid_url, "-x", "-f", "bestaudio", "--audio-format", "mp3", "--output", out_tmpl]
                if CONFIG["PREFERRED_BROWSER"]: cmd.extend(shlex.split(CONFIG["PREFERRED_BROWSER"]))
                subprocess.Popen(cmd, start_new_session=True)
                send_notification(f"Started downloading {clean_title}")

            elif action_sel == "Save": update_json_list("saved_videos.json", video, add=True)
            elif action_sel == "UnSave": update_json_list("saved_videos.json", video, add=False)
            elif action_sel == "Open in Browser":
                if shutil.which("open"): subprocess.run(["open", vid_url])
                elif shutil.which("xdg-open"): subprocess.run(["xdg-open", vid_url])
            elif action_sel == "Toggle Enumerate Downloads":
                enumerate_playlist = "%(playlist_index)s - " if enumerate_playlist == "" else ""
            elif action_sel == "Mix":
                vid_id = video.get("id")
                mix_url = f"https://www.youtube.com/watch?v={vid_id}&list=RD{vid_id}"
                new_results = run_yt_dlp(mix_url)
                playlist_explorer(new_results, mix_url, urlForAll=mix_url)

            elif action_sel == "Shell":
                user_shell = os.environ.get("SHELL", "/bin/bash")
                shell_env = os.environ.copy()
                shell_env.update({
                    "url": vid_url,
                    "urlForAll": urlForAll if urlForAll else "",
                    "video_url": vid_url,
                    "playlist_title": clean_title,
                    "CLI_HEADER": CLI_HEADER,
                    "CLI_NAME": CLI_NAME,
                    "DOWNLOAD_DIRECTORY": CONFIG["DOWNLOAD_DIRECTORY"],
                    "CLI_YT_DLP_ARCHIVE": CLI_YT_DLP_ARCHIVE
                })
                init_text = f"{CLI_HEADER}\nWelcome to the {CLI_NAME} shell.\nVariables available: url, urlForAll, video_url, playlist_title, DOWNLOAD_DIRECTORY"
                print(f"Spawning {user_shell}...")
                if "fish" in user_shell:
                    subprocess.run([user_shell, "--init-command", f"clear; echo '{init_text}'"], env=shell_env)
                else:
                    print(init_text)
                    subprocess.run([user_shell], env=shell_env)

    PLAYLIST_START = 1
    PLAYLIST_END = int(CONFIG["NO_OF_SEARCH_RESULTS"])

def playlists_explorer(url):
    playlist_results = run_yt_dlp(url)
    if not playlist_results: return

    entries = playlist_results.get("entries", [])
    titles = []
    for i, entry in enumerate(entries):
        num = str(i + 1)
        if len(entries) < 10 and len(num) < 2: num = "0" + num
        entry["title"] = f"{num} {entry.get('title', '')}"
        titles.append(entry["title"])

    os.environ["playlist_results"] = json.dumps(playlist_results)
    if CONFIG["ENABLE_PREVIEW"] == "true" and CONFIG["PREFERRED_SELECTOR"] == "fzf":
        download_preview_images(playlist_results)

    while True:
        if CONFIG["ENABLE_PREVIEW"] == "true":
            options = "\n".join(titles) + f"\n{CYAN}󰌍{RESET}  Back\n{RED}󰈆{RESET}  Exit"
            sel = launcher(options, "select video", "playlist")
        else:
            options = "\n".join(titles) + "\nBack\nExit"
            sel = launcher(options, "select video")

        sel = re.sub(r'^[^0-9]*  ', '', sel).strip()
        os.system('clear')

        if "Back" in sel or not sel: break
        if "Exit" in sel: byebye()

        playlist = next((e for e in entries if e["title"] == sel), None)
        if playlist:
            pl_url = playlist.get("url")
            search_results = run_yt_dlp(pl_url)
            playlist_explorer(search_results, pl_url)

def channels_explorer(channel):
    while True:
        actions = [
            f"{CYAN}{RESET}  Videos", f"{CYAN}󰩉{RESET}  Featured", f"{CYAN}{RESET}  Search",
            f"{CYAN}󰐑{RESET}  Playlists", f"{CYAN}{RESET}  Shorts", f"{CYAN}󰠿{RESET}  Streams",
            f"{CYAN}{RESET}  Podcasts", f"{CYAN}󰵀{RESET}  Subscribe", f"{CYAN}󰌍{RESET}  Back",
            f"{RED}󰈆{RESET}  Exit"
        ]
        sel = launcher("\n".join(actions), "Select Action")
        sel = re.sub(r'.  ', '', sel)

        if sel == "Exit": byebye()
        if sel in ["Back", ""]: break

        uploader_url = channel.get("uploader_url")
        if sel == "Videos": playlist_explorer(run_yt_dlp(f"{uploader_url}/videos"), f"{uploader_url}/videos")
        elif sel == "Streams": playlist_explorer(run_yt_dlp(f"{uploader_url}/streams"), f"{uploader_url}/streams")
        elif sel == "Playlists": playlists_explorer(f"{uploader_url}/playlists")
        elif sel == "Search":
            os.system('clear')
            term = prompt("Enter term to search for")
            term_enc = urllib.parse.quote(term)
            url = f"{uploader_url}/search?query={term_enc}"
            playlist_explorer(run_yt_dlp(url), url)
        elif sel == "Subscribe":
            sub_file = os.path.join(CLI_CONFIG_DIR, "subscriptions.json")
            if not os.path.exists(sub_file) or os.path.getsize(sub_file) == 0:
                if confirm("Import YouTube subscriptions?"):
                    data = run_yt_dlp("https://www.youtube.com/feed/channels")
                    with open(sub_file, 'w') as f: json.dump(data, f)
                else: data = {"entries": []}
            else:
                with open(sub_file, 'r') as f: data = json.load(f)

            cid = channel.get("id")
            data["entries"] = [e for e in data["entries"] if e.get("id") != cid]
            data["entries"].append(channel)
            with open(sub_file, 'w') as f: json.dump(data, f)
            send_notification("successfully subscribed")
        os.system('clear')

def main_menu(initial_action=None, search_term=None):
    os.system('clear')
    action = initial_action
    if not action:
        options = [
            f"{CYAN}{RESET}  Your Feed", f"{CYAN}{RESET}  Trending", f"{CYAN}󰐑{RESET}  Playlists",
            f"{CYAN}{RESET}  Search", f"{CYAN}{RESET}  Watch Later", f"{CYAN}󰵀{RESET}  Subscription Feed",
            f"{CYAN}󰑈{RESET}  Channels", f"{CYAN}{RESET}  Custom Playlists", f"{CYAN}{RESET}  Liked Videos",
            f"{CYAN}{RESET}  Saved Videos", f"{CYAN}{RESET}  Watch History", f"{CYAN}{RESET}  Recent",
            f"{CYAN}{RESET}  Clips", f"{CYAN}{RESET}  Edit Config", f"{CYAN}{RESET}  Miscellaneous",
            f"{RED}󰈆{RESET}  Exit"
        ]
        sel = launcher("\n".join(options), "Select Action")
        action = re.sub(r'.*  ', '', sel)

    if action == "Exit": byebye()

    if action == "Your Feed": playlist_explorer(run_yt_dlp("https://www.youtube.com"), "https://www.youtube.com")
    elif action == "Trending": playlist_explorer(run_yt_dlp("https://www.youtube.com/feed/trending"), "https://www.youtube.com/feed/trending")
    elif action == "Search":
        os.system('clear')
        if not search_term:
            search_term = prompt("Enter term to search for")
            if re.match(r'^![0-9]{1,2}$', search_term):
                idx = int(search_term[1:])
                hist_file = os.path.join(CLI_CACHE_DIR, "search_history.txt")
                if os.path.exists(hist_file):
                    with open(hist_file) as f: lines = [l.strip() for l in f if l.strip()]
                    if lines and idx <= 10: search_term = lines[-idx]

        if not search_term: return main_menu()

        sp = "EgIQAQ%253D%253D"
        match = re.match(r'^(:[a-z]+)\s+(.+)', search_term)
        if match:
            filter_cmd, search_term = match.groups()
            if filter_cmd == ":hour": sp="EgIIAQ%253D%253D"
            elif filter_cmd == ":today": sp="EgIIAg%253D%253D"
            elif filter_cmd == ":week": sp="EgIIAw%253D%253D"
            elif filter_cmd == ":month": sp="EgIIBA%253D%253D"
            elif filter_cmd == ":year": sp="EgIIBQ%253D%253D"

        if CONFIG["SEARCH_HISTORY"] == "true":
            hist_file = os.path.join(CLI_CACHE_DIR, "search_history.txt")
            lines = []
            if os.path.exists(hist_file):
                with open(hist_file) as f: lines = [l.strip() for l in f if l.strip() and l.strip() != search_term]
            lines.append(search_term)
            with open(hist_file, 'w') as f: f.write("\n".join(lines) + "\n")

        term_enc = urllib.parse.quote(search_term)
        url = f"https://www.youtube.com/results?search_query={term_enc}&sp={sp}"
        playlist_explorer(run_yt_dlp(url), url)

    elif action == "Channels":
        while True:
            sub_file = os.path.join(CLI_CONFIG_DIR, "subscriptions.json")
            if not os.path.exists(sub_file):
                print("Loading subscriptions...")
                data = run_yt_dlp("https://www.youtube.com/feed/channels")
                if data:
                    with open(sub_file, 'w') as f: json.dump(data, f)
            else:
                with open(sub_file) as f: data = json.load(f)

            if not data: break
            channels = [e.get("channel") for e in data.get("entries", [])]
            options = "\n".join(channels) + "\nMain Menu\nExit"
            sel = launcher(options, "Select Channel", "channel")
            if sel == "Exit": byebye()
            if sel == "Main Menu": break
            channel = next((e for e in data["entries"] if e["channel"] == sel), None)
            if channel: channels_explorer(channel)

    elif action == "Edit Config":
        subprocess.run([CONFIG["EDITOR"], os.path.join(CLI_CONFIG_DIR, f"{CLI_NAME}.conf")])
        load_config()

    main_menu()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"Browse youtube from the terminal ({CLI_NAME})")
    parser.add_argument("-S", "--search", help="search for a video")
    parser.add_argument("-e", "--edit-config", action="store_true", help="edit config file")
    parser.add_argument("--rofi-theme", help="path to rofi config")
    parser.add_argument("--disown-streaming-process", action="store_true")
    parser.add_argument("--no-disown-streaming-process", action="store_true")
    parser.add_argument("-s", "--preferred-selector", choices=["fzf", "rofi"])
    parser.add_argument("-p", "--player", choices=["mpv", "vlc"])
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("-E", "--generate-desktop-entry", action="store_true")
    parser.add_argument("-v", "--version", action="store_true")

    args, unknown = parser.parse_known_args()

    if args.version:
        print(f"{CLI_NAME} v{CLI_VERSION} Copyright © 2024 {CLI_AUTHOR} projects")
        sys.exit(0)

    if args.generate_desktop_entry:
        print(f"[Desktop Entry]\nName={CLI_NAME}\nType=Application\nversion={CLI_VERSION}\nPath={os.path.expanduser('~')}\nComment=Browse Youtube from the terminal\nTerminal=false\nIcon={CLI_DIR}/assets/logo.png\nExec={sys.argv[0]} --preferred-selector rofi\nCategories=Education")
        sys.exit(0)

    load_config()

    if args.preferred_selector: CONFIG["PREFERRED_SELECTOR"] = args.preferred_selector
    if args.player: CONFIG["PLAYER"] = args.player
    if args.preview: CONFIG["ENABLE_PREVIEW"] = "true"
    if args.no_preview: CONFIG["ENABLE_PREVIEW"] = "false"
    if args.rofi_theme: CONFIG["ROFI_THEME"] = args.rofi_theme
    if args.disown_streaming_process: CONFIG["DISOWN_STREAMING_PROCESS"] = "true"
    if args.no_disown_streaming_process: CONFIG["DISOWN_STREAMING_PROCESS"] = "false"

    if args.edit_config:
        subprocess.run([CONFIG["EDITOR"], os.path.join(CLI_CONFIG_DIR, f"{CLI_NAME}.conf")])
        sys.exit(0)

    for dep in ["yt-dlp", "fzf", "jq"]:
        if not shutil.which(dep):
            print(f"{dep} is not installed and is a core dep please install it to proceed")
            sys.exit(1)

    if CONFIG["WELCOME_SCREEN"] == "true":
        ts_file = os.path.join(CLI_CACHE_DIR, ".last_welcome")
        last = 0
        if os.path.exists(ts_file):
            try: last = int(open(ts_file).read().strip())
            except: pass

        if time.time() - last > 86400:
            print(f"{CYAN}How are you {os.environ.get('USER', 'User')} 🙂?\nIf you like the project consider supporting at {CLI_SUPPORT_PROJECT_URL}.{RESET}")
            if confirm("Open support page?"):
                subprocess.run(["xdg-open", CLI_SUPPORT_PROJECT_URL])
            with open(ts_file, 'w') as f: f.write(str(int(time.time())))

    try:
        if args.search: main_menu(initial_action="Search", search_term=args.search)
        else: main_menu()
    except KeyboardInterrupt:
        byebye()
