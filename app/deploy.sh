#!/usr/bin/env bash

user="$USER"

echo "Attempting to kill existing processes..."
pkill -f "python views.py"
pkill -f "ngrok"

echo "Changing permissions to $user:$user..."
sudo chown -R $user:$user ..
echo "Running flaskapp..."
python flaskapp.py &
echo "Running ngrok..."
nohup ngrok http -region=eu -log=stdout 5000 > ngrok.log &
sleep 1
python ngrokinstances.py
