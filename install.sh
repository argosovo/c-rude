#!/usr/bin/env bash
# Nainstaluje plugin c-rude do Claude Code z této složky (pro instalaci ze zipu).
# Složku po instalaci NEMAŽ – Claude Code z ní čte marketplace.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v claude >/dev/null || { echo "Chybí příkaz 'claude' (Claude Code CLI)."; exit 1; }
command -v python3 >/dev/null || { echo "Chybí python3, plugin ho potřebuje."; exit 1; }

claude plugin marketplace add "$DIR" || true   # už může být přidaný
claude plugin uninstall c-rude@c-rude >/dev/null 2>&1 || true
claude plugin install c-rude@c-rude --scope user

echo
echo "Hotovo. Spusť nový Claude Code a zkus mu zadat něco, co selže."
