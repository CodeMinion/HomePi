#!/usr/bin/expect -f

set prompt "#"
set deviceAddress [lindex $argv 0]
set pinCode [lindex $argv 1]
set btInterfaceAddress [lindex $argv 2]

set timeout 30 

spawn sudo bluetoothctl -a
expect "Agent registered"
expect -re $prompt
send "select $btInterfaceAddress\r"
expect -re $prompt
send "remove $deviceAddress\r"
expect "Device"
expect -re $prompt
send "scan on\r"
send_user "\nScanning\r"
expect "Device $deviceAddress *"
send_user "\nDone scanning\r"
send "scan off\r"
expect "Controller"
send "pair $deviceAddress\r"
expect {
		"Attempting to pair with $deviceAddress" {
			expect {
				"Request PIN code" {
					send "$pinCode\r"
					expect -re $prompt
					send "trust $deviceAddress\r"
					expect "Changing $deviceAddress trust succeeded" 
					expect -re $prompt
					send "quit\r"	
				}
				"Failed to pair:" {
					send "quit\r"
				}
			}
		}
		
		"Device $deviceAddress not available" { 
			send_user "\nDevice Not Found\r"
			send "quit\r"
		}
		
		"Device $deviceAddress not available" { send "quit\r"}
}
expect eof