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
# sudo contrab -e
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



# Change to your user home dir.
cd /

# Change to Home Pi root directory. 
# Note: You migh need to change this depending on your location.
cd /home/pi/HomePi

# Run HomePi with your configuration.
# Note: You might want to tweak this for your config file.
sudo screen -m -d ./HomePi.py config_v2

# Go back.
cd /

# We are done.

