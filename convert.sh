#!/bin/sh

ORG_PATH="$1"
ORG_NAME="${ORG_PATH##*/}"
ORG_NAME_NO_EXT="${ORG_NAME%.*}"
TO_EXT="$2"
UUID=`cat /proc/sys/kernel/random/uuid`
CONV_NAME=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 16)

if [ "$TO_EXT" = "png" ]; then
    convert "$ORG_PATH" -quality 90 "convfiles/$CONV_NAME.png"
    echo -n "$CONV_NAME.png"
else
    echo -n "Error. Filetype not supported." 1>&2
fi
