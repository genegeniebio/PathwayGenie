#!/usr/bin/env bash
docker build -t designgenie .
docker run -d -p $1:5000 designgenie