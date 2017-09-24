#!/bin/bash
set -o pipefail

function build-docs () {
    mkdir /tmp/site
    cd /tmp/site
    git clone https://$GH_USER_NAME:$GH_USER_PWD@github.com/chaostoolkit/chaostoolkit.git .
    git checkout gh-pages
    cd -
    cd docs
    mkdocs build --strict -d /tmp/site
    cd /tmp/site
    git add .
    git commit -a -m "Built from ${TRAVIS_COMMIT}"
    git push
}

function main () {
    build-docs || return 1
}

main "$@" || exit 1
exit 0
