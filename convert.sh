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
    # Documents
    "doc")
        soffice --headless --convert-to doc "$FILE_PATH" \
            --outdir "$CONV_PATH" >/dev/null 2>&1
        mv "$CONV_PATH/$FILE_NAME_NO_EXT.doc" "$CONV_PATH_WITH_NAME.doc"
        echo -n "$CONV_PATH_WITH_NAME.doc"
        ;;
    "docx")
        soffice --headless --convert-to docx "$FILE_PATH" \
            --outdir "$CONV_PATH" >/dev/null 2>&1
        mv "$CONV_PATH/$FILE_NAME_NO_EXT.docx" "$CONV_PATH_WITH_NAME.docx"
        echo -n "$CONV_PATH_WITH_NAME.docx"
        ;;
    "pdf")
        soffice --headless --convert-to "pdf:writer_pdf_Export" "$FILE_PATH" \
            --outdir "$CONV_PATH" >/dev/null 2>&1
        mv "$CONV_PATH/$FILE_NAME_NO_EXT.pdf" "$CONV_PATH_WITH_NAME.pdf"
        echo -n "$CONV_PATH_WITH_NAME.pdf"
        ;;
    "txt")
        soffice --headless --convert-to txt "$FILE_PATH" \
            --outdir "$CONV_PATH" >/dev/null 2>&1
        mv "$CONV_PATH/$FILE_NAME_NO_EXT.txt" "$CONV_PATH_WITH_NAME.txt"
        echo -n "$CONV_PATH_WITH_NAME.txt"
        ;;

    # Images
    "jpeg"|"png"|"gif"|"webp"|"jpg")
        convert "$FILE_PATH" -quality 90 -colorspace sRGB \
            "$CONV_PATH_WITH_NAME.$TO_EXT"
        echo -n "$CONV_PATH_WITH_NAME.$TO_EXT"
        ;;
    
    # Videos
    "mp4")
        ffmpeg -i "$FILE_PATH" -c:v libx264 -c:a aac -crf 22 -b:a 256k \
            "$CONV_PATH_WITH_NAME.mp4" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.mp4"
        ;;
    # "webm")
    #     ffmpeg -i "$FILE_PATH" -c:v libvpx-vp9 -c:a opus -crf 21 -b:a 128k \
    #         "$CONV_PATH_WITH_NAME.webm" >/dev/null 2>&1
    #     echo -n "$CONV_PATH_WITH_NAME.webm"
    #     ;;
    "avi")
        ffmpeg -i "$FILE_PATH" -c:v libx264 -crf 22 -preset fast \
            "$CONV_PATH_WITH_NAME.avi" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.avi"
        ;;
    "mov")
        ffmpeg -i "$FILE_PATH" -c:v prores -c:a pcm_s16le \
            "$CONV_PATH_WITH_NAME.mov" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.mov"
        ;;
    "mkv")
        ffmpeg -i "$FILE_PATH" -c:v libx264 -c:a aac \
            "$CONV_PATH_WITH_NAME.mkv" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.mkv"
        ;;

    # Audio
    "mp3")
        ffmpeg -i "$FILE_PATH" -c:a libmp3lame -b:a 256k \
            "$CONV_PATH_WITH_NAME.mp3" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.mp3"
        ;;
    "wav")
        ffmpeg -i "$FILE_PATH" -c:a pcm_s16le \
            "$CONV_PATH_WITH_NAME.wav" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.wav"
        ;;
    "ogg")
        ffmpeg -i "$FILE_PATH" -c:a libvorbis -q:a 4 \
            "$CONV_PATH_WITH_NAME.ogg" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.ogg"
        ;;
    "flac")
        ffmpeg -i "$FILE_PATH" -c:a flac \
            "$CONV_PATH_WITH_NAME.flac" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.flac"
        ;;
    "aac")
        ffmpeg -i "$FILE_PATH" -c:a aac -b:a 256k \
            "$CONV_PATH_WITH_NAME.aac" >/dev/null 2>&1
        echo -n "$CONV_PATH_WITH_NAME.aac"
        ;;

    # Compressed formats
    # Convert to ZIP
    "zip")
        # Extract files from source archive into a folder named after the archive
        case "$FILE_PATH" in
            *.rar) unrar x -o+ "$FILE_PATH" "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.7z) 7z x "$FILE_PATH" -o"$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.tar) tar -xvf "$FILE_PATH" -C "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.gz) gunzip -c "$FILE_PATH" > "$CONV_PATH/$(basename "${FILE_PATH%.*}")" ;;
            *.zip) unzip -o "$FILE_PATH" -d "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *) echo "Error: Unsupported source format for ZIP conversion."; echo -n "-1"; exit 1 ;;
        esac
        # Archive only the extracted folder into the new ZIP archive
        zip -r "$CONV_PATH_WITH_NAME.zip" "$CONV_PATH/$(basename "${FILE_PATH%.*}")" >/dev/null 2>&1
        # Delete the initial archive and the extracted folder
        rm -rf "$FILE_PATH" "$CONV_PATH/$(basename "${FILE_PATH%.*}")"
        echo -n "$CONV_PATH_WITH_NAME.zip"
        ;;

    # Convert to TAR
    "tar")
        case "$FILE_PATH" in
            *.rar) unrar x -o+ "$FILE_PATH" "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.7z) 7z x "$FILE_PATH" -o"$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.zip) unzip -o "$FILE_PATH" -d "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.gz) gunzip -c "$FILE_PATH" > "$CONV_PATH/$(basename "${FILE_PATH%.*}")" ;;
            *) echo "Error: Unsupported source format for TAR conversion."; echo -n "-1"; exit 1 ;;
        esac
        # Create TAR archive from the extracted folder
        tar -cvf "$CONV_PATH_WITH_NAME.tar" -C "$CONV_PATH" "$(basename "${FILE_PATH%.*}")" >/dev/null 2>&1
        # Delete the initial archive and the extracted folder
        rm -rf "$FILE_PATH" "$CONV_PATH/$(basename "${FILE_PATH%.*}")"
        echo -n "$CONV_PATH_WITH_NAME.tar"
        ;;

    # Convert to GZ
    "gz")
        case "$FILE_PATH" in
            *.rar) unrar x -o+ "$FILE_PATH" "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.7z) 7z x "$FILE_PATH" -o"$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.zip) unzip -o "$FILE_PATH" -d "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.tar) tar -xvf "$FILE_PATH" -C "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *) echo "Error: Unsupported source format for GZ conversion."; echo -n "-1"; exit 1 ;;
        esac
        # Create GZ archive from the extracted folder
        tar -czvf "$CONV_PATH_WITH_NAME.gz" -C "$CONV_PATH" "$(basename "${FILE_PATH%.*}")" >/dev/null 2>&1
        # Delete the initial archive and the extracted folder
        rm -rf "$FILE_PATH" "$CONV_PATH/$(basename "${FILE_PATH%.*}")"
        echo -n "$CONV_PATH_WITH_NAME.gz"
        ;;

    # Convert to 7Z
    "7z")
        case "$FILE_PATH" in
            *.rar) unrar x -o+ "$FILE_PATH" "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.zip) unzip -o "$FILE_PATH" -d "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.tar) tar -xvf "$FILE_PATH" -C "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.gz) gunzip -c "$FILE_PATH" > "$CONV_PATH/$(basename "${FILE_PATH%.*}")" ;;
            *) echo "Error: Unsupported source format for 7Z conversion."; echo -n "-1"; exit 1 ;;
        esac
        # Create 7Z archive from the extracted folder
        7z a "$CONV_PATH_WITH_NAME.7z" "$CONV_PATH/$(basename "${FILE_PATH%.*}")"/* >/dev/null 2>&1
        # Delete the initial archive and the extracted folder
        rm -rf "$FILE_PATH" "$CONV_PATH/$(basename "${FILE_PATH%.*}")"
        echo -n "$CONV_PATH_WITH_NAME.7z"
        ;;

    # Convert to RAR
    "rar")
        case "$FILE_PATH" in
            *.zip) unzip -o "$FILE_PATH" -d "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.7z) 7z x "$FILE_PATH" -o"$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.tar) tar -xvf "$FILE_PATH" -C "$CONV_PATH/$(basename "${FILE_PATH%.*}")/" >/dev/null 2>&1 ;;
            *.gz) gunzip -c "$FILE_PATH" > "$CONV_PATH/$(basename "${FILE_PATH%.*}")" ;;
            *) echo "Error: Unsupported source format for RAR conversion."; echo -n "-1"; exit 1 ;;
        esac
        # Create RAR archive from the extracted folder
        rar a "$CONV_PATH_WITH_NAME.rar" "$CONV_PATH/$(basename "${FILE_PATH%.*}")"/* >/dev/null 2>&1
        # Delete the initial archive and the extracted folder
        rm -rf "$FILE_PATH" "$CONV_PATH/$(basename "${FILE_PATH%.*}")"
        echo -n "$CONV_PATH_WITH_NAME.rar"
        ;;





    # Default: unsupported format
    *)
        echo "Error: Unsupported conversion format '$TO_EXT'."
        echo -n "-1"
        ;;
esac
