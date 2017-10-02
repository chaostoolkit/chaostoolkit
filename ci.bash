#!/bin/bash
set -eo pipefail

function build-docs () {
    echo "Building the documentation"
    origin=$PWD
    mkdir /tmp/site
    cd /tmp/site
    git clone https://$GH_USER_NAME:$GH_USER_PWD@github.com/chaostoolkit/chaostoolkit.git .
    git checkout gh-pages
    cd -
    cd docs
    pip install -r requirements.txt
    mkdocs build --strict -d /tmp/site
    cd $origin
}

function publish-docs () {
    echo "Publishing the documentation"
    origin=$PWD
    cd /tmp/site
    echo "chaostoolkit.org" > CNAME
    git add .
    git commit -a -m "Built from ${TRAVIS_COMMIT}"
    git push
    cd $origin
}

function lint () {
    echo "Checking the code syntax"
    pycodestyle --first chaostoolkit
}

function build () {
    echo "Building the choastoolkit package"
    python setup.py build
}

function run-test () {
    echo "Running the tests"
    python setup.py test
}

function release () {
    echo "Releasing the pachaage"
    python setup.py release

    echo "Publishing to PyPI"
    pip install twine
    twine upload dist/* -u ${PYPI_USER_NAME} -p ${PYPI_PWD}

    echo "Building the Docker image"
    docker login -u ${DOCKER_USER_NAME} -p ${DOCKER_PWD}
    docker build -t chaostoolkit/chaostoolkit .

    docker tag chaostoolkit/chaostoolkit:latest chaostoolkit/chaostoolkit:$TRAVIS_TAG
    
    echo "Publishing to the Docker repository"
    docker push chaostoolkit/chaostoolkit:$TRAVIS_TAG
    docker push chaostoolkit/chaostoolkit:latest
}

function main () {
    lint || return 1
    build || return 1
    run-test || return 1

    if [[ $TRAVIS_PYTHON_VERSION =~ ^3\.5+$ ]]; then
        build-docs || return 1

        if [[ $TRAVIS_PULL_REQUEST == false && $TRAVIS_BRANCH == 'master' ]]; then
            # build docs on each commit but only from master
            publish-docs || return 1
        fi

        if [[ $TRAVIS_TAG =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "Releasing tag $TRAVIS_TAG with Python $TRAVIS_PYTHON_VERSION"
            release || return 1
        fi
    fi
}

main "$@" || exit 1
exit 0
