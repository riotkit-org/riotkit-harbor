#!/bin/bash

function git_is_dirty {
  [[ $(git diff --shortstat 2> /dev/null | tail -n1) != "" ]] && echo "*"
}

main () {
    if git_is_dirty; then
        echo " >> Please commit your changes to git or stash them at first"
        git status
        exit 1
    fi
}

main
