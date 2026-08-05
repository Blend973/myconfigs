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

# Suppress autocd output (cd -- dir/)
exec {BASH_XTRACEFD}>/dev/null

# History search: up/down arrows cycle through history matching typed text
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# History settings
HISTSIZE=10000
HISTFILESIZE=10000

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
alias hw='hwinfo --short'
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
alias tb='nc termbin.com 9999'
alias cleanup='sudo pacman -Rcsn $(pacman -Qtdq)'
alias jctl="journalctl -p 3 -xb"
alias rip="expac --timefmt='%Y-%m-%d %T' '%l\t%n %v' | sort | tail -200 | nl"

# Search functions
pe() {
    sudo plocate --regexp --basename "^$1$"
}

pa() {
    sudo plocate --regexp --basename "$1"
}

fa() {
    sudo fd -u "$1" /
}

fb() {
    sudo fd -u "^$1$" /
}

# Git-aware prompt with nerd symbols
__git_prompt() {
    local branch=$(git symbolic-ref --short HEAD 2>/dev/null)
    if [ -n "$branch" ]; then
        local dirty=$(git diff --quiet 2>/dev/null || echo " 󰦷 ")
        printf " \e[1;36m\e[0m \e[1;33m%s%s" "$branch" "$dirty"
    fi
}

PS1='\[\e[1;31m\]\u\[\e[38;5;120m\]@\[\e[1;34m\]\h\[\e[0m\] \[\e[1;35m\] \[\e[38;5;79m\]\w\[\e[33m\]$(__git_prompt)\[\e[0m\]\n\[\e[38;5;120m\]❯\[\e[0m\] '
