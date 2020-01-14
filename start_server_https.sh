#!/usr/bin/env bash

rm -rf certs
mkdir certs

docker build -t partsgenie .

docker build -t nginx-proxy-unrestricted .

docker run  -d -p 80:80 -p 443:443  \
    --name nginx-proxy-unrestricted \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    -v certs:/etc/nginx/certs:ro \
    -v /etc/nginx/vhost.d \
    -v /usr/share/nginx/html \
    --label com.github.jrcs.letsencrypt_nginx_proxy_companion.nginx_proxy=true \
    nginx-proxy-unrestricted

docker run -d \
    --name nginx-letsencrypt \
    --volumes-from nginx-proxy-unrestricted \
    -v certs:/etc/nginx/certs:rw \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    jrcs/letsencrypt-nginx-proxy-companion

docker run --name pathwaygenie -d -p :5000 \
    -e VIRTUAL_HOST=parts.genemill.liv.ac.uk \
    -e LETSENCRYPT_EMAIL=neil.swainston@liverpool.ac.uk \
    -e LETSENCRYPT_HOST=parts.genemill.liv.ac.uk \
    partsgenie