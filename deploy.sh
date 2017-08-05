#!/usr/bin/env bash

sudo git pull
sudo rm instabot.db
python db_create.py
sudo chmod 664 instabot.db
sudo cp instabot.conf /etc/apache2/sites-available/
sudo a2ensite instabot.conf
sudo service apache2 restart