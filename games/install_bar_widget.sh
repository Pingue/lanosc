#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WIDGET_SRC="$SRC_DIR/bar_lua/lanosc_spectator.lua"

if [[ ! -f "$WIDGET_SRC" ]]; then
  echo "Widget source not found: $WIDGET_SRC" >&2
  exit 1
fi

DESTS=(
  "$HOME/.config/Beyond-All-Reason/LuaUI/Widgets"
  "$HOME/.local/share/Beyond-All-Reason/LuaUI/Widgets"
  "$HOME/.spring/LuaUI/Widgets"
)

installed=0
for d in "${DESTS[@]}"; do
  mkdir -p "$d"
  cp "$WIDGET_SRC" "$d/"
  echo "Installed: $d/lanosc_spectator.lua"
  installed=1
done

if [[ "$installed" -eq 0 ]]; then
  echo "No destination installed." >&2
  exit 1
fi

echo
echo "Next steps:"
echo "1) Start LANOSC with BAR adapter enabled in lanosc.toml"
echo "2) Start BAR as spectator"
echo "3) In BAR Widgets menu, ensure 'LANOSC Spectator Bridge' is enabled"
