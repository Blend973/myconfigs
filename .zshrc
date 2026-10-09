case ":$PATH:" in
*":/home/user/.local/bin:"*) ;;
*) export PATH="/home/user/.local/bin:$PATH" ;;
esac

setopt autocd              # change directory just by typing its name (bash: shopt -s autocd)
setopt extendedglob        # ~ bash extglob
setopt interactivecomments # allow comments in interactive mode
setopt magicequalsubst     # enable filename expansion for arguments of the form ‘anything=expression’
setopt nonomatch           # hide error message if there is no match for the pattern (bash uses nullglob instead)
# setopt notify              # report the status of background jobs immediately
# setopt numericglobsort     # sort filenames numerically when it makes sense
setopt promptsubst         # enable command substitution in prompt

WORDCHARS='_-' # Don't consider certain characters part of the word

# configure key keybindings (KEPT VERBATIM from Kali)
bindkey -e                                        # emacs key bindings
bindkey ' ' magic-space                           # do history expansion on space
bindkey '^U' backward-kill-line                   # ctrl + U
bindkey '^[[3;5~' kill-word                       # ctrl + Supr
bindkey '^[[3~' delete-char                       # delete
bindkey '^[[3;6~' kill-whole-line                 # for xterm
bindkey '^H' kill-whole-line                      # other terms
bindkey '^[[127;6u' kill-whole-line               # ctrl+shift+bksp (kitty CSI-u)
bindkey '^[[1;5C' forward-word                    # ctrl + ->
bindkey '^[[1;5D' backward-word                   # ctrl + <-
bindkey '^[[5~' beginning-of-buffer-or-history    # page up
bindkey '^[[6~' end-of-buffer-or-history          # page down
bindkey '^[[H' beginning-of-line                  # home
bindkey '^[[1~' beginning-of-line                 # home alt
bindkey '^[OH' beginning-of-line                  # home app-mode
bindkey '^[[F' end-of-line                        # end
bindkey '^[[4~' end-of-line                       # end - cat ^[[4~
bindkey '^[OF' end-of-line                        # end app-mode
bindkey '^[[Z' undo                               # shift + tab undo last action
bindkey "^[[A" history-beginning-search-backward # up - bash-like prefix search, cursor stays
bindkey "^[OA" history-beginning-search-backward # up app-mode
bindkey "^[[B" history-beginning-search-forward  # down, cursor stays
bindkey "^[OB" history-beginning-search-forward  # down app-mode

# enable completion features
autoload -Uz compinit
compinit -d ~/.cache/zcompdump
zstyle ':completion:*:*:*:*:*' menu select
zstyle ':completion:*' auto-description 'specify: %d'
zstyle ':completion:*' completer _expand _complete
zstyle ':completion:*' format 'Completing %d'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' list-prompt %SAt %p: Hit TAB for more, or the character to insert%s
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
zstyle ':completion:*' rehash true
zstyle ':completion:*' select-prompt %SScrolling active: current selection at %p%s
zstyle ':completion:*' use-compctl false
zstyle ':completion:*' verbose true
zstyle ':completion:*:kill:*' command 'ps -u $USER -o pid,%cpu,tty,cputime,cmd'

# History
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt hist_expire_dups_first # delete duplicates first when trimming, like bash
setopt hist_ignore_dups       # ignore dup of previous event
setopt hist_ignore_all_dups   # bash erasedups: remove older dup when new one added
setopt hist_save_no_dups      # don't write duplicates to file
setopt hist_find_no_dups      # don't show duplicates when searching
setopt hist_reduce_blanks     # trim superfluous blanks
setopt hist_ignore_space      # ignore commands that start with space
setopt hist_verify            # show expanded history before running
#setopt share_history         # share command history data

