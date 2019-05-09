#!/usr/bin/expect -f

set prompt "#"
set deviceAddress [lindex $argv 0]
set pinCode [lindex $argv 1]
set btInterfaceAddress [lindex $argv 2]

spawn sudo bluetoothctl -a
expect -re $prompt
send "select $btInterfaceAddress\r"
sleep 1
#expect -re $prompt
#send "remove $address\r"
#sleep 1
expect -re $prompt
send "scan on\r"
send_user "\nSleeping\r"
sleep 5
send_user "\nDone sleeping\r"
send "scan off\r"
expect "Controller"
send "trust $deviceAddress\r"
sleep 2
send "pair $deviceAddress\r"
sleep 4
send "$pinCode\r"
sleep 3
send_user "\nShould be paired now.\r"
send "quit\r"
expect eof