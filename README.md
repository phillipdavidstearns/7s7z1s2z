<span id="top"></span>
# 7s7z1s2z Guide

* [Startup and Shutdown](#startup-and-shutdown) - Day to Day Operation
* [Hardware Overview](#hardware-overview) - To get familiar with the parts and terminology
* [Hardware Setup](#hardware-setup) - How everything is put together
* [Software Overview](#software-overview) - Under the hood a little
* [Using the Web Application](#using-the-web-application) - Connecting, controlling and making changes to settings
* [Troubleshooting](#troubleshooting) - Common things that might go wrong
* [Resources](#additional-resources) - Notes and other things

<span id="startup-and-shutdown"></span>
## Startup and Shutdown Procedure [(top)](#top)

### Startup

1. Complete the [Hardware Setup](#hardware-setup) portion of this guide.
1. Plug the installation to power it on.
1. Wait for it to boot.
1. Connect to the same network the installation is connected to.
1. In a web browser (will not work on mobile), navigate to: `https://7s7z1s2z.local`
1. Log in using supplied credentials.
1. Click `ON` in the "Pump:" section.
1. Load the installation with liquid soap.
1. Click `RESUME` or `OPEN` in the "Go To:" section.
1. Click `logout`
 
### Shutdown

1. Connect to the same network the installation is connected to.
1. In a web browser (will not work on mobile), navigate to: `https://7s7z1s2z.local`
1. Log in using supplied credentials.
1. Click `CLOSE & HOLD` in the "Go To:" section
1. Drain the liquid soap from the installation.
1. Click `OFF` in the "Pump:" section
1. Click `logout` 

<span id="hardware-overview"></span>
## Hardware Overview [(top)](#top)

![](images/HardwareOverview.jpg)

### Components:

* [12V 29A DC power supply by Mean Well (LRS-350-12)](https://www.meanwell.com/productPdf.aspx?i=459)
* [Raspberry Pi4B Single Board Computer](https://www.raspberrypi.org/products/raspberry-pi-4-model-b/)
* [Pololu Dual G2 High-Power Motor Driver 18v22 for Raspberry Pi](https://www.pololu.com/product/3754)
* 2x [131:1 Metal Gearmotor 37Dx73L mm 12V with 64 CPR Encoder (Helical Pinion)](https://www.pololu.com/product/4756)
* Pump Motor
* Custom PCB with terminal blocks for connecting motors and PWM variable speed motor driver
* Black Acrylic Base
* Various standoffs and screws

**Note:** Motor enclosure dimensions 4.5" diameter, 5.25" length, hole 1.5"x9/32" 1.5" from the back.

* 7' cable for each 
* Grey if possible

<span id="hardware-setup"></span>
## Hardware Setup [(top)](#top)

**NOTE: Before wiring up the installation, complete these steps and proceed to the [Using the Web Application](#using-the-web-application) to test that everything is wired properly and running smoothly**

![](images/Tools.jpg)

Before starting, make sure that all connection to VAC 120 mains power are disconnected.

* Mount `Power Supply` to Base
* Mount `Raspberry Pi` standoffs to base

![](images/PiStandoffs.jpg)

* Insert pre-formatted `SD Card` into `Raspberry Pi`

![](images/SDCard.jpg)

* Mount `Raspberry Pi` to standoffs and fasten using standoffs for the `Motor Driver Shield`.

![](images/PiMount.jpg)

* Fit Motor `Driver Shield` on `Raspberry Pi` GPIO header pins and fasten with screws.

![](images/DriverMount.jpg)

* Fit the Custom PCB on the `Driver Shield` taking care to align ALL header pins with ALL header holes. Press firmly in place.

![](images/PCBMount.jpg)

* Connect `Green (-)` and `Blue (+)` wires from the `Driver Shield` to the corresponding 2-connection `Terminal Block`. Screw tight with precision flat head screw driver and tug gently to ensure they're secure.

![](images/PCBPower.jpg)

* Connect the `Red (+)` and `Clear (-)` wires from the `Driver Shield` to the `VM` and `GROUND (Symbol)` terminal block.
* Connect the `Gear Motors`, M1 and M2, the their corresponding terminal blocks using the following pinout:

**NOTE: Be sure to strip, tin, and trim wires (if necessary) so that they can be cleanly inserted and secured into the terminal blocks**

1. Strip insulation off the ends
1. Twist the conductors to make a tight bundle
1. Tin conductors with solder
1. Trim conductors to ~2mm
1. Open terminal block completely with screw driver by screwing CCW (should hear/feel a slight click when end is reached) 
1. Insert tinned and trimmed wire ends into the terminal block. (Leave no conductor material exposed)
1. Close the block with screw driver by screwing CW until tight
1. Give a gentle tug to ensure the connection is secure

**NOTE: The Color of the wires no longer matches the labels on the terminal blocks. Please refer to the table below to match existing wire colors to their proper terminals. Contact the Technical Lead for clarification.**

```
Motor Wire Color Code:

==============================================
POWER (Black 2-conductor)
----------------------------------------------
Wire Color		Function		Terminal Block
----------------------------------------------
Black (ribbed)	Motor +V		Motor Driver 1/2+
Black (smooth)	Motor GND		Motor Driver 1/2-

==============================================
ENCODER (Grey 4-conductor)
----------------------------------------------
Wire Color		Function		Terminal Block
----------------------------------------------
Black			Encoder GND		PCB G
Red				Encoder +5V		PCB B
Yellow			Encoder 1		PCB Y
White			Encoder 2		PCB W
```

* Connect the `Pump Motor` to `M+` and `M-` terminal blocks for the Pump motor.

![](images/PCBOverview.jpg)

11. Connect the `V+` and `V-` on the `Power Supply` to the corresponding `V+` and `V-` terminals on the `Driver Shield`

**NOTE: Ensure that the top PCB is seated properly in the header socket below by gently pressing down along the top edge. Do this after making any adjustments to the wiring or (re)positioning of the board**

![](images/DriverShieldPowerTerminals.jpg)

12. Connect ~120 VAC power to the `Power Supply` using the following chart:

```
~120 VAC Wire Color Code:
==============================================
Color			Function	Terminal Block
----------------------------------------------
Black			Line		L
White			Neutral		N
Green			Ground		GND (symbol)
```

![](images/PowerSupply.jpg)

1. **Double check that ALL connections are correct!**
2. Connect the power supply to mains power when ready to proceed to testing and configuration.

<span id="software-overview"></span>
## Software Overview [(top)](#top)

### Components

* Debian Linux RaspiOS
* Wireguard VPN
* Main 7s7z1s2z `server.py` script
	* `MotorControl` python class defined in `motor_control.py`
		* `Decoder` class defined in `rotary_encoder.py`
	* Tornado Web Application
		* Assets located in `static/` and `template/` directories
* Install and uninstall bash scripts.
* `systemd` unit descriptor for `7s7z1s2z.service`
* `systemd` unit descriptor for `7s7z1s2z_shutdown.service`

### Python Dependencies

* Python3.7
* packages: `python3-pigpio`, `python3-tornado`
* drivers: [https://github.com/pololu/dual-g2-high-power-motor-driver-rpi](https://github.com/pololu/dual-g2-high-power-motor-driver-rpi)

### RaspiOS

* Web Application is located at `https://7s7z1s2z.local` when accessing from the same network. Does not need the internet to run, but internet is required for remote management.
* Wireguard VPN permits secure remote access as long as the Raspberry Pi is connected to the internet.
* Password Login is Enabled for `ssh` user `membrane`
* `ssh` login by key is also possible locally and remotely
* `systemd` is used to manage the startup and shutdown of the software running the sculpture via `7s7z1s2z.service`.

### Wireguard VPN

* Used to create an encrypted tunnel for remote access. Requires that my Virtual Private Server is up and that the Wireguard VPN Server is running.
* VPN IP Address: `10.42.0.100`
* Custom `wg_setup.sh` scripts used by `wg_setup@.service` to manage VPN interface. Configuration and environment files are located in `/etc/wireguard/`

### Main `server.py` Script

* Executed by `7s7z1s2z.service` at boot.
* Creates and instance of `MotorController` and `Tornado Web Application` server. 
* The HTTP(S) server is managed by Tornado's IOLoop.
* The `MotorController` instance runs in a separate thread. Full asynchronous management `asyncio` is a place where the code and be optimized in the future.

### MotorController Class

Provides all the resources necessary to control the main gear head motors and the pump motor

* dependencies: Custom modified `Decoder` class from `rotary_encoder.py`, and `dual_g2_hpmd_rpi` module provided by Pololu.
* Runs in a thread separate from the main `server.py` thread.
* Asynchronously handles WebSocket messages

### Tornado Web Application

* Requires authentication
* Requires the javascript be enabled
* Uses self-signed SSL certificates to achieve a secure encrypted HTTPS connection, which may cause mobile devices to reject attempts to create a web socket connection.
* Uses WebSockets to pass data between the browser and the application
* Displays current status, updated every second
* Displays WebSocket connection status
* Interface for changing the state of the sculpture, updating parameters/settings with session store/recall/apply, and load/write defaults.
* Components:
	* `static/favicon.ico` - cute icon for the browser tab
	* `templates/login.html` - login page
	* `templates/index.html` - main control panel page
	* `static/jquery-3.5.1.min.js` - simplified javascript access/control of DOM elements
	* `static/style.css` - CSS styling of elements
	* `static/ws-client.js` - WebSocket
	* `static/Fira_Mono/` - font
* Sets routes for about resources.
* Defines which actions to be handled and how.
* Creates and manages the `MotorController` instance.

### Management Scripts

* `install.sh` - use for fresh install
* `uninstall.sh` - removes all install components

<span id="using-the-web-application"></span>
## Using the Web Application [(top)](#top)

* [Connecting](#connect)
* [Login](#login)
* [Control Panel](#control-panel)
	* [Current Status](#current-status)
	* [Change Settings](#change-settings)
	* [Saving and Loading Settings](#saving-and-loading-settings)

<span id="connect"></span>
### Connecting

1. Ethernet connection can be used to access the device locally. Simply connect an ethernet cable between the Raspberry Pi 4 and your device (laptop/desktop required). This method is recommended when setting up for the first time.
2. Ethernet should be used to connect to the museum network. Ensure that the ethernet connection is on the same subnet as the WiFi network OR is given an IP address that is accessible from the museum WiFi (non-public/staff only).
3. WiFi can be configured to connect to the museum WiFi network. In which case, stuff wishing to access the device must be connected to the same network.

<span id="login"></span>
### Login

* Navigate to `https://7s7z1s2z.local`

![](images/browser.png)

* You will likely see a warning from your browser that the certificate is invalid. Make an exception to access the page using the options provided by your browser.

![](images/Login.png)

* Login is required. Sessions expire after 1 day.
* Failed login returns to the login page, no status is displayed.
* Successful login loads the `Control Panel`.

<span id="control-panel"></span>
### Control Panel

![](images/ControlPanel.png)

* `Current Settings & Status` - This section relies on websockets to poll and update the values seen here. They are a reflection of the current parameters governing the behaviors of the installation.
* `Change Settings` section relies on websockets to push values entered here to the installation.
* `logout` ends the session and requires the user to log back in again. Sessions are valid only for 24 hours. Logging out at the end of each session is highly recommended to ensure security for the safety of the sculpture and visitors.
*  `Websocket status:` indicates whether the sculpture is connected to the `7s7z1s2z Control Panel` web page. `Current Status` and `Change Settings` require the status to be `Connected`


<span id="current-status"></span>
#### Current Status

Displays the current status of the sculpture and the settings currently running.

* `Machine State` and `Last Machine State`:
	* `STOPPED` - Indicates that the `!! EMERGENCY STOP !!` has been pushed.
	* `STARTUP` - Indicates whether the control program has just been started.
	* `OPENING` - Sculpture is in the process of opening.
	* `HOLDING OPEN` - Sculpture is open and holding open.
	* `CLOSING` - Sculpture is in the process of closing.
	* `HOLDING CLOSE` - Sculpture is closed and holding closed.
	* `PAUSED` - Sculpture movement has been suspended by the user.
	* Notes: Machine State is the CURRENT state and Last State was the state the sculpture was in when the user pressed `PAUSE` or `STOP`. States progress in order with OPENING following the completion of HOLDING CLOSED.
* `Motor Power`: Value applied to the Driver Shield, min/max range -480/480. (float)
* `Motor Position`: Encoder event count. 8400/rev (int)
* `Motor Speed`: Encoder Events / Loop Delay
* `Motor Flipped`: Whether the motor direction is reversed (boolean)
* `Motor Offset`: Offset Motor Position by N counts (int)
* `Pump Speed`: Current speed setting for the pump motor (float)
* `Current Time`: seconds since linux epoch (float)
* `State End Time`: time when the current machineState should complete (float)
* `Durations`: time in seconds for how long each machine state should take to complete. (float)
	* `Startup Duration`: How long the pump is given a chance to coat the cables in liquid soap.
	* `Open Duration`: amount of time it takes to move from CLOSED to OPEN.
	* `Open Hold Duration`: amount of time to hold the sculpture open (HOLDING OPEN).
	* `Close Duration`: amount of time it takes to move from OPEN to CLOSED.
	* `Close Hold Duration`: amount of time to hold the sculpture closed (HOLDING CLOSED).
* `Target Open`: Open position expressed as encoder event counts (int)
* `Target Close`: Closed position expressed as encoder event counts (int)
*  `Target`: The position the motors are aiming for. This changes based on the progression through each machine state.
*  `Progress`: 0.0 = closed, 1.0 = open
*  `Sigmoid Function`: The currently selected motion smoothing function.
*  `Loop Delay`: Interval between triggering of the main `MotorController` `motionControl` method. (float)

<span id="change-settings"></span>
#### Change Settings

* `Go To:` - Clicking buttons immediately change the state of the sculpture. Totally safe to do whenever. 
	* `OPEN`: opens the sculpture. keeps running without pause. (can be used to start the installation)
	* `CLOSE`: closes the sculpture keeps running without pause.
	* `OPEN & HOLD`: opens the sculpture then pauses.
	* `CLOSE & HOLD`: closes the sculpture then pauses.
	* `PAUSE`: pauses progress in any state. 
	* `RESUME`: resumes progress of the `PAUSED` or `STOPPED` (can be used to start the installation).

* `!! EMERGENCY STOP !!`
	* Issues a command to the MotorController to set motor power to 0.0 and the pump power to 0.0 (hard pause)
	* Can be exited by clicking `RESUME` only.
	* **NOTE: This feature was put in place in the event that the motors begin to spin erratically. It may not work under certain circumstances and power may need to be disconnected. It's recommended to have the sculpture on a dedicated breaker or switch that is easily accessible.**

***

Changes to the settings below cannot be performed when the installation is moving. Best practice is to click either `OPEN & HOLD` or `CLOSE & HOLD` and wait for the "Machine State" to reach `PAUSED`.

**Note: It is possible to edit the parameters below without applying.**

* `Motor Flipped` - checkbox to flip the direction of each motor (boolean)
* `Motor Offset` - number input to set the offset values for each motor (int)
	* Use `set` buttons to push the values to the sculpture (`Apply Settings` no longer works here)
	* Use `apply offsets` when the offsets achieve the desired balance between sides
* `Durations` - number inputs to set the durations for each state (int). Cannot be negative!!!
* `Targets` - number inputs to set the OPEN and CLOSE positions (int)
* `Sigmoid Function` - select input to choose a motion smoothing algorithm. Controls the easing of the motor out of closed and into open positions.
* `Power Multiplier` - Power is determined by distance from target. Multiplier scales the effect of being off target. 1 peans there is a 1:1 distance to power relationship. Increase if motors hesitate 
* `Power Easing` - gradually applies power changes based on this percentage. 1.0 for no easing. lowest recommended easing value is 0.125. If the powers are over shooting, reduce value. If the motors are pulsing, increased value.
* `Power Limit` - hard limits the power sent to the motors. Increase only if motors are struggling. 480 is the max.
* `Loop Delay`- controls the timing of the `MotionController` `motionControl` loop. Adjust to smaller value if motion stutters in a rapid pulse or is jerky/jittery. Adjust upwards to free up system resources. Ideally this should not need to be changed.

* Click `Apply Settings` to push the above settings to the sculpture

<span id="saving-and-loading-settings"></span>
#### Saving and Loading Settings

* `Apply Settings`:
	* Pushes values in `Change Settings` fields to the `MotorController`, which should translate over to the `Current Status`
* `Save Applied/Current Settings`:
	* Temporarily saves the current settings running on the `MotorController` to be recalled later in the same session.
* `Load Last Saved Settings`:
	* Loads the previously saved settings from the current session into the `Change Settings` fields. Click `Apply Settings` to push to the `MotorController`. Think of the above two steps as a multi-step undo.
* `Load Default Settings`:
	* Loads the `Default Settings` from disk into the `Change Settings` fields. Click `Apply Settings` to push to the `MotorController`.
* `Write Applied/Current Settings to Default`: 
	* Writes the current applied settings running on the `Motor Controller` to disk. The sculpture will use these settings when it is restarted.
	* **NOTE: Make sure that motor offsets have been applied and are zeroed out in the "Current Settings & Status" column.**

<span id="troubleshooting"></span>
## Troubleshooting [(top)](#top)

### 1. Motors spin erratically

1. 

### 2. Pump motor doesn't spin

1. 

<span id="additional-resources"></span>
## Additional Resources [(top)](#top)

### Pololu Dual G2 High-Power Motor Driver 18v22

Previous version of this piece used an arduino mega. Code was written in C++ for Arduino using the standard IDE. This version of the piece will use a raspberry pi to control the motors.

#### Resources:

* [Python library for the Pololu Dual G2 High-Power Motor Drivers for Raspberry Pi](https://github.com/pololu/dual-g2-high-power-motor-driver-rpi)

#### Process:

1. Install pigpiod: `sudo apt install python3-pigpio python-pigpio`
1. Enable `pigpiod` daemon: `sudo systemctl enable pigpiod`
1. Start the `pigpiod` service: `sudo systemctl start pigpiod`
1. Clone the Pololu driver repo: `git clone https://github.com/pololu/dual-g2-high-power-motor-driver-rpi`
1. Change into the cloned repo directory: `cd dual-g2-high-power-motor-driver-rpi`
1. Run the install script: `sudo python setup.py install