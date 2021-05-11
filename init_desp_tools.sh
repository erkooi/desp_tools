#!/usr/bin/env bash -e
###############################################################################
#
# Copyright (C) 2018 
# ASTRON (Netherlands Institute for Radio Astronomy) <http://www.astron.nl/>
# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# $Id$
#
###############################################################################

#
# Initialisation script to setup the environment variables for this branch
#

# Make sure the script is sourced and not accidentally given execution rights and just executes it.
if [[ "$_" == "${0}" ]]; then
    echo "ERROR: Use this command with '. ' or 'source '"
    sleep 1
    exit
fi

# Figure out where this script is located and set environment variables accordingly
export DESP_TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "DESP_TOOLS environment will be setup for" $DESP_TOOLS

# Define function to add directories to a given environment variable
#     args: name_of_env_var new_path [new_path ...]
# Directories are only added when they exist.
pathadd() {
    for new_dir in ${@:2}
    do
        eval dir_to_add=`echo ${new_dir}`
        if [ -d ${dir_to_add} ] && ! echo ${!1} | grep -E -q "(^|:)$dir_to_add($|:)" ; then
            eval export ${1}=${1:+${!1#:}:}${dir_to_add}
        fi
    done
}

# Extend the PATH and PYTHONPATH variables
pathadd "PYTHONPATH" ${DESP_TOOLS}

