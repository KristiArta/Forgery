#!/bin/bash

projects=(
    "notpixel"
)
current_project=""


while true
do
    for project in "${projects[@]}"; do
        current_project=$project
        poetry run python -m scripts.$project.claimer >> scripts/$project/claimer/log.txt 2>&1
    done
done
