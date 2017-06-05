#!/usr/bin/env bash

sudo git pull
sudo rm instabot.db
sudo python db_create.py
sudo service apache2 restart