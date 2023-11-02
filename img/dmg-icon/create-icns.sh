#!/bin/sh

# This script takes the source dmg-icon-macos.png and converts it to an iconset with all needed image sizes included
# for macos deployment. Credits to glyph (https://github.com/glyph).

mkdir dmg-icon-macos.iconset
sips -z 16 16     dmg-icon-macos.png --out dmg-icon-macos.iconset/icon_16x16.png
sips -z 32 32     dmg-icon-macos.png --out dmg-icon-macos.iconset/icon_16x16@2x.png
sips -z 32 32     dmg-icon-macos.png --out dmg-icon-macos.iconset/icon_32x32.png
sips -z 64 64     dmg-icon-macos.png --out dmg-icon-macos.iconset/icon_32x32@2x.png
sips -z 128 128   dmg-icon-macos.png --out dmg-icon-macos.iconset/icon_128x128.png
sips -z 256 256   dmg-icon-macos.png --out dmg-icon-macos.iconset/icon_128x128@2x.png
sips -z 256 256   dmg-icon-macos.png --out dmg-icon-macos.iconset/icon_256x256.png
sips -z 512 512   dmg-icon-macos.png --out dmg-icon-macos.iconset/icon_256x256@2x.png
sips -z 512 512   dmg-icon-macos.png --out dmg-icon-macos.iconset/icon_512x512.png
cp dmg-icon-macos.png dmg-icon-macos.iconset/icon_512x512@2x.png
iconutil -c icns dmg-icon-macos.iconset
rm -R dmg-icon-macos.iconset

