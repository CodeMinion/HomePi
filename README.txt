HomePi Setup - Software
- sudo apt-get update
- sudo apt-get install bluetooth

Note: There seems to be an issue with the gatttool, so we need to build a newer version of bluez and copy the latest version of gatttools from it.

- sudo apt-get install libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev

Download Bluez
- sudo mkdir bluez
- cd bluez
- sudo wget www.kernel.org/pub/linux/bluetooth/bluez-5.28.tar.xz

Unzip and Compile Bluez
- sudo unxz bluez-5.28.tar.xz
- sudo tar xvf bluez-5.28.tar
- cd bluez-5.28
- sudo ./configure --disable-systemd
- sudo make

Copy gatttool
- sudo cp attrib/gatttool /usr/bin/

Bluetooth tends to hang on accept, in order to prevent this we need to modify the main.conf file
- sudo vim /etc/bluetooth/main.conf

Enter the following line
- DisablePlugins = pnat

Restart bluetooth service.
- sudo invoke-rc.d bluetooth restart

Install Pexpect to allow HomePi interpreters to communicate with BLE devices. See ColorificBulbInterpreter.py for an example.
- sudo apt-get install git build-essential python-dev python-pip python-bluetooth
- sudo pip install pexpect

Download HomePi into your Raspberry Pi.
- cd ~ 
- git clone https://github.com/CodeMinion/HomePi

Make the main HomePi script executable
- cd HomePi
- chmod 755 HomePi.py


Make HomePi Raspberry discoverable. 
- sudo hciconfig hci0 piscan

Before running HomePi you might have to Pair your devices with it.
- sudo vim /usr/bin/bluez-simple-agent

In line 92 replace 'KeyboardDisplay' by 'DisplayYesNo' then save your changes.
- :qw

Pair with phone/table
- sudo bluez-simple-agent hci0 30:85:A9:51:D3:06
- sudo bluez-test-device trusted 30:85:A9:51:D3:06 yes

Restart bluetooth service.
- sudo invoke-rc.d bluetooth restart

Note: If the HomePi is also connecting to other bluetooth devices you might need to 
pair those too.

Run HomePi
- ./HomePi.py config_file_path

