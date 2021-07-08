#!/bin/bash

INSTALL_DIR="/usr/local/bin/valence"
SERVICE="valence.service"

sudo systemctl stop $SERVICE
sudo rm /lib/systemd/system/$SERVICE
sudo rm -rf $INSTALL_DIR
sudo systemctl daemon-reload