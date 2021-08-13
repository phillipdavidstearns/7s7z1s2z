#!/bin/bash

INSTALL_DIR="/usr/local/bin/7s7z1s2z/"
SERVICE_DIR="/lib/systemd/system/"
SERVICE="7s7z1s2z.service"
SHUTDOWN_SERVICE="7s7z1s2z_shutdown.service"

echo "[*] Checking for previously installed files"

if sudo systemctl -a | grep $SERVICE >/dev/null 2>&1;then
	echo "[*] Stopping $SERVICE"
	sudo systemctl stop $SERVICE
fi

if [ -d $INSTALL_DIR ];then
	echo "[+] $INSTALL_DIR exists."
else
	echo "[*] Creating $INSTALL_DIR"
	sudo mkdir $INSTALL_DIR
fi

echo "[*] Copying files into $INSTALL_DIR"
sudo cp server.py $INSTALL_DIR
sudo chmod +x server.py
sudo cp motor_controller.py $INSTALL_DIR
sudo cp rotary_encoder.py $INSTALL_DIR
sudo cp default_settings.json $INSTALL_DIR
sudo cp -r templates $INSTALL_DIR
sudo cp -r static $INSTALL_DIR
echo "[*] Copying $SHUTDOWN_SERVICE and $SERVICE into $SERVICE_DIR"
sudo cp $SHUTDOWN_SERVICE $SERVICE_DIR$SHUTDOWN_SERVICE
sudo cp $SERVICE $SERVICE_DIR$SERVICE
echo "[*] Reloading systenctl"
sudo systemctl daemon-reload
echo "[*] Enabling $SHUTDOWN_SERVICE"
sudo systemctl enable $SHUTDOWN_SERVICE
echo "[*] Starting $SHUTDOWN_SERVICE"
sudo systemctl start $SHUTDOWN_SERVICE
echo "[*] Checking $SHUTDOWN_SERVICE status"
systemctl status $SERVICE
echo "[*] Enabling $SERVICE"
sudo systemctl enable $SERVICE
echo "[*] Starting $SERVICE"
sudo systemctl start $SERVICE
echo "[*] Checking $SERVICE status"
systemctl status $SERVICE
exit 0