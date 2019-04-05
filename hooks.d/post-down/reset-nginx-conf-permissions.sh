#!/bin/bash

if [[ -d ./containers/nginx/vhost.d ]]; then
    echo " .. Resetting permissions on ./containers/nginx/vhost.d"
    sudo chown ${USER} -R ./containers/nginx/vhost.d

    if [[ "${IS_DEBUG_ENVIRONMENT}" != "1" ]]; then
        echo "   > Resetting nginx files on production"

        for file in ./containers/nginx/vhost.d/*; do
            echo "   - ${file}"

            if [[ -d "${file}" ]]; then
                continue
            fi

            git checkout "${file}"
        done
    else
        echo "   > Skipped resetting nginx files, as not on production"
    fi
fi
