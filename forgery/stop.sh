#!/bin/bash

killall background.sh
pkill -15 -f ".*python -m scripts.*"
