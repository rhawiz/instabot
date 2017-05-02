#!/usr/bin/env bash

sudo chown -R rawandhawiz:rawandhawiz ..
sudo chown root:root ngrok
python contentuploader.py &
./ngrok http 5000 &