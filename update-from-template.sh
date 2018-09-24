#!/bin/bash

git_is_dirty () {
    if [[ $(git diff --shortstat 2> /dev/null | tail -n1) != "" ]]; then
        return 1
    fi

    return 0
}

main () {
    if git_is_dirty; then
        echo " >> Please commit your changes to git or stash them at first"
        git status
        exit 1
    fi
}

main
