#!/usr/bin/env python3
# Optimized YT-Browser
# Features: Search, Preview, Audio-Only, Autoplay, Configurable.

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
CLI_VERSION = "0.5.0"
CLI_DIR = os.path.dirname(os.path.realpath(__file__))

# XDG Base Directory specification
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache"))
XDG_VIDEOS_DIR = os.environ.get("XDG_VIDEOS_DIR", os.path.join(os.path.expanduser("~"), "Videos"))

CLI_CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, CLI_NAME)
CLI_CACHE_DIR = os.path.join(XDG_CACHE_HOME, CLI_NAME)
CLI_PREVIEW_IMAGES_CACHE_DIR = os.path.join(CLI_CACHE_DIR, "preview_images")
CLI_PREVIEW_SCRIPTS_DIR = os.path.join(CLI_CACHE_DIR, "preview_text")
CLI_HELPER_SCRIPT = os.path.join(CLI_CONFIG_DIR, "yt-x-helper.sh")
CLI_PREVIEW_DISPATCHER = os.path.join(CLI_CONFIG_DIR, "yt-x-preview.sh")

# Ensure directories exist
for d in [CLI_CONFIG_DIR, CLI_PREVIEW_IMAGES_CACHE_DIR, CLI_PREVIEW_SCRIPTS_DIR]:
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
    "EDITOR": os.environ.get("EDITOR", "nano"),
    "PREFERRED_SELECTOR": "fzf",
    "VIDEO_QUALITY": "1080",
    "ENABLE_PREVIEW": "false",
    "PLAYER": "mpv",
    "PREFERRED_BROWSER": "",
    "NO_OF_SEARCH_RESULTS": "30",
    "NOTIFICATION_DURATION": "5",
    "SEARCH_HISTORY": "true",
    "DOWNLOAD_DIRECTORY": os.path.join(XDG_VIDEOS_DIR, CLI_NAME),
}

# Global State
PLAYLIST_START = 1
PLAYLIST_END = 30
CURRENT_TIME = int(time.time())
AUDIO_ONLY_MODE = False
AUTOPLAY_MODE = False

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
    if text is None: text = ""
    if isinstance(text, str): text = text.encode('utf-8')
    return hashlib.sha256(text).hexdigest()

def send_notification(message):
    sys.stderr.write(f"{message}\n")
    time.sleep(int(CONFIG["NOTIFICATION_DURATION"]))

def byebye(code=0):
    os.system('clear')
    print(f"Have a good day")
    sys.exit(code)

def cleanup_cache():
    """Removes preview images older than 24 hours."""
    try:
        now = time.time()
        cutoff = now - 86400 
        for d in [CLI_PREVIEW_IMAGES_CACHE_DIR, CLI_PREVIEW_SCRIPTS_DIR]:
            for filename in os.listdir(d):
                filepath = os.path.join(d, filename)
                if os.path.isfile(filepath):
                    if os.path.getmtime(filepath) < cutoff:
                        os.remove(filepath)
    except Exception: pass

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
    # 1. Helper Functions Script
    helper_content = f"""#!/usr/bin/env bash
export CLI_PREVIEW_IMAGES_CACHE_DIR="{CLI_PREVIEW_IMAGES_CACHE_DIR}"
export CLI_PREVIEW_SCRIPTS_DIR="{CLI_PREVIEW_SCRIPTS_DIR}"
export IMAGE_RENDERER="{CONFIG['IMAGE_RENDERER']}"
export PLATFORM="{PLATFORM}"

generate_sha256() {{
  local input
  if [ -n "$1" ]; then input="$1"; else input=$(cat); fi
  if command -v sha256sum &>/dev/null; then echo -n "$input" | sha256sum | awk '{{print $1}}'
  elif command -v shasum &>/dev/null; then echo -n "$input" | shasum -a 256 | awk '{{print $1}}'
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
    chafa -s "$dim" "$file"; echo
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
    preview_content = f"""#!/usr/bin/env bash
source "{CLI_HELPER_SCRIPT}"
MODE="$1"; shift; SELECTION="$*"
MAGENTA='\\x1b[38;2;215;0;95m'; BOLD=$(tput bold); RESET=$(tput sgr0)

if [ "$MODE" = "video" ]; then
  title="$SELECTION"
  id=$(echo "$title" | sed -E 's/^[0-9]+ //g' | generate_sha256)
  if [ -f "{CLI_PREVIEW_SCRIPTS_DIR}/${{id}}.txt" ]; then
    . "{CLI_PREVIEW_SCRIPTS_DIR}/${{id}}.txt"
  else
    echo "Loading Preview..."
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
            f.write(f"PRETTY_PRINT: true\nEDITOR: {os.environ.get('EDITOR', 'nano')}\nPREFERRED_SELECTOR: fzf\n")

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
    cleanup_cache()

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

