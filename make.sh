#!/bin/bash

#
# Alias for using make with sudo
# Allows to give access via sudoers only to executing the Makefile with sudo
#

cd /project && exec make "$@"
