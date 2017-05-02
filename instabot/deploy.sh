#!/usr/bin/env bash

sudo chown rawandhawiz:rawandhawiz .
python contentuploader.py &
./ngrok http 5000 &