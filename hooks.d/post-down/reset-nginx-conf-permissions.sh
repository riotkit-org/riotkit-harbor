#!/bin/bash

if [[ -d ./containers/nginx/vhost.d ]]; then
    echo " .. Resetting permissions on ./containers/nginx/vhost.d"
    sudo chown ${APP_USER} ./containers/nginx/vhost.d

    if [[ "${IS_DEBUG_ENVIRONMENT}" != "1" ]]; then
        echo "   > Resetting nginx files on production"

        for file in ./containers/nginx/vhost.d/*; do
            echo "   - ${file}"
            git checkout "${file}"
        done
    else
        echo "   > Skipped resetting nginx files, as not on production"
    fi
fi
