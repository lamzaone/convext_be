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

    # doc/docx not working for now
    # !!!THIS NEEDS TO BE CHANGED!!!
    # "docx")
    #     soffice --headless --infilter="writer_pdf_import" \
    #         --convert-to doc:"writer_pdf_Export" $ORG_PATH \
    #         --outdir "convfiles/" >/dev/null 2>&1
    #     mv "convfiles/$ORG_NAME_NO_EXT.docx" "convfiles/$CONV_PATH.docx"
    #     # echo -n "$CONV_PATH.docx" 
    #    ;;
        
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
    # TODO: Maybe rethink file conversion by adding compression. Converted pngs
    # get really big.
    "jpeg"|"png"|"webp")
        convert "$FILE_PATH" -quality 90 -colorspace sRGB \
            "$CONV_PATH_WITH_NAME.$TO_EXT"
        # pngquant -f --ext .png "$CONV_PATH_WITH_NAME.$TO_EXT"
        echo -n "$CONV_PATH_WITH_NAME.$TO_EXT"
        ;;

    # Audio
    "mp3@320k")
        ffmpeg  -i "$FILE_PATH" -c:v libmp3lame -b:a 320k \
            "$CONV_PATH_WITH_NAME.mp3"
        echo -n "$CONV_PATH_WITH_NAME.mp3"
        ;;
    "mp3@256k")
        ffmpeg -i "$FILE_PATH" -c:v libmp3lame -b:a 256k \
            "$CONV_PATH_WITH_NAME.mp3"
        echo -n "$CONV_PATH_WITH_NAME.mp3"
        ;;
    "mp3@128k")
        ffmpeg -i "$FILE_PATH" -c:v libmp3lame -b:a 128k \
            "$CONV_PATH_WITH_NAME.mp3"
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
        echo -n "-1"
        ;;
esac
