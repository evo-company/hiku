#!/bin/bash
if [[ $(git status hiku -s) ]]; then
    echo "Working directory is not clean"
    false
else
    true
fi
