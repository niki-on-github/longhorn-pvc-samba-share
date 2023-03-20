#!/bin/bash

AFFINITY_HOSTNAME=test SVC_SAMBA_IP=127.0.0.1 SAMBA_PASSWORD=test NAMESPACE=vpn-apps LOG_LEVEL=DEBUG VOLUMES_CONFIG_PATH=./example/config/volumes.yaml python3 -u deploy-samba-server.py
