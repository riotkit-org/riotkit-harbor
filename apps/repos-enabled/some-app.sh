#!/bin/bash
export GIT_PROJECT_NAME=some-app
export GIT_PROJECT_DIR=some-app
export WRITABLE_DIRS="files store cache"

#
# Install the assets
#
post_update () {
    echo "I'm a post_update hook, i'm in $1 directory"
}
