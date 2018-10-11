#!/bin/bash
CONTAINER_NAME=${COMPOSE_PROJECT_NAME}_gateway_proxy_gen_1

sudo docker start ${CONTAINER_NAME}
sleep 10

# retry
if ! sudo docker ps |grep ${CONTAINER_NAME} > /dev/null; then
    sudo docker start ${CONTAINER_NAME}
fi