def prompt(text, value=""):
    history_file = os.path.join(CLI_CACHE_DIR, "search_history.txt")
    history_text = ""
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                lines = [l.strip() for l in f if l.strip()]
            lines = lines[-10:]
            lines.reverse()
            history_formatted = "\n".join([f"{i+1}. {l}" for i, l in enumerate(lines)])
            history_text = f"Search history:\n{history_formatted}\n(Enter !<n> to select from history. Example: !1)\n"
        except Exception: pass

    if CONFIG["PREFERRED_SELECTOR"] == "rofi":
        cmd = ["rofi", "-dmenu", "-p", f"{text}: "]
        if CONFIG["SEARCH_HISTORY"] == "true" and history_text:
             cmd.extend(["-mesg", history_text])
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate(input="")
        return out.strip()
    elif shutil.which("gum"):
        header = CLI_HEADER
        if CONFIG["SEARCH_HISTORY"] == "true" and history_text: header += "\n" + history_text
        cmd = ["gum", "input", "--header", header, "--prompt", f"{text}: ", "--value", value]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return proc.stdout.strip()
    else:
        sys.stderr.write(f"{CLI_HEADER}\n")
        if CONFIG["SEARCH_HISTORY"] == "true" and history_text: sys.stderr.write(f"{history_text}\n")
        sys.stderr.write(f"{text}: ")
        sys.stderr.flush()
        try: return input().strip()
        except EOFError: return ""

def launcher(options_str, prompt_text, preview_mode=None):
    selector = CONFIG["PREFERRED_SELECTOR"].lower()
    if selector == "rofi":
        cmd = ["rofi", "-sort", "-matching", "fuzzy", "-dmenu", "-i", "-p", "", "-mesg", prompt_text, "-matching", "fuzzy", "-sorting-method", "fzf"]
        if CONFIG["ROFI_THEME"]: cmd[1:1] = ["-no-config", "-theme", CONFIG["ROFI_THEME"]]
        else: cmd.extend(["-width", "1500"])
        clean_options = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', options_str)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate(input=clean_options)
        res = out.strip()
        return res if res else "Exit"
    else: # fzf
        cmd = ["fzf", "--info=hidden", "--layout=reverse", "--height=100%", f"--prompt={prompt_text}: ",
            "--header-first", f"--header={CLI_HEADER}", "--exact", "--cycle", "--ansi"]
        if preview_mode:
            cmd.extend(["--preview-window=left,35%,wrap", "--bind=right:accept", "--expect=shift-left,shift-right",
                "--tabstop=1", f"--preview=bash '{CLI_PREVIEW_DISPATCHER}' '{preview_mode}' {{}}"])
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate(input=options_str)
        lines = out.splitlines()
        if not lines: return ""
        if preview_mode and len(lines) >= 2: return lines[1]
        return lines[0]

