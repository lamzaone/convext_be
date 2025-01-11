#!/bin/sh



## VARIABLES

# Flag for authenticated user
AUTH="$1"

# Path of the file to convert. (first arg)
FILE_PATH="$2" 


# Path of the file without the filename, just the firectory
FILE_PATH_DIR=$(dirname "$2")

# Name+ext of the file to convert, extracted from
# path.  
FILE_NAME="${FILE_PATH##*/}" 

# Name of the file to convert, no extension.
FILE_NAME_NO_EXT="${FILE_NAME%.*}" 

# Extension to convert to. (second arg) 
TO_EXT="$3" 

if [ $AUTH = "True" ]; then
    CONV_NAME="$FILE_NAME_NO_EXT"
    CONV_PATH="$FILE_PATH_DIR"
else
    CONV_NAME=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 16)
    CONV_PATH="convfiles"
fi

CONV_PATH_WITH_NAME="$CONV_PATH/$CONV_NAME"



## MAIN

case "$TO_EXT" in
    # Docs

    # doc/docx not sure if working
    
    "docx")
        soffice --headless --convert-to docx "$FILE_PATH" \
            --outdir "$CONV_PATH" >/dev/null 2>&1
        mv "$CONV_PATH/$FILE_NAME_NO_EXT.docx" "$CONV_PATH_WITH_NAME.docx"
        echo -n "$CONV_PATH_WITH_NAME.docx"
        ;;

        
    "compdf")
        gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen \
            -dNOPAUSE -dQUIET -dBATCH -sOutputFile="$CONV_PATH_WITH_NAME.pdf" \
            "$FILE_PATH" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.pdf"
        ;;
    "pdf")
        soffice --headless --convert-to "pdf:writer_pdf_Export" "$FILE_PATH" \
            --outdir "$CONV_PATH" >/dev/null 2>&1
        mv "$CONV_PATH/$FILE_NAME_NO_EXT.pdf" "$CONV_PATH_WITH_NAME.pdf"
        echo -n "$CONV_PATH_WITH_NAME.pdf" 
        ;;

    # Images
    
    "jpeg"|"webp")
        convert "$FILE_PATH" -quality 90 -colorspace sRGB \
            "$CONV_PATH_WITH_NAME.$TO_EXT"
        echo -n "$CONV_PATH_WITH_NAME.$TO_EXT"
        ;;
    
    "png")
        # Convert the PNG file and optionally compress using pngquant for better size optimization
        convert "$FILE_PATH" -quality 90 -colorspace sRGB \
            "$CONV_PATH_WITH_NAME.$TO_EXT"
        pngquant -f --ext .png "$CONV_PATH_WITH_NAME.$TO_EXT" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.$TO_EXT"
        ;;

    # Audio
    "mp3@320k"|"mp3@256k"|"mp3@128k")
        BITRATE=${TO_EXT#*@}
        ffmpeg -i "$FILE_PATH" -c:a libmp3lame -b:a "$BITRATE" \
            "$CONV_PATH_WITH_NAME.mp3" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.mp3"
        ;;
        
    "opus@128k")
        ffmpeg -i "$FILE_PATH" -c:v opus -b:a 128k \
            "$CONV_PATH_WITH_NAME.opus"
        echo -n "$CONV_PATH_WITH_NAME.opus"
        ;;

    # Video
    "mp4")
        ffmpeg -i "$FILE_PATH" -c:v libx264 -c:a aac -crf 22 -b:a 256k \
            "$CONV_PATH_WITH_NAME.mp4"
        echo -n "$CONV_PATH_WITH_NAME.mp4"
        ;;
    "webm")
        ffmpeg -i "$FILE_PATH" -c:v libvpx-vp9 -c:a opus -crf 21 -b:a 128k \
            "$CONV_PATH_WITH_NAME.webm"
        echo -n "$CONV_PATH_WITH_NAME.webm"
        ;;

    # If none of the above, echo an error message.
    *)
        echo "Error: Unsupported conversion format '$TO_EXT'."
        echo -n "-1"
        ;;
esac
