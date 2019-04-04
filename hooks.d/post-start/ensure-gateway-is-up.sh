#!/bin/bash
CONTAINER_NAME=${COMPOSE_PROJECT_NAME}_gateway_proxy_gen_1

sudo docker start ${CONTAINER_NAME}
sleep 3

while ! sudo docker ps |grep ${CONTAINER_NAME} > /dev/null; do
    sudo docker start ${CONTAINER_NAME}
    sleep 1
done
