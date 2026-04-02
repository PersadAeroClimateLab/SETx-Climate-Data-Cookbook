#!/usr/bin/env bash
set -euo pipefail
 
URL="https://web.corral.tacc.utexas.edu/setxuifl/setx-climate-atlas-datasets.tar.gz"
ARCHIVE="setx-climate-atlas-datasets.tar.gz"
DEST="../data"
 
echo "[1/3] Downloading..."
wget --progress=bar:force:noscroll -q --show-progress -O "$ARCHIVE" "$URL"
 
echo "[2/3] Extracting..."
mkdir -p "$DEST"
tar -xf "$ARCHIVE" -C "$DEST" --checkpoint=500 --checkpoint-action=exec='printf "\r  %d files extracted" $TAR_CHECKPOINT'
printf "\n"
 
echo "[3/3] Cleaning up..."
rm "$ARCHIVE"
 
echo "Done! Dataset extracted to $DEST/"