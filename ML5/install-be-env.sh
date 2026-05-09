#!/bin/bash

# Install Backend dependecies here:

##############################################################################
# Installing Python Pip and library Dependencies
##############################################################################
sudo apt update -y
sudo apt install -y python3-dev python3-setuptools python3-pip mysql-client
sudo -u ubuntu python3 -m pip install pip --upgrade
python3 -m pip install pillow
python3 -m pip install boto3
python3 -m pip install mysql-connector-python

cd /home/ubuntu

# Command to clone your private repo via SSH usign the Private key
####################################################################
# Note - change "hajek.git" to be your private repo name (hawk ID) #
####################################################################
sudo -u ubuntu git clone git@github.com:jonathanparraga/ITMO463-Module5.git

# Start the nodejs app where it is located via PM2
# https://pm2.keymetrics.io/docs/usage/quick-start
cd /home/ubuntu/ITMO463-Module5/M5

echo "Copying ./app.py to /usr/local/bin/..." 
sudo cp ./app.py /usr/local/bin/
echo "Copying ./checkqueue.timer to /etc/systemd/system/..."
sudo cp ./checkqueue.timer /etc/systemd/system/
echo "Copying ./checkqueue.service to /etc/systemd/system/..."
sudo cp ./checkqueue.service /etc/systemd/system/

sudo systemctl daemon-reload							
sudo systemctl enable --now checkqueue.timer
sudo systemctl enable checkqueue.service
