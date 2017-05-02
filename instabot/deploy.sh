#!/usr/bin/env bash

sudo chown -R rawandhawiz:rawandhawiz ..
python contentuploader.py &
./ngrok http 5000 &