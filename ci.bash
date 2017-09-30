#!/bin/bash
set -o pipefail

function build-docs () {
    origin=$PWD
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
    cd $origin
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

    pip install twine
    twine upload dist/* -u ${PYPI_USER_NAME} -p ${PYPI_PWD}

    version=$(sed -n "s/^__version__\s=\s'\(.*\)'$/\1/p" chaostoolkit/__init__.py)
    docker login -u ${DOCKER_USER_NAME} -p ${DOCKER_PWD}
    docker build -t chaostoolkit/chaostoolkit:$version .
    docker push chaostoolkit/chaostoolkit:$version
}

function main () {
    lint || return 1
    build || return 1
    run-test || return 1

    if [[ $TRAVIS_TAG =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        build-docs || return 1
        release || return 1
    fi
}

main "$@" || exit 1
exit 0
