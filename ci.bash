#!/bin/bash
set -o pipefail

function build-docs () {
    mkdir /tmp/site
    cd /tmp/site
    git clone https://$GH_USER_NAME:$GH_USER_PWD@github.com/chaostoolkit/chaostoolkit.git .
    git checkout gh-pages
    cd -
    cd docs
    pip install -r requirements.txt
    mkdocs build --strict -d /tmp/site
    cd /tmp/site
    git add .
    git commit -a -m "Built from ${TRAVIS_COMMIT}"
    git push
}

function lint () {
    pycodestyle --first chaostoolkit
}

function build () {
    python setup.py build
}

function run-test () {
    python setup.py test
}

function release () {
    python setup.py release
}

function main () {
    lint || return 1
    build-docs || return 1
    build || return 1
    run-test || return 1
    release || return 1
}

main "$@" || exit 1
exit 0
