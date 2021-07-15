#!/bin/bash

INSTALL_DIR="/usr/local/bin/valence"
SERVICE="valence.service"

echo "[*] Running service: $SERVICE"

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
sudo cp -r templates $INSTALL_DIR
sudo cp -r static $INSTALL_DIR
sudo cp $SERVICE /lib/systemd/system/$SERVICE
echo "[*] Reloading systenctl"
sudo systemctl daemon-reload
echo "[*] Enabling $SERVICE"
sudo systemctl enable $SERVICE
echo "[*] Starting $SERVICE"
sudo systemctl start $SERVICE
echo "[*] Checking $SERVICE status"
systemctl status $SERVICE
exit 0