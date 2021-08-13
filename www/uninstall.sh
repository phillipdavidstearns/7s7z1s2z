#!/bin/bash

INSTALL_DIR="/usr/local/bin/7s7z1s2z/"
SERVICE_DIR="/lib/systemd/system/"
SERVICE="7s7z1s2z.service"
SHUTDOWN_SERVICE="7s7z1s2z_shutdown.service"

sudo systemctl stop $SHUTDOWN_SERVICE
sudo systemctl disable $SHUTDOWN_SERVICE
sudo rm $SERVICE_DIR$SHUTDOWN_SERVICE
sudo systemctl stop $SERVICE
sudo systemctl disable $SERVICE
sudo rm $SERVICE_DIR$SERVICE
sudo rm -rf $INSTALL_DIR
sudo systemctl daemon-reload