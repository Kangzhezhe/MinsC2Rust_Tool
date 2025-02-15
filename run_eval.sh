#!/bin/bash

DEFAULT_CONFIG_PATH="Tool_py/configs/config.ini"

if [ "$#" -eq 1 ]; then
    CONFIG_PATH=$1
else
    CONFIG_PATH=$DEFAULT_CONFIG_PATH
    echo "No config path provided. Using default: $CONFIG_PATH"
fi

CONFIG_PATH=$(realpath "$CONFIG_PATH")

cd Tool_py
python3 ./post_process.py "$CONFIG_PATH" --eval-only