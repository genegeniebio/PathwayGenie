#!/usr/bin/env bash
docker build -t pathwaygenie .
docker run -d -p 80:80 pathwaygenie