def run_yt_dlp(url, extra_args=None):
    cmd = ["yt-dlp", url, "-J", "--flat-playlist", "--extractor-args", "youtubetab:approximate_date",
           "--playlist-start", str(PLAYLIST_START), "--playlist-end", str(PLAYLIST_END)]
    if CONFIG["PREFERRED_BROWSER"]: cmd.extend(shlex.split(CONFIG["PREFERRED_BROWSER"]))
    if extra_args: cmd.extend(extra_args)

    if shutil.which("gum"):
        spin_cmd = ["gum", "spin", "--show-output", "--"] + cmd
        proc = subprocess.run(spin_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    else:
        sys.stderr.write("Loading...\n")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if proc.returncode != 0:
        send_notification("Failed to fetch data : (")
        return None
    try: return json.loads(proc.stdout)
    except json.JSONDecodeError: return None

# ==========================================
# PREVIEW GENERATION
# ==========================================

def generate_text_preview(data):
    if not data or "entries" not in data: return
    for i, video in enumerate(data["entries"]):
        if not video: continue
        raw_title = video.get("title", "")
        clean_title = re.sub(r'^[0-9]+ ', '', raw_title)
        filename_hash = generate_sha256(clean_title)
        safe_title = shlex.quote(clean_title)
        
        thumbs = video.get("thumbnails", [])
        thumb_url = thumbs[-1]["url"] if thumbs else ""
        preview_image_hash = generate_sha256(thumb_url)

        vc = video.get("view_count")
        view_count = "{:,}".format(int(vc)) if vc is not None else "Unknown"
        ls = video.get("live_status")
        live_status = "Online" if ls == "is_live" else ("Offline" if ls == "was_live" else "False")
        safe_description = shlex.quote(video.get("description") or "null")
        safe_channel = shlex.quote(video.get("channel", ""))

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
echo {safe_title}
ll=1
while [ $ll -le $FZF_PREVIEW_COLUMNS ];do echo -n -e "─" ;(( ll++ ));done;
printf "${{MAGENTA}}${{BOLD}}Channel: ${{RESET}}{safe_channel}\\n";
printf "${{MAGENTA}}${{BOLD}}Duration: ${{RESET}}{duration_str}\\n";
printf "${{MAGENTA}}${{BOLD}}View Count: ${{RESET}}{view_count} views\\n";
printf "${{MAGENTA}}${{BOLD}}Live Status: ${{RESET}}{live_status}\\n";
printf "${{MAGENTA}}${{BOLD}}Uploaded: ${{RESET}}{timestamp_str}\\n";
ll=1
while [ $ll -le $FZF_PREVIEW_COLUMNS ];do echo -n -e "─" ;(( ll++ ));done;
echo
! [ {safe_description} = "null" ] && echo -n {safe_description};
"""
        with open(os.path.join(CLI_PREVIEW_SCRIPTS_DIR, f"{filename_hash}.txt"), "w") as f: f.write(content)

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

def playlist_explorer(search_results, url):
    global PLAYLIST_START, PLAYLIST_END, AUDIO_ONLY_MODE, AUTOPLAY_MODE
    download_images = False

    while True:
        if not search_results or "entries" not in search_results: break
        entries = search_results.get("entries", [])
        titles = []
        
        if not download_images:
            for i, entry in enumerate(entries):
                if not entry: continue
                num = str(i + 1)
                if len(entries) < 10 and len(num) < 2: num = "0" + num
                entry["title"] = f"{num} {entry.get('title', '')}"
                titles.append(entry["title"])
        else:
            for entry in entries:
                if entry: titles.append(entry.get("title", ""))

        if CONFIG["ENABLE_PREVIEW"] == "true" and CONFIG["PREFERRED_SELECTOR"] == "fzf" and not download_images:
            download_preview_images(search_results)
            download_images = True

        if CONFIG["ENABLE_PREVIEW"] == "true":
            options_str = "\n".join(titles) + f"\nNext\nPrevious\n{CYAN}󰌍{RESET}  Back\n{RED}󰈆{RESET}  Exit"
            selection = launcher(options_str, "select video", "video")
        else:
            options_str = "\n".join(titles + ["Next", "Previous", "Back", "Exit"])
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
            min_end = int(CONFIG["NO_OF_SEARCH_RESULTS"])
            if PLAYLIST_END < min_end: PLAYLIST_END = min_end
            search_results = run_yt_dlp(url)
            download_images = False
            continue
        elif selection in ["Back", "", "Exit"]:
            if selection == "Exit": byebye()
            break

        try:
            sel_id = int(selection.split(' ')[0])
            current_index = sel_id - 1
            video = entries[current_index]
            clean_title = re.sub(r'^[0-9]+ ', '', video['title'])
        except (ValueError, IndexError): continue

        while True:
            audio_state = f"{CYAN}[x]{RESET}" if AUDIO_ONLY_MODE else "[ ]"
            autoplay_state = f"{CYAN}[x]{RESET}" if AUTOPLAY_MODE else "[ ]"
            
            media_actions = [
                f"{CYAN}{RESET}  Watch",
                f"{CYAN}󰎆{RESET}  Toggle Audio Only {audio_state}",
                f"{CYAN}{RESET}  Toggle Autoplay {autoplay_state}",
                f"{CYAN}󱑤{RESET}  Download",
                f"{CYAN}󰌍{RESET}  Back", f"{RED}󰈆{RESET}  Exit"
            ]

            action_sel = launcher("\n".join(media_actions), "Select Media Action")
            action_sel = re.sub(r'.  ', '', action_sel)
            os.system('clear')

            if action_sel == "Exit": byebye()
            if action_sel in ["Back", ""]: break

            if "Toggle Audio Only" in action_sel:
                AUDIO_ONLY_MODE = not AUDIO_ONLY_MODE
                continue
            
            if "Toggle Autoplay" in action_sel:
                AUTOPLAY_MODE = not AUTOPLAY_MODE
                continue

            vid_url = video.get("url")

            if action_sel == "Watch":
                # Autoplay Loop
                while True:
                    print(f"{MAGENTA}Now playing:{RESET} {clean_title}")
                    
                    # Determine Player Arguments
                    player_cmd = [CONFIG["PLAYER"], vid_url]
                    if CONFIG["PLAYER"] == "mpv":
                        if AUDIO_ONLY_MODE: player_cmd.extend(["--no-video", "--force-window=no"])
                    elif CONFIG["PLAYER"] == "vlc":
                        player_cmd.extend(["--video-title", clean_title])
                        if AUDIO_ONLY_MODE: player_cmd.append("--no-video")

                    # Play (Blocking if Autoplay is on, Non-blocking if off)
                    if AUTOPLAY_MODE:
                        subprocess.run(player_cmd)
                        
                        # Prepare next video
                        current_index += 1
                        if current_index >= len(entries):
                            print("End of current list. Fetching next page...")
                            PLAYLIST_START += int(CONFIG["NO_OF_SEARCH_RESULTS"])
                            PLAYLIST_END += int(CONFIG["NO_OF_SEARCH_RESULTS"])
                            search_results = run_yt_dlp(url)
                            if not search_results or "entries" not in search_results: break
                            entries = search_results.get("entries", [])
                            current_index = 0
                            download_images = False # Reset for next page
                        
                        if current_index < len(entries):
                            video = entries[current_index]
                            vid_url = video.get("url")
                            clean_title = re.sub(r'^[0-9]+ ', '', video.get("title", "Unknown"))
                        else:
                            break
                    else:
                        subprocess.Popen(player_cmd, start_new_session=True)
                        break

            elif action_sel == "Download":
                folder = "audio" if AUDIO_ONLY_MODE else "videos"
                ext_args = ["-x", "-f", "bestaudio", "--audio-format", "mp3"] if AUDIO_ONLY_MODE else []
                out_tmpl = os.path.join(CONFIG["DOWNLOAD_DIRECTORY"], f"{folder}/individual/%(channel)s/%(title)s.%(ext)s")
                
                cmd = ["yt-dlp", vid_url, "--output", out_tmpl] + ext_args
                if CONFIG["PREFERRED_BROWSER"]: cmd.extend(shlex.split(CONFIG["PREFERRED_BROWSER"]))
                
                subprocess.Popen(cmd, start_new_session=True)
                send_notification(f"Started downloading {clean_title}")

    PLAYLIST_START = 1
    PLAYLIST_END = int(CONFIG["NO_OF_SEARCH_RESULTS"])

def main_menu(initial_action=None, search_term=None):
    os.system('clear')
    action = initial_action
    if not action:
        options = [
            f"{CYAN}{RESET}  Search",
            f"{CYAN}{RESET}  Edit Config",
            f"{RED}󰈆{RESET}  Exit"
        ]
        sel = launcher("\n".join(options), "Select Action")
        action = re.sub(r'.*  ', '', sel)

    if action == "Exit": byebye()

    elif action == "Search":
        os.system('clear')
        if not search_term:
            search_term = prompt("Enter term to search for")
            if re.match(r'^![0-9]{1,2}$', search_term):
                idx = int(search_term[1:])
                hist_file = os.path.join(CLI_CACHE_DIR, "search_history.txt")
                if os.path.exists(hist_file):
                    try:
                        with open(hist_file) as f: lines = [l.strip() for l in f if l.strip()]
                        if lines and idx <= 10: search_term = lines[-idx]
                    except Exception: pass

        if not search_term: return main_menu()

        sp = "EgIQAQ%253D%253D" # Default video
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
                try:
                    with open(hist_file) as f: lines = [l.strip() for l in f if l.strip() and l.strip() != search_term]
                except Exception: pass
            lines.append(search_term)
            with open(hist_file, 'w') as f: f.write("\n".join(lines) + "\n")

        term_enc = urllib.parse.quote(search_term)
        url = f"https://www.youtube.com/results?search_query={term_enc}&sp={sp}"
        playlist_explorer(run_yt_dlp(url), url)

    elif action == "Edit Config":
        subprocess.run([CONFIG["EDITOR"], os.path.join(CLI_CONFIG_DIR, f"{CLI_NAME}.conf")])
        load_config()

    main_menu()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"Browse youtube from the terminal ({CLI_NAME})")
    parser.add_argument("-S", "--search", help="search for a video")
    parser.add_argument("-e", "--edit-config", action="store_true", help="edit config file")
    parser.add_argument("-v", "--version", action="store_true")
    args, unknown = parser.parse_known_args()

    if args.version:
        print(f"{CLI_NAME} v{CLI_VERSION}")
        sys.exit(0)

    load_config()

    if args.edit_config:
        subprocess.run([CONFIG["EDITOR"], os.path.join(CLI_CONFIG_DIR, f"{CLI_NAME}.conf")])
        sys.exit(0)

    for dep in ["yt-dlp", "fzf", "jq"]:
        if not shutil.which(dep):
            print(f"{dep} is not installed and is a core dep please install it to proceed")
            sys.exit(1)

    try:
        if args.search: main_menu(initial_action="Search", search_term=args.search)
        else: main_menu()
    except KeyboardInterrupt:
        byebye()
