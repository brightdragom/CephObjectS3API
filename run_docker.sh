#!/bin/bash

read -p 'Please enter the image(ceph-api-back) tag: ' img

docker build -t ceph-api-back:$img -f Dockerfile .
#docker run -it --rm -p 5000:5000 -e AWS_ACCESS_KEY_ID=$key_id -e AWS_SECRET_ACCESS_KEY=$secret_key -e BUCKET_HOST=$host -e BUCKET_PORT=$port $img
docker run -it --rm -p 5000:5000 --env-file config.env ceph-api-back:$img
