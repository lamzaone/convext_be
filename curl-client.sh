#!/bin/sh

# 146 bytes from the start
# 54 bytes from the end

curl -X 'POST' \
  'http://alpha.lan:8000/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@hello.txt;type=text/plain'

# Simple POST request, data gets send differently
#  -d '@hello.txt' 
