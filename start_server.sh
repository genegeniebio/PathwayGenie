#!/usr/bin/env bash
docker build -t partsgenie .
docker run -d -p $1:5000 partsgenie