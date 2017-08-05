#!/usr/bin/env bash

sudo git pull
sudo rm instabot.db
python db_create.py
sudo chmod 664 /
sudo chmod 664 instabot.db
sudo service apache2 restart