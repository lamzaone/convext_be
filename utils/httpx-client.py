#!/usr/bin/env python3

# 132 bytes from the start
# 40 bytes from the end

import httpx
import time


# Set some paramteres
url ='http://127.0.0.1:8000/upload'
# headers = {'user-agent': 'my-app/0.0.1'}
# files is name of input field in a html form, we attach hello.txt to it
files = {"files" : open('hello.txt', 'rb')}

# start the client and the timer, send the request, return elapsed time and
# status code, also server response
with httpx.Client() as client:
    start = time.time()
    r = client.post(url, files=files)
    end = time.time()
    print(f'Time elapsed: {end - start}s')
    print(r.status_code, r.content, sep='\n')

