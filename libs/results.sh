#!/bin/bash

function download_results {
    local RESULT_DIR="$1"
    local SITE="$2"

    scp -ar $SITE:$RESULT_DIR $RESULT_DIR
