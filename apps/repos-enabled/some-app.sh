#!/bin/bash
export GIT_PROJECT_NAME=some-app
export GIT_PROJECT_DIR=some-app

# note: writable dirs will be automatically copied to backup, space separated
export WRITABLE_DIRS="files store cache"

#
# Install the assets
#
post_update () {
    echo "I'm a post_update hook, i'm in $1 directory"
}
