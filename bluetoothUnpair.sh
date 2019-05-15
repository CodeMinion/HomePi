#!/usr/bin/expect -f

set prompt "#"
set deviceAddress [lindex $argv 0]
set pinCode [lindex $argv 1]
set btInterfaceAddress [lindex $argv 2]

set timeout 60 

spawn sudo bluetoothctl -a
expect "Agent registered"
expect -re $prompt
send "select $btInterfaceAddress\r"
expect -re $prompt
send "remove $deviceAddress\r"
expect "Device"
expect -re $prompt
send "quit\r"	
expect eof