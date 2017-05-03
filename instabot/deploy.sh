#!/usr/bin/env bash

sudo chown -R rawandhawiz:rawandhawiz ..
python contentuploader.py &
ngrok http -log=stdout 5000 > /dev/null &
python ngrokinstances.py