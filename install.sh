#!/bin/zsh
# Instala Nube Limit en REAPER (macOS) como enlace: los cambios del repo se ven al volver a insertar el FX.
set -e
DST="$HOME/Library/Application Support/REAPER/Effects/Nube Limit"
cd "$(dirname "$0")"
mkdir -p "$DST"
ln -sf "$PWD/nube_limit.jsfx" "$DST/nube_limit.jsfx"
echo "Listo: en REAPER busca \"Nube Limit\" en el navegador de FX (JS: Nube Limit)."
