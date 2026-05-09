#!/bin/bash

# Install dependecies here:

##############################################################################
# Installing Nginx
##############################################################################
sudo apt update -y
sudo apt install nginx unzip -y

##############################################################################
# Enable and start Nginx service
##############################################################################
sudo systemctl enable nginx
sudo systemctl start nginx

##############################################################################
# Install Node JS
# https://github.com/nodesource/distributions#installation-instructions-deb
##############################################################################
curl -fsSL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh
sudo apt install -y nodejs
node -v
##############################################################################
# Use NPM (node package manager to install AWS JavaScript SDK)
##############################################################################
# Run NPM to install the NPM Node packages needed for the code
# You will start this NodeJS script by executing the command: node app.js
# from the directory where app.js is located. The program `pm2` can be
# used to auto start NodeJS applications (as they don't have a normal
# systemd service handler).
# <https://pm2.keymetrics.io/docs/usage/quick-start/>. This will require
# the install of PM2 via npm as well.
cd /home/ubuntu
sudo -u ubuntu npm install @aws-sdk/client-dynamodb @aws-sdk/client-sqs @aws-sdk/client-s3 @aws-sdk/client-sns express multer multer-s3 uuid ip
sudo npm install pm2 -g

# Command to clone your private repo via SSH usign the Private key
####################################################################
# Note - change "hajek.git" to be your private repo name (hawk ID) #
####################################################################
sudo -u ubuntu git clone git@github.com:jonathanparraga/ITMO463-Module6.git

# Start the nodejs app where it is located via PM2
# https://pm2.keymetrics.io/docs/usage/quick-start
cd /home/ubuntu/ITMO463-Module6

sudo cp /home/ubuntu/ITMO463-Module6/default /etc/nginx/sites-available/default
sudo systemctl daemon-reload
sudo systemctl restart nginx

sudo pm2 start app.js
