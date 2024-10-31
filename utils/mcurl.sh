#!/bin/sh

# Send multiple request at the same time using curl-client
./curl-client.sh &
./curl-client.sh &
./curl-client.sh &
./curl-client.sh &
./curl-client.sh &
./curl-client.sh &

 wait 
