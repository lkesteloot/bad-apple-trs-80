#!/bin/bash

INPUT_DIR="./image_sequence"
OUTPUT_DIR="./converted_images"

mkdir -p "$OUTPUT_DIR"

process_image() {
    local i="$1"
    local filename="bad_apple_${i}.png"
    local input_file="$INPUT_DIR/$filename"
    local output_file="$OUTPUT_DIR/${filename%.png}.pgm"

    if [[ -f "$input_file" ]]; then
        convert "$input_file" -resize 128x48! -colorspace Gray -compress none "$output_file"
        echo "Converted: $filename"
    else
        echo "Missing: $filename"
    fi
}

export -f process_image
export INPUT_DIR OUTPUT_DIR

# Use seq -f to get correct zero-padded numbers, then run in parallel
seq -f "%03g" 1 6562 | xargs -n 1 -P 16 -I{} bash -c 'process_image "$@"' _ {}

