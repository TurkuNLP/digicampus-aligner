#!/usr/bin/env bash

function on_exit {
    kill -15 $UDPIPE_PID
}
trap on_exit EXIT

UDPIPE_PORT=6000
./udpipe/src/rest_server/udpipe_server $UDPIPE_PORT fi fi Data/finnish-tdt-ud-2.5-191206.udpipe acknowledgement &
UDPIPE_PID=$(ps | grep udpipe | grep -Po '^\d+')

FLASK_APP=digic_aligner.app FLASK_ENV=development DIGIC_CODEHOME=$(pwd) METHOD=laser PORT=$UDPIPE_PORT flask run $*
