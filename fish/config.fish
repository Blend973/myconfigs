## Source from conf.d before our fish config
source /home/user/.config/fish/done.fish

set fish_greeting ""
## Set values
## Run fastfetch as welcome message
#function fish_greeting
#   fastfetch
#end

# Format man pages
set -x MANROFFOPT -c
set -x MANPAGER "sh -c 'col -bx | bat -l man -p'"

# Set settings for https://github.com/franciscolourenco/done
set -U __done_min_cmd_duration 10000
set -U __done_notification_urgency_level low

## Environment setup
# Apply .profile: use this to put fish compatible .profile stuff in
if test -f ~/.fish_profile
    source ~/.fish_profile
end

# Add ~/.local/bin to PATH
if test -d ~/.local/bin
    if not contains -- ~/.local/bin $PATH
        set -p PATH ~/.local/bin
    end
end

# Add depot_tools to PATH
if test -d ~/Applications/depot_tools
    if not contains -- ~/Applications/depot_tools $PATH
        set -p PATH ~/Applications/depot_tools
    end
end

## Functions
# Functions needed for !! and !$ https://github.com/oh-my-fish/plugin-bang-bang
function __history_previous_command
    switch (commandline -t)
        case "!"
            commandline -t $history[1]
            commandline -f repaint
        case "*"
            commandline -i !
    end
end

function __history_previous_command_arguments
    switch (commandline -t)
        case "!"
            commandline -t ""
            commandline -f history-token-search-backward
        case "*"
            commandline -i '$'
    end
end

if [ "$fish_key_bindings" = fish_vi_key_bindings ]

    bind -Minsert ! __history_previous_command
    bind -Minsert '$' __history_previous_command_arguments
else
    bind ! __history_previous_command
    bind '$' __history_previous_command_arguments
end

# Fish command history
function history
    builtin history --show-time='%F %T '
end

function backup --argument filename
    cp $filename $filename.bak
end

# Copy DIR1 DIR2
function copy
    set count (count $argv | tr -d \n)
    if test "$count" = 2; and test -d "$argv[1]"
        set from (echo $argv[1] | trim-right /)
        set to (echo $argv[2])
        command cp -r $from $to
    else
        command cp $argv
    end
end

## Useful aliases
# Replace ls with eza
alias ls='eza -al --color=always --group-directories-first --icons' # preferred listing
alias la='eza -a --color=always --group-directories-first --icons' # all files and dirs
alias ll='eza -l --color=always --group-directories-first --icons' # long format
alias lt='eza -aT --color=always --group-directories-first --icons' # tree listing
alias l.="eza -a | grep -e '^\.'" # show only dotfiles

# Common use
alias grubup="sudo grub-mkconfig -o /boot/grub/grub.cfg"
alias fixpacman="sudo rm /var/lib/pacman/db.lck"
alias tarnow='tar -acf '
alias untar='tar -zxvf '
alias wget='wget -c '
alias psmem='ps auxf | sort -nr -k 4'
alias psmem10='ps auxf | sort -nr -k 4 | head -10'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias ......='cd ../../../../..'
alias dir='dir --color=auto'
alias vdir='vdir --color=auto'
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
alias hw='hwinfo --short' # Hardware Info
alias big="expac -H M '%m\t%n' | sort -h | nl" # Sort installed packages according to size in MB
alias gitpkg='pacman -Q | grep -i "\-git" | wc -l' # List amount of -git packages
alias update='sudo pacman -Syu'
alias sync='sudo pacman -Sy'
alias install='sudo pacman -S'
alias remove='sudo pacman -Rcsn'
alias search='pacman -Ss'
alias check='pacman -Qs'
alias ym='ytf -a -p'
alias cwm='sudo nvim /opt/dwm-source/config.def.h'
alias mwm='cd /opt/dwm-source/; sudo make clean install; cd'
alias sc='sudo ./cleaner.sh'

# Get fastest mirrors
alias mirror="sudo cachyos-rate-mirrors"

# Help people new to Arch
alias apt='man pacman'
alias apt-get='man pacman'
alias please='sudo'
alias tb='nc termbin.com 9999'

# Cleanup orphaned packages
alias cleanup='sudo pacman -Rcsn (pacman -Qtdq)'

# Get the error messages from journalctl
alias jctl="journalctl -p 3 -xb"

# Recent installed packages
alias rip="expac --timefmt='%Y-%m-%d %T' '%l\t%n %v' | sort | tail -200 | nl"
# export OPENAI_API_KEY="csk-8rd56dded4mtkh48th3c5j9e8538mypk8rvtfj362w8jtrdx"
# export OPENAI_BASE_URL="https://api.cerebras.ai/v1"
# export OPENAI_MODEL="zai-glm-4.6"
#function ytf
#    yt-dlp --flat-playlist -j "ytsearch50:$argv" \
#        | jq -r '"\(.title) — \(.url)"' \
#        | fzf --height=40% --reverse \
#        | awk -F ' — ' '{print $2}' \
#        | xargs -I{} mpv --ytdl-format="bestvideo[height<=720]+bestaudio/best[height<=720]" "{}"
#end
#function ytf
#    yt-dlp --flat-playlist -j "ytsearch50:$argv" \
#        | jq -r '"\(.title) — \(.url)"' \
#        | fzf --reverse \
#        | awk -F ' — ' '{print $2}' \
#        | xargs -I{} mpv --ytdl-format="bestvideo[height<=720]+bestaudio/best[height<=720]" "{}"
#end
#function fa
#    sudo fd -u $argv /
#end
#
#function fb
#    set search_pattern "^$argv\$"
#    sudo fd -u $search_pattern /
#end
function pe
    set search_pattern "^$argv\$"
    sudo plocate --regexp --basename "$search_pattern"
end
function pa
    sudo plocate --regexp --basename "$argv"
end
zoxide init fish | source
source /home/user/yt.sh
