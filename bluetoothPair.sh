#!/usr/bin/expect -f

set prompt "#"
set deviceAddress [lindex $argv 0]
set pinCode [lindex $argv 1]
set btInterfaceAddress [lindex $argv 2]

set timout 30 # Wait as much as 30 seconds for a response.

spawn sudo bluetoothctl -a
expect -re $prompt
send "select $btInterfaceAddress\r"
sleep 1
expect -re $prompt
send "remove $deviceAddress\r"
sleep 1
expect -re $prompt
send "scan on\r"
send_user "\nScanning\r"
expect "Device $deviceAddress *"
send_user "\nDone scanning\r"
send "scan off\r"
expect "Controller"
send "trust $deviceAddress\r"
expect {
	"Changing $deviceAddress trust succeeded" { 
		send "pair $deviceAddress\r"
		expect {
				"Request PIN code" { 
					send "$pinCode\r" 
					send "quit\r"

				}
				"Device $deviceAddress not available" { 
					send_user "\nDevice Not Found\r"
					send "quit\r"
				}
		}
	}
	"*" { send "quit\r"}
}
expect eof