#!/bin/sh
# Script: home_pi_boot.sh
# Purpose: Helper script to launch an instance of Home Pi after rebooting
# the Raspberry Pi. Nice helper for when things go south, just power cycle.
#
# Required:
# Make sure you have the poGlow libraries installed or HomePi won't run.
#
# Setup Steps:
# 1 - Make exucutable 
# chmod 755 home_pi_boot.sh
#
# 2 - Add to crontb 
# sudo crontab -e
# @reboot sh path_to_this scrip
# 
# Ex. @reboot sudo sh /home/pi/HomePi/home_pi_boot.sh > /home/pi/HomePi/cronlogs 2>&1
#
# 3 - Save changes
# Ctrl-O
#
# 4 - Exit
# Ctrl-X
#
# 5 - Reboot
# sudo reboot
#

# Start bluetooth.
sudo /etc/init.d/bluetooth restart

# Sleep for now to give the interface time to load.
# Need a better way to do this.
sleep 15

# Make HomePi discoverable.
sudo hciconfig hci0 piscan

# Change to your user home dir.
cd /

# Change to Home Pi root directory. 
# Note: You migh need to change this depending on your location.
cd /home/pi/HomePi

# Run HomePi with your configuration.
# Note: You might want to tweak this for your config file.
sudo screen -m -d ./HomePi.py /boot/home_pi_config 

# Go back.
cd /

# We are done.

