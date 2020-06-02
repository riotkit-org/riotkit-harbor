#!/bin/bash
# variables here are overriding everything that is in .env file
export GIT_PROJECT_NAME=riotkit-do
export GIT_PROJECT_DIR=riotkit-do
export GIT_ORG_NAME=riotkit-org
export WRITABLE_DIRS=".rkd"

#
# Install the assets
#
post_update () {
    echo "I'm a post_update hook, i'm in $1 directory"
}

pre_update() {
    echo "Hello! Going to update! mhmhmh"
}
