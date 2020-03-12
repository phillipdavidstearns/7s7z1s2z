# Pololu Dual G2 High-Power Motor Driver 18v22

Previous version of this piece used an arduino mega. Code was written in C++ for Arduino using the standard IDE. This version of the piece will use a raspberry pi to control the motors.

## Resources:

* [Python library for the Pololu Dual G2 High-Power Motor Drivers for Raspberry Pi](https://github.com/pololu/dual-g2-high-power-motor-driver-rpi)

## Process:

1. Install pigpiod: `sudo apt install python3-pigpio python-pigpio`
1. Enable `pigpiod` daemon: `sudo systemctl enable pigpiod`
1. Start the `pigpiod` service: `sudo systemctl start pigpiod`
1. Clone the Pololu driver repo: `git clone https://github.com/pololu/dual-g2-high-power-motor-driver-rpi`
1. Change into the cloned repo directory: `cd dual-g2-high-power-motor-driver-rpi`
1. Run the install script: `sudo python setup.py install`