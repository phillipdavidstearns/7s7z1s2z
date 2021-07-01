#!/bin/bash

sudo systemctl stop rover.service
sudo rm -rf /usr/local/bin/rover
sudo rm /lib/systemd/system/rover.service
sudo chmod +x server.py
sudo mkdir /usr/local/bin/rover
sudo cp server.py /usr/local/bin/rover/
sudo cp -r templates /usr/local/bin/rover/
sudo cp -r static /usr/local/bin/rover/
sudo cp rover.service /lib/systemd/system/rover.service
sudo systemctl daemon-reload
sudo systemctl start rover.service
systemctl status rover.service