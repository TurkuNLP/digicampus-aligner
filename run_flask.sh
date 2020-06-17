#!/usr/bin/env bash

function on_exit {
    kill -15 $UDPIPE_PID
}
trap on_exit EXIT

PORT=5000
./udpipe/src/rest_server/udpipe_server $PORT fi fi Data/finnish-tdt-ud-2.5-191206.udpipe acknowledgement &
UDPIPE_PID=$(ps | grep udpipe | grep -Po '^\d+')

source /home/ginter/venv-digicampus/bin/activate

FLASK_APP=digic_aligner.app FLASK_ENV=development DIGIC_CODEHOME=$(pwd) METHOD="sbert" THRESHOLD="0.85" PORT=$PORT flask run --port <ssh -L port number>
