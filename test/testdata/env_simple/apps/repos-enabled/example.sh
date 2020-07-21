#!/bin/bash
export GIT_PROTO=https
export GIT_SERVER=github.com
export GIT_PROJECT_NAME=empty
export GIT_PROJECT_DIR=infracheck
export GIT_USER=""
export GIT_PASSWORD=""
export GIT_ORG_NAME="riotkit-org"
export WRITABLE_DIRS="files store cache"

##################################
# Executes after repository update
#
# Parameters:
#   $1 current_working_dir
#
post_update () {
    echo "I'm a post_update hook, i'm in $1 directory"
}

pre_update() {
    echo "Starting to clone/pull example repository :)"
}
