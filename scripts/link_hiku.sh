#!/bin/bash

if [ "$1" == '-d' ]; then
  echo "unlinking hiku from repos"
  rm -rf ../uaprom/hiku
  exit 1
fi

echo "linking hiku to uaprom"
rm -rf ../uaprom/hiku
cp -r hiku ../uaprom/hiku