# Added by ForgeCode installer
case ":$PATH:" in
*":/home/user/.local/bin:"*) ;;
*) export PATH="/home/user/.local/bin:$PATH" ;;
esac
#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# Auto-cd into directories
shopt -s autocd
shopt -s extglob
shopt -s globstar
shopt -s nullglob

# Suppress autocd output (cd -- dir/)
exec {BASH_XTRACEFD}>/dev/null

# History search: up/down arrows cycle through history matching typed text
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# History settings
HISTSIZE=10000
HISTFILESIZE=10000
export HISTCONTROL=erasedups

# Ctrl+Backspace deletes backward (multiple common sequences)
bind '"\C-H": backward-kill-word'
bind '"\e[3;5~": backward-kill-word'
bind '"\e\C-?": backward-kill-word'
bind '"\e\C-H": backward-kill-word'

# Ctrl+Delete deletes forward
bind '"\e[3;2~": kill-word'
bind '"\e[3;5~": kill-word'

alias ls='eza -al --color=always --group-directories-first --icons always'
alias la='eza -a --color=always --group-directories-first --icons always'
alias ll='eza -l --color=always --group-directories-first --icons always'
alias lt='eza -aT --color=always --group-directories-first --icons always'
alias l.="eza -a | grep -e '^\.'"

alias grubup="sudo grub-mkconfig -o /boot/grub/grub.cfg"
alias fixpacman="sudo rm /var/lib/pacman/db.lck"
alias tarnow='tar -acf '
alias untar='tar -zxvf '
alias wget='wget -c '
# alias psmem='ps auxf | sort -nr -k 4'
# alias psmem10='ps auxf | sort -nr -k 4 | head -10'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias ......='cd ../../../../..'
# alias dir='dir --color=auto'
# alias vdir='vdir --color=auto'
# alias grep='grep --color=auto'
# alias fgrep='fgrep --color=auto'
# alias egrep='egrep --color=auto'
# alias hw='hwinfo --short'
alias big="expac -H M '%m\t%n' | sort -h | nl"
alias gitpkg='pacman -Q | grep -i "\-git" | wc -l'
alias update='sudo pacman -Syyu'
alias sync='sudo pacman -Sy'
alias info='pacman -Sii'
alias install='sudo pacman -S'
alias remove='sudo pacman -Rcsn'
alias search='pacman -Ss'
alias check='pacman -Qs'
alias cwm='nvim /opt/dwm-source/config.def.h'
alias mwm='cd /opt/dwm-source/; sudo make clean install; cd'
alias sc='sudo ./cleaner.sh'
alias pss='paru -Ss'
alias pis='paru -S'
alias paur='yay -Syua'
alias pkg='paru -Gp'
# alias tb='nc termbin.com 9999'
# alias cleanup='sudo pacman -Rcsn $(pacman -Qtdq)'
alias clean='sudo paccache -rk0'
# alias jctl="journalctl -p 3 -xb"
alias rip="expac --timefmt='%Y-%m-%d %T' '%l\t%n %v' | sort | tail -200 | nl"

# Search functions
pe() {
  sudo plocate -br "^$1$" "${@:2}"
}

pa() {
  sudo plocate -b "$1" "${@:2}"
}

plrm() {
  if [[ -z ${1:-} ]]; then
    echo "Usage: plrm <filename> [plocate-opts...]" >&2
    return 1
  fi
  local needle=$1
  shift

  local matches
  mapfile -t matches < <(sudo plocate -br "^${needle}$" "$@")

  if ((${#matches[@]} == 0)); then
    echo "No matches found for: $needle"
    return 1
  fi

  printf 'Matches:\n'
  printf '  %s\n' "${matches[@]}"

  local answer
  read -r -p "Run sudo rm -rf on these results? [y/N] " answer
  [[ $answer == [yY] || $answer == [yY][eE][sS] ]] || return 0

  printf '%s\0' "${matches[@]}" | xargs -0 sudo rm -rf --
}

flrm() {
  if [[ -z ${1:-} ]]; then
    echo "Usage: flrm <filename> [fd-opts...]" >&2
    return 1
  fi
  local needle=$1
  shift

  local matches
  mapfile -t matches < <(sudo fd -u "^${needle}$" "$@")

  if ((${#matches[@]} == 0)); then
    echo "No matches found for: $needle"
    return 1
  fi

  printf 'Matches:\n'
  printf '  %s\n' "${matches[@]}"

  local answer
  read -r -p "Run sudo rm -rf on these results? [y/N] " answer
  [[ $answer == [yY] || $answer == [yY][eE][sS] ]] || return 0

  sudo fd -u "^${needle}$" "$@" -X sudo rm -rf {}
}

fa() {
  sudo fd -u "$1" "${@:2}"
}

fe() {
  sudo fd -u "^$1$" "${@:2}"
}

# # Git-aware prompt with nerd symbols
# __git_prompt() {
#   local branch=$(git symbolic-ref --short HEAD 2>/dev/null)
#   if [ -n "$branch" ]; then
#     local dirty=$(git diff --quiet 2>/dev/null || echo " 󰦷 ")
#     printf " \e[1;36m\e[0m \e[1;33m%s%s" "$branch" "$dirty"
#   fi
# }

# PS1='\[\e[1;31m\]\u\[\e[38;5;120m\]@\[\e[1;34m\]\h\[\e[0m\] \[\e[1;35m\] \[\e[38;5;79m\]\w\[\e[33m\]$(__git_prompt)\[\e[0m\]\n\[\e[38;5;120m\]❯\[\e[0m\] '

__git_prompt() {
  local branch=$(git symbolic-ref --short HEAD 2>/dev/null)
  if [ -n "$branch" ]; then
    local dirty=$(git diff --quiet 2>/dev/null || echo " 󰦷 ")
    # Cyan (00FFFF) for branch icon, Yellow (FFFF00) for branch name
    printf " \e[38;2;0;255;255m\e[0m \e[38;2;255;255;0m%s%s" "$branch" "$dirty"
  fi
}

# Prompt with 24-bit true color (RGB) escape sequences
# Prompt with 24-bit true color (RGB) escape sequences
# Format: \e[38;2;R;G;Bm for foreground, \e[48;2;R;G;Bm for background
# Hex values converted to decimal:
# Orange (FF8C00) -> 255,140,0
# Light Violet (C8A2FF) -> 200,162,255
# Teal (00CED1) -> 0,206,209
# White (FFFFFF) -> 255,255,255
# Green (5FFF5F) -> 95,255,95
# Yellow (FFFF00) -> 255,255,0
# Cyan (5FD7FF) -> 95,215,255

PS1='\[\e[38;2;255;140;0m\]\u\[\e[38;2;200;162;255m\]@\[\e[38;2;0;206;209m\]\h\[\e[0m\] \[\e[38;2;255;255;255m\] \[\e[38;2;95;255;95m\]\w\[\e[0m\]$(__git_prompt)\n\[\e[38;2;95;215;255m\]❯\[\e[0m\] '

export FZF_CTRL_R_OPTS="--exact --no-sort --height=11 --style=minimal --reverse"
eval "$(fzf --bash)"
# eval "$(atuin init bash --disable-up-arrow)"
