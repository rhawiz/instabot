#!/usr/bin/env bash

user="$USER"

echo "Attempting to kill existing processes..."
pkill -f "python contentuploader.py"
pkill -f "ngrok"

echo "Changing permissions to $user:$user..."
sudo chown -R $user:$user ..
echo "Running content uploader..."
nohup python contentuploader.py &
echo "Running ngrok..."
nohup ngrok http -region=eu -log=stdout 5000 > /dev/null &
sleep 1
python ngrokinstances.py
