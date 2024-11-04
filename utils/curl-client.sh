#!/bin/sh

# 146 bytes from the start
# 54 bytes from the end

curl -X 'POST' \
  'http://127.0.0.1:8000/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@bliss.jpg;type=image/jpeg' 
echo
# Simple POST request, data gets send differently
#  -d '@hello.txt' 
