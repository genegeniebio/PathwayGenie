#!/usr/bin/env bash
docker build -t partsgenie .
docker run -d -p 80:80 partsgenie