#!/usr/bin/env bash

module load tensorflow/1.14.0
source /projappl/project_2002820/venv/aligner/bin/activate

function on_exit {
    kill -15 $UDPIPE_PID
    deactivate
}
trap on_exit EXIT

UDPIPE_PORT=6000
./udpipe/src/rest_server/udpipe_server $UDPIPE_PORT fi fi Data/finnish-tdt-ud-2.5-191206.udpipe acknowledgement &
UDPIPE_PID=$(ps | grep udpipe | grep -Po '^\d+')

FLASK_APP=digic_aligner.app FLASK_ENV=development DIGIC_CODEHOME=$(pwd) METHOD=laser PORT=$UDPIPE_PORT flask run $*


#if [ "$#" -eq 1 ]; then
#    PORT=$1
#    flask run --port $PORT
#else
#    flask run
#fi