HomePi Setup - Hardware
1 x Raspberry Pi 2 (https://www.adafruit.com/product/2358)
2 x Bluetooth Dongles (http://www.adafruit.com/product/1327)

Note: I encountered the issue that after my Raspberry Pi had loaded an connected two bluetooth devices it would stop accepting connections from the mobile app. Currently I am dealing with this issue by having two dongles in the Raspberry Pi, one for connecting to the devices (clients dongle), and one two listen for incoming connections from the mobile apps. I purchased my bluetooth module from (http://www.adafruit.com/product/1327) and all came with the exact same MAC address which meant I didn't need to perform any additional settings. If you have two different MACs for your modules make sure to specify their addresses in the config file for the HomePi. 

About the Config File:
- The HomePi connects to a series of devices specified by you and makes them available. These devices are specified in the config file that is used at run time by the HomePi. The config file must be in JSON format. For examples of config files I have included two in this release. 

About the Interpreters:
- The HomePi has no specific knowledge about the kinds of devices it connects to. The job of the HomePi is to stablish connections with this devices, expose them to the client apps and pass any commands received to the specified device. Aside from that the HomePi is oblivious of how the devices operate. This job is left to the Interpreters. The interpreters behave just like drivers do, they are in change of translating the requests received into something that is understood by the device. For what methods must be implemented by your interpreter refer interpreters/InterpreterTemplate.py. All interpreters must be placed in the interpreter folder because the HomePi will instantiate them from there. 

About controlling your Home Pi:
- Simply download the Home Pi Remote App from the Google Play store. (https://play.google.com/store/apps/details?id=codeminion.homepimote )

About Home Pi:
- The Home Pi was inspired by the tutorial at Adafuit.com (https://learn.adafruit.com/reverse-engineering-a-bluetooth-low-energy-light-bulb/control-with-bluez).
I also wanted to be able to control all my BLE and Bluetooth devices from a single application. One of the nice outcomes from the Home Pi is that I am not required to have a mobile device with Bluetooth 4.0 in order to interact with the light bulbs or other BLE devices. Since the devices connect to the Raspberry Pi, only it needs to support Bluetooth 4.0 and all my mobile devices can just connect to the Pi.

Supported Devices (Interpreters)
- Colorific Bulb (ColorificBulbInterpreter.py)
- Roysben Bulb (RoybensBleBulbInterpreter.py)
- BlueMote (BlueMoteInterpreter.py) - (https://github.com/CodeMinion/BlueMoteServer)
- MoteDuino (MoteDuinoInterpreter.py) - (https://github.com/CodeMinion/MoteDuinoServer)
- LegaMote (LegaMoteInterpreter.py) - (https://github.com/CodeMinion/LegaMoteServer)
 bpoint Bluetooth Outlet (BPointInterpreter)

In order to add support for more bulbs or devices, just add a new interpreter. If you make your own interpreter feel free to let me know and I'll add it to the list.    

Keep HomePi running after Disconnect:
- sudo apt-get install screen
- screen ./HomePi.py config_file_path


Creating your own Interpreters
In order to create an interpreter for your bulb or BLE devices you will need to get the following:
- BLE Bulb or device you want to create the interpreter for.
- BLE Sniffer (I Used https://www.adafruit.com/products/2269)
- The official app that controls your bulb. 

Adafruit has a nice tutorial on sniffing BLE packets (https://learn.adafruit.com/introducing-the-adafruit-bluefruit-le-sniffer) 

My Approach:
- Change color to red and record Handle and Value from Wireshark.
- Change color to blue and record Handle and Value from Wireshark. 
- Change color to green and record Handle and Value from Wireshark.
- Change Brightness to 100 and record Handle and Value from Wireshark. 
- Change Brightness to 0 (or as close to it) and record Handle and Value from Wireshark. 

That should give you all the information you need to create your interpreter. For light bulbs the commands that the HomePi receives are:
Color: R,G,B (Range: 0-255)
Dim: Value (Range: 0-255)
Power: Value (Range: 0/1)

Note: You can always check out any of the bulb interpreters for a better idea.

Pairing with Bluetooth Module (HC-06)
It seems that in order to pair with the module from the Raspberry Pi you need to run the following commands (as root):
1 - sudo echo "XX:XX:XX:XX:XX:XX 1234" >> /var/lib/bluetooth/YY:YY:YY:YY:YY:YY/pincodes
(Where XX represent the address of the BT module and YY represents the address of the dongle attached to the Raspberry pi, just press Tab after /var/lib/bluetooth/ to autocomple this)
2 -  echo 1234 | bluez-simple-agent hci0 XX:XX:XX:XX:XX:XX
3 -  bluez-test-device trusted XX:XX:XX:XX:XX:XX yes
After this you should be able to connect.

LegaMote Config:
For LegaMote the config interpretation was extend to allow naming of the switches as well as having a unique name show in the control screen. Format is as follows.
userId: "(name to show in main screen)/(name of 1st switch)/(name of 2nd switch)/(and so on..)"
See config files for concrete examples.

PiGlow:
Integrated with Home Pi with Pimoroni's PiGlow for some visible feedback.

Installing PiGlow:
- curl get.pimoroni.com/piglow | bash

Language:
RED    - Performing Home Pi clean up.
ORANGE - Performing Home Pi configuration. 
YELLOW - Performing connection to configured devices.
BLUE   - Ready!

Start HomePi at Boot:
Created home_pi_boot.sh to allow the HomePi to be configured to start after Raspberry Pi boots.
Follow instructions inside the script for setup. 
     
