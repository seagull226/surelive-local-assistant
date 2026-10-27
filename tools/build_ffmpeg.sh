#!/usr/bin/env bash
# Run in MSYS2 UCRT64 with gcc, make, diffutils and nasm. No external codec libraries.
set -euo pipefail
source_dir="$(cd "$1" && pwd)"
mkdir -p "$2"
cd "$2"
"$source_dir/configure" --target-os=mingw32 --arch=x86_64 \
  --disable-autodetect --disable-network --disable-gpl --disable-nonfree \
  --disable-doc --disable-debug --disable-ffplay --disable-ffprobe \
  --disable-avdevice --disable-postproc --disable-encoders --disable-muxers \
  --enable-encoder=pcm_f32le --enable-muxer=pcm_f32le \
  --disable-shared --enable-static --extra-ldflags=-static
make -j8 ffmpeg.exe
./ffmpeg.exe -version > build-version.txt
cp ffbuild/config.log build-config.log
