#!/bin/sh

# This script takes the source logo.macos.png and converts it to an iconset with all needed image sizes included
# for macos deployment. Credits to glyph (https://github.com/glyph).

mkdir logo_macos.iconset
sips -z 16 16     logo_macos.png --out logo_macos.iconset/icon_16x16.png
sips -z 32 32     logo_macos.png --out logo_macos.iconset/icon_16x16@2x.png
sips -z 32 32     logo_macos.png --out logo_macos.iconset/icon_32x32.png
sips -z 64 64     logo_macos.png --out logo_macos.iconset/icon_32x32@2x.png
sips -z 128 128   logo_macos.png --out logo_macos.iconset/icon_128x128.png
sips -z 256 256   logo_macos.png --out logo_macos.iconset/icon_128x128@2x.png
sips -z 256 256   logo_macos.png --out logo_macos.iconset/icon_256x256.png
sips -z 512 512   logo_macos.png --out logo_macos.iconset/icon_256x256@2x.png
sips -z 512 512   logo_macos.png --out logo_macos.iconset/icon_512x512.png
cp logo_macos.png logo_macos.iconset/icon_512x512@2x.png
iconutil -c icns logo_macos.iconset
rm -R logo_macos.iconset

