#!/bin/bash

IGNORED_FILES=()
ZIP_URL=https://github.com/zwiazeksyndykalistowpolski/docker-project-template/archive/master.zip
UNPACKED_DIR_NAME=docker-project-template-master
TEMP_DIR_NAME=/tmp/_dpt

git_is_dirty () {
    return 1
    [[ $(git diff --shortstat 2> /dev/null | tail -n1) != "" ]] && return 1
    return 0
}

# @see https://gist.github.com/BR0kEN-/a84b18717f8c67ece6f7
# @param string $1
#   Input string.
# @param string $2
#   String that will be searched in input string.
# @param int [$3]
#   Offset of an input string.
strpos() {
    local str=${1}
    local offset=${3}

    if [ -n "${offset}" ]; then
        str=`substr "${str}" ${offset}`
    else
        offset=0
    fi

    str=${str/${2}*/}

    if [ "${#str}" -eq "${#1}" ]; then
        return 0
    fi

    echo $((${#str}+${offset}))
}

copy_file_update () {
    cp "${TEMP_DIR_NAME}/${1}" "./${1}"
}


download_and_unzip_archive () {
    if [[ -f /tmp/_dpt.zip ]]; then
        return 1
    fi

    CURRENT_PWD=$(pwd)
    echo " >> Unzipping archive..."
    wget ${ZIP_URL} -O /tmp/_dpt.zip > /dev/null 2>&1
    cd /tmp/ && unzip -o -q ./_dpt.zip
    mv /tmp/docker-project-template-master ${TEMP_DIR_NAME} > /dev/null 2>&1
}

clean_up () {
    rm /tmp/_dpt.zip  2>/dev/null
    rm -rf ${TEMP_DIR_NAME} 2>/dev/null
}

normalize_path () {
    echo $1 | sed -e 's/^[\.\/|\/]*//'
}

is_file_ignored () {
    compared=$(normalize_path $1)

    for ignored in "${IGNORED_FILES[@]}"; do
        ignored=$(normalize_path ${ignored})

        if [[ $(strpos "${compared}" "${ignored}") == "0" ]]; then
            return 0
        fi
    done

    return 1
}

load_ignored_files () {
    if [[ ! -f ./.updateignore ]]; then
        return 1
    fi

    echo " >> Loading .updateignore (ignored files and directories list)"
    IFS=$'\r\n' GLOBIGNORE='*' command eval  'IGNORED_FILES=($(cat ./.updateignore))'
}

list_files_to_upgrade () {
    CURRENT_PWD=$(pwd)
    cd ${TEMP_DIR_NAME} && find ./ -type f
    cd ${CURRENT_PWD}
}

main () {
    if git_is_dirty; then
        echo " >> Please commit your changes to git or stash them at first"
        git status
        exit 1
    fi

    load_ignored_files
    download_and_unzip_archive

    for f_path in $(list_files_to_upgrade); do
        echo -n " ~> ${f_path}"

        if is_file_ignored "${f_path}"; then
            echo " [ignored by .updateignore]"
            continue
        fi

        copy_file_update "${f_path}"

        echo ""
    done

    echo " >> DONE! Please review the changes using GIT"
    echo " TIP: If you do not want to update some files or directories, then add them to .updateignore"

    clean_up
    git status
}

main