# enable syntax-highlighting - Dracula theme (https://draculatheme.com/zsh-syntax-highlighting)
# Dracula Theme (for zsh-syntax-highlighting)
#
# https://github.com/zenorocha/dracula-theme
#
# Copyright 2021, All rights reserved
#
# Code licensed under the MIT license
# http://zenorocha.mit-license.org
#
# @author George Pickering <@bigpick>
# @author Zeno Rocha <hi@zenorocha.com>
# Paste this files contents inside your ~/.zshrc before you activate zsh-syntax-highlighting
ZSH_HIGHLIGHT_HIGHLIGHTERS=(main)
typeset -gA ZSH_HIGHLIGHT_STYLES
# Default groupings per, https://spec.draculatheme.com, try to logically separate
# possible ZSH_HIGHLIGHT_STYLES settings accordingly...?
#
# Italics not yet supported by zsh; potentially soon:
#    https://github.com/zsh-users/zsh-syntax-highlighting/issues/432
#    https://www.zsh.org/mla/workers/2021/msg00678.html
# ... in hopes that they will, labelling accordingly with ,italic where appropriate
#
# Main highlighter styling: https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/docs/highlighters/main.md
#
## General
### Diffs
### Markup
## Classes
## Comments
ZSH_HIGHLIGHT_STYLES[comment]='fg=#6272A4'
## Constants
## Entitites
## Functions/methods
ZSH_HIGHLIGHT_STYLES[alias]='fg=#50FA7B'
ZSH_HIGHLIGHT_STYLES[suffix-alias]='fg=#50FA7B'
ZSH_HIGHLIGHT_STYLES[global-alias]='fg=#50FA7B'
ZSH_HIGHLIGHT_STYLES[function]='fg=#50FA7B'
ZSH_HIGHLIGHT_STYLES[command]='fg=#FFB86C'
ZSH_HIGHLIGHT_STYLES[precommand]='fg=#50FA7B,italic'
ZSH_HIGHLIGHT_STYLES[autodirectory]='fg=#FFB86C,italic'
ZSH_HIGHLIGHT_STYLES[single-hyphen-option]='fg=#FFB86C'
ZSH_HIGHLIGHT_STYLES[double-hyphen-option]='fg=#FFB86C'
ZSH_HIGHLIGHT_STYLES[back-quoted-argument]='fg=#BD93F9'
## Keywords
## Built ins
ZSH_HIGHLIGHT_STYLES[builtin]='fg=#8BE9FD'
ZSH_HIGHLIGHT_STYLES[reserved-word]='fg=#8BE9FD'
ZSH_HIGHLIGHT_STYLES[hashed-command]='fg=#8BE9FD'
## Punctuation
ZSH_HIGHLIGHT_STYLES[commandseparator]='fg=#FF79C6'
ZSH_HIGHLIGHT_STYLES[command-substitution-delimiter]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[command-substitution-delimiter-unquoted]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[process-substitution-delimiter]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[back-quoted-argument-delimiter]='fg=#FF79C6'
ZSH_HIGHLIGHT_STYLES[back-double-quoted-argument]='fg=#FF79C6'
ZSH_HIGHLIGHT_STYLES[back-dollar-quoted-argument]='fg=#FF79C6'
## Serializable / Configuration Languages
## Storage
## Strings
ZSH_HIGHLIGHT_STYLES[command-substitution-quoted]='fg=#F1FA8C'
ZSH_HIGHLIGHT_STYLES[command-substitution-delimiter-quoted]='fg=#F1FA8C'
ZSH_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#F1FA8C'
ZSH_HIGHLIGHT_STYLES[single-quoted-argument-unclosed]='fg=#FF5555'
ZSH_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#F1FA8C'
ZSH_HIGHLIGHT_STYLES[double-quoted-argument-unclosed]='fg=#FF5555'
ZSH_HIGHLIGHT_STYLES[rc-quote]='fg=#F1FA8C'
## Variables
ZSH_HIGHLIGHT_STYLES[dollar-quoted-argument]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[dollar-quoted-argument-unclosed]='fg=#FF5555'
ZSH_HIGHLIGHT_STYLES[dollar-double-quoted-argument]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[assign]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[named-fd]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[numeric-fd]='fg=#F8F8F2'
## No category relevant in spec
ZSH_HIGHLIGHT_STYLES[unknown-token]='fg=#FF5555'
ZSH_HIGHLIGHT_STYLES[path]='fg=#8BE9FD'
ZSH_HIGHLIGHT_STYLES[path_pathseparator]='fg=#FF79C6'
ZSH_HIGHLIGHT_STYLES[path_prefix]='fg=#8BE9FD'
ZSH_HIGHLIGHT_STYLES[path_prefix_pathseparator]='fg=#FF79C6'
ZSH_HIGHLIGHT_STYLES[globbing]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[history-expansion]='fg=#BD93F9'
#ZSH_HIGHLIGHT_STYLES[command-substitution]='fg=?'
#ZSH_HIGHLIGHT_STYLES[command-substitution-unquoted]='fg=?'
#ZSH_HIGHLIGHT_STYLES[process-substitution]='fg=?'
#ZSH_HIGHLIGHT_STYLES[arithmetic-expansion]='fg=?'
ZSH_HIGHLIGHT_STYLES[back-quoted-argument-unclosed]='fg=#FF5555'
ZSH_HIGHLIGHT_STYLES[redirection]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[arg0]='fg=#F8F8F2'
ZSH_HIGHLIGHT_STYLES[default]='fg=#F8F8F2'
# disabled cursor highlighter to keep terminal cursor unchanged
ZSH_HIGHLIGHT_STYLES[cursor]=none
# activate syntax-highlighting
if [ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
    . /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
elif [ -f /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
    . /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
fi
# enable syntax-highlighting
# if [ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
#     . /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
# elif [ -f /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
#     . /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
# fi
# if [ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ] || [ -f /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
#     ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets pattern)
#     ZSH_HIGHLIGHT_STYLES[default]=none
#     ZSH_HIGHLIGHT_STYLES[unknown-token]=underline
#     ZSH_HIGHLIGHT_STYLES[reserved-word]=fg=cyan,bold
#     ZSH_HIGHLIGHT_STYLES[suffix-alias]=fg=green,underline
#     ZSH_HIGHLIGHT_STYLES[global-alias]=fg=green,bold
#     ZSH_HIGHLIGHT_STYLES[precommand]=fg=green,underline
#     ZSH_HIGHLIGHT_STYLES[commandseparator]=fg=blue,bold
#     ZSH_HIGHLIGHT_STYLES[autodirectory]=fg=green,underline
#     ZSH_HIGHLIGHT_STYLES[path]=bold
#     ZSH_HIGHLIGHT_STYLES[path_pathseparator]=
#     ZSH_HIGHLIGHT_STYLES[path_prefix_pathseparator]=
#     ZSH_HIGHLIGHT_STYLES[globbing]=fg=blue,bold
#     ZSH_HIGHLIGHT_STYLES[history-expansion]=fg=blue,bold
#     ZSH_HIGHLIGHT_STYLES[command-substitution]=none
#     ZSH_HIGHLIGHT_STYLES[command-substitution-delimiter]=fg=magenta,bold
#     ZSH_HIGHLIGHT_STYLES[process-substitution]=none
#     ZSH_HIGHLIGHT_STYLES[process-substitution-delimiter]=fg=magenta,bold
#     ZSH_HIGHLIGHT_STYLES[single-hyphen-option]=fg=green
#     ZSH_HIGHLIGHT_STYLES[double-hyphen-option]=fg=green
#     ZSH_HIGHLIGHT_STYLES[back-quoted-argument]=none
#     ZSH_HIGHLIGHT_STYLES[back-quoted-argument-delimiter]=fg=blue,bold
#     ZSH_HIGHLIGHT_STYLES[single-quoted-argument]=fg=yellow
#     ZSH_HIGHLIGHT_STYLES[double-quoted-argument]=fg=yellow
#     ZSH_HIGHLIGHT_STYLES[dollar-quoted-argument]=fg=yellow
#     ZSH_HIGHLIGHT_STYLES[rc-quote]=fg=magenta
#     ZSH_HIGHLIGHT_STYLES[dollar-double-quoted-argument]=fg=magenta,bold
#     ZSH_HIGHLIGHT_STYLES[back-double-quoted-argument]=fg=magenta,bold
#     ZSH_HIGHLIGHT_STYLES[back-dollar-quoted-argument]=fg=magenta,bold
#     ZSH_HIGHLIGHT_STYLES[assign]=none
#     ZSH_HIGHLIGHT_STYLES[redirection]=fg=blue,bold
#     ZSH_HIGHLIGHT_STYLES[comment]=fg=black,bold
#     ZSH_HIGHLIGHT_STYLES[named-fd]=none
#     ZSH_HIGHLIGHT_STYLES[numeric-fd]=none
#     ZSH_HIGHLIGHT_STYLES[arg0]=fg=cyan
#     ZSH_HIGHLIGHT_STYLES[bracket-error]=fg=red,bold
#     ZSH_HIGHLIGHT_STYLES[bracket-level-1]=fg=blue,bold
#     ZSH_HIGHLIGHT_STYLES[bracket-level-2]=fg=green,bold
#     ZSH_HIGHLIGHT_STYLES[bracket-level-3]=fg=magenta,bold
#     ZSH_HIGHLIGHT_STYLES[bracket-level-4]=fg=yellow,bold
#     ZSH_HIGHLIGHT_STYLES[bracket-level-5]=fg=cyan,bold
#     ZSH_HIGHLIGHT_STYLES[cursor-matchingbracket]=standout
# fi



# enable color support of ls, less and man, and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    export LS_COLORS="$LS_COLORS:ow=30;44:" # fix ls color for folders with 777 permissions
    export LESS_TERMCAP_mb=$'\E[1;38;2;255;85;85m'     # begin blink - Dracula Red #FF5555 fixed, ignores pywal
    export LESS_TERMCAP_md=$'\E[1;38;2;139;233;253m'   # begin bold - Dracula Cyan #8BE9FD fixed
    export LESS_TERMCAP_me=$'\E[0m'        # reset bold/blink
    export LESS_TERMCAP_so=$'\E[1;38;2;241;250;140;48;2;68;71;90m'    # begin reverse video - Dracula Yellow #F1FA8C on Selection #44475A
    export LESS_TERMCAP_se=$'\E[0m'        # reset reverse video
    export LESS_TERMCAP_us=$'\E[4;1;38;2;80;250;123m'  # begin underline - Dracula Green #50FA7B fixed
    export LESS_TERMCAP_ue=$'\E[0m'        # reset underline
    export MANROFFOPT="-c"
    export GROFF_NO_SGR=1                  # force overstrike so LESS_TERMCAP applies

    # Take advantage of $LS_COLORS for completion as well
    zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
    zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#)*=0=01;31'
fi

alias ls='eza -al --color=always --group-directories-first --icons always'
alias la='eza -a --color=always --group-directories-first --icons always'
alias ll='eza -l --color=always --group-directories-first --icons always'
alias lt='eza -aT --color=always --group-directories-first --icons always'
alias l.="eza -a | grep -e '^\.'"
alias l='ls -CF'
alias grubup="sudo grub-mkconfig -o /boot/grub/grub.cfg"
alias fixpacman="sudo rm /var/lib/pacman/db.lck"
alias tarnow='tar -acf '
alias untar='tar -zxvf '
alias wget='wget -c '
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias ......='cd ../../../../..'
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
alias clean='sudo paccache -rk0'
alias rip="expac --timefmt='%Y-%m-%d %T' '%l\t%n %v' | sort | tail -200 | nl"

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
  local -a matches
  matches=("${(@f)$(sudo plocate -br "^${needle}$" "$@")}")
  if (( ${#matches[@]} == 0 )); then
    echo "No matches found for: $needle"
    return 1
  fi
  printf 'Matches:\n'
  printf '  %s\n' "${matches[@]}"
  local answer
  read -r "answer?Run sudo rm -rf on these results? [y/N] "
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
  local -a matches
  matches=("${(@f)$(sudo fd -u "^${needle}$" "$@")}")
  if (( ${#matches[@]} == 0 )); then
    echo "No matches found for: $needle"
    return 1
  fi
  printf 'Matches:\n'
  printf '  %s\n' "${matches[@]}"
  local answer
  read -r "answer?Run sudo rm -rf on these results? [y/N] "
  [[ $answer == [yY] || $answer == [yY][eE][sS] ]] || return 0
  sudo fd -u "^${needle}$" "$@" -X sudo rm -rf {}
}

fa() {
  sudo fd -u "$1" "${@:2}"
}

fe() {
  sudo fd -u "^$1$" "${@:2}"
}

# enable auto-suggestions based on the history
if [ -f /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]; then
    . /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
elif [ -f /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh ]; then
    . /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
fi
if typeset -f _zsh_autosuggest_start > /dev/null 2>&1; then
    # change suggestion color
    ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=244'
fi

# enable command-not-found if installed
if [ -f /etc/zsh_command_not_found ]; then
    . /etc/zsh_command_not_found
elif [ -f /usr/share/doc/pkgfile/command-not-found.zsh ]; then
    . /usr/share/doc/pkgfile/command-not-found.zsh
fi

# export FZF_CTRL_R_OPTS="--exact --no-sort --height=11 --style=minimal --reverse"
# command -v fzf > /dev/null 2>&1 && eval "$(fzf --zsh)"

autoload -U colors && colors

# git_branch() {
#   git rev-parse --abbrev-ref HEAD 2>/dev/null
# }

# git_dirty() {
#   git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return
#   if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
#     echo "✓"
#   else
#     echo "✗"
#   fi
# }

# git_prompt_info() {
#   local branch
#   branch=$(git_branch) || return
#   [[ -n $branch ]] || return
#   [[ $branch == HEAD ]] && branch=$(git rev-parse --short HEAD 2>/dev/null)
#   branch=${branch//\%/%%}
#   local dirty
#   dirty=$(git_dirty)
#   print -n "%F{#f952ff}(%f%F{#ff8c12}${branch}%f%F{#00ff08}${dirty}%f%F{#ff44ff})%f"
# }
# $(git_prompt_info) at _ PROMPT='%F{#a5e3ff}%n%f%F{#ff9500}@%f%F{#00ff64}%m%f%F{#2dd4bf}:%f%F{#ff3333}{%f%F{#7ddbff}%1~%f_%F{#ff3333}}%f'$'\n''%F{#ffff00}❯%f '

PROMPT='%F{#a5e3ff}%n%f%F{#ff9500}@%f%F{#00ff64}%m%f%F{#2dd4bf}:%f%F{#ff3333}{%f%F{#7ddbff}%1~%f%F{#ff3333}}%f'$'\n''%F{#ffff00}❯%f '
