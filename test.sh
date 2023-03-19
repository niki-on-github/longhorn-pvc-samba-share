#!/bin/bash

NAMESPACE=vpn-apps LOG_LEVEL=DEBUG VOLUMES_CONFIG_PATH=./example/storage/config/volumes.yaml python3 -u deploy-samba-server.py
