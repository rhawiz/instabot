#!/usr/bin/env bash

sudo git pull
sudo pip install -r requirements.txt
sudo rm instabot.db
python db_create.py
sudo chmod 664 instabot.db
sudo pip install gunicorn
gunicorn -b 0.0.0.0:80 -b unix:instabot.sock app:app