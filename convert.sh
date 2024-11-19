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

case "$TO_EXT" in
    # Docs

    # doc/docx not working for now
    # "docx")
    #     soffice --headless --infilter="writer_pdf_import" \
    #         --convert-to doc:"writer_pdf_Export" $ORG_PATH \
    #         --outdir "convfiles/" >/dev/null 2>&1
    #     mv "convfiles/$ORG_NAME_NO_EXT.docx" "convfiles/$CONV_NAME.docx"
    #     echo -n "$CONV_NAME.docx" 
    #    ;;
        
    "compdf")
        gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen \
            -dNOPAUSE -dQUIET -dBATCH -sOutputFile="convfiles/$CONV_NAME.pdf" \
            "$ORG_PATH" >/dev/null 2>&1
        echo -n "$CONV_NAME.pdf"
        ;;
    "pdf")
        soffice --headless --convert-to "pdf:writer_pdf_Export" "$ORG_PATH" \
            --outdir "convfiles/" >/dev/null 2>&1
        mv "convfiles/$ORG_NAME_NO_EXT.pdf" "convfiles/$CONV_NAME.pdf"
        echo -n "$CONV_NAME.pdf" 
        ;;

    # Images
    # TODO: Maybe rethink file conversion by adding compression. Converted pngs
    # get really big.
    "jpeg"|"png"|"webp")
        convert "$ORG_PATH" -quality 90 -colorspace sRGB "convfiles/$CONV_NAME.$TO_EXT"
        # pngquant -f --ext .png "convfiles/$CONV_NAME.$TO_EXT"
        echo -n "$CONV_NAME.$TO_EXT"
        ;;

    # Audio
    "mp3@320k")
        ffmpeg  -i "$ORG_PATH" -c:v libmp3lame -b:a 320k \
            "convfiles/$CONV_NAME.mp3"
        echo -n "$CONV_NAME.mp3"
        ;;
    "mp3@256k")
        ffmpeg -i "$ORG_PATH" -c:v libmp3lame -b:a 256k \
            "convfiles/$CONV_NAME.mp3"
        echo -n "$CONV_NAME.mp3"
        ;;
    "mp3@128k")
        ffmpeg -i "$ORG_PATH" -c:v libmp3lame -b:a 128k \
            "convfiles/$CONV_NAME.mp3"
        echo -n "$CONV_NAME.mp3"
        ;;
    "opus@128k")
        ffmpeg -i "$ORG_PATH" -c:v opus -b:a 128k \
            "convfiles/$CONV_NAME.opus"
        echo -n "$CONV_NAME.opus"
        ;;

    # Video
    "mp4")
        ffmpeg -i "$ORG_PATH" -c:v libx264 -c:a aac -crf 22 -b:a 256k \
            "convfiles/$CONV_NAME.mp4"
        echo -n "$CONV_NAME.mp4"
        ;;
    "webm")
        ffmpeg -i "$ORG_PATH" -c:v libvpx-vp9 -c:a opus -crf 21 -b:a 128k \
            "convfiles/$CONV_NAME.webm"
        echo -n "$CONV_NAME.webm"
        ;;

    # If none of the above, echo an error message.
    *)
        echo -n "-1"
        ;;
esac
