#!/bin/sh



## VARIABLES

# Path of the file to convert. (first arg)
ORG_PATH="$1" 

# Name+ext of the file to convert, extracted from
# path.  
ORG_NAME="${ORG_PATH##*/}" 

# Name of the file to convert, no extension.
ORG_NAME_NO_EXT="${ORG_NAME%.*}" 

# Extension to convert to. (second arg) 
TO_EXT="$2" 

# Get random hex string for converted filename. 
CONV_NAME=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 16)



## MAIN

# Just PNG for now. If format to convert to is png call convert from
# ImageMagick with quality 90 and convert it. Echo filename of converted file.
if [ "$TO_EXT" = "png" ]; then
    convert "$ORG_PATH" -quality 90 "convfiles/$CONV_NAME.png"
    echo -n "$CONV_NAME.png"
# If the format is not PNG, echo an error message.
else
    echo -n "Error. Filetype not supported."
fi
