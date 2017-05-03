#!/usr/bin/env bash

sudo chown -R rawandhawiz:rawandhawiz ..
sudo chown root:root ngrok
sudo chmod +x ngrok
python contentuploader.py &
ngrok http -log=stdout 5000 > /dev/null &
python ngrokinstances.py