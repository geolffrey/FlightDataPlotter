#!/usr/bin/env bash

#!/usr/bin/env bash

function usage() {
    local MODE=${1}
    echo "Usage"
    echo
    echo "  ${0} -v python_version"
    echo
    echo "Required parameters"
    echo "  -u google_username  : Your googlecode account username"
    echo "  -p google_password  : Your googlecode account password"    
    echo "  -v python version   : The virtualenv Python version to use."
    echo "Optional parameters"
    echo "  -h                : This help"
    exit 1
}

# Make sure we are running from within Jenkins
if [ -z "${WORKSPACE}" ]; then
    echo "ERROR! This script is designed to run from within a Jenkins build."
    exit1
fi

# Init the variables
VIRTVER=""
GC_USERNAME=""
GC_PASSWORD=""

# Parse the options
OPTSTRING=hp:u:v:
while getopts ${OPTSTRING} OPT
do
    case ${OPT} in
        h) usage;;
        p) GC_PASSWORD=${OPTARG};;
        u) GC_USERNAME=${OPTARG};;        
        v) VIRTVER=${OPTARG};;
        *) usage;;
    esac
done
shift "$(( $OPTIND - 1 ))"

if [ -z "${GC_USERNAME}" ] || [ -z "${GC_PASSWORD}" ]; then
    echo "ERROR! You must provide your PyPI username and password."
    exit 1
fi

VIRTENV=${WORKSPACE}/.py${VIRTVER}

# Check the virtualenv exists
if [ ! -f ${VIRTENV}/bin/python${VIRTVER} ]; then
    echo "ERROR! Couldn't find the virtualenv : ${VIRTENV}"
    exit 1
fi

# Enter the virtualenv
. ${VIRTENV}/bin/activate

# Enter the Jenkins workspace
cd ${WORKSPACE}

# Add Google authentication credentials
if [ -e ~/.netrc ]; then
    grep "machine code.google.com login ${GC_USERNAME} password ${GC_PASSWORD}" ~/.netrc || :

    if [ $? -eq 1 ]; then
        echo "machine code.google.com login ${GC_USERNAME} password ${GC_PASSWORD}" >> ~/.netrc
    fi
else
    echo "machine code.google.com login ${GC_USERNAME} password ${GC_PASSWORD}" > ~/.netrc
fi

mkdir -p /tmp/bzr2git/FilterPype || :
cd /tmp/bzr2git/FilterPype

# Get Bazaar code
if [ ! -d FilterPype.bzr ]; then
    bzr branch http://vindictive.flightdataservices.com/Bazaar/FilterPype/ FilterPype.bzr || :
else
    cd FilterPype.bzr
    bzr pull
    cd ..
fi

# Get Git code
if [ ! -d FilterPype.git ]; then
    git clone https://code.google.com/p/filterpype/ FilterPype.git || :
else
    cd FilterPype.git
    git pull
    cd ..
fi

cd /tmp/bzr2git/FilterPype/FilterPype.git
bzr fast-export --export-marks /tmp/bzr2git/FilterPype/FilterPype.marks /tmp/bzr2git/FilterPype/FilterPype.bzr | git fast-import || :
git push || :
