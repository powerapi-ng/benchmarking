#!/bin/bash
# Logging Level configuration works as follows:
# DEBUG - Provides all logging output
# INFO  - Provides all but debug messages
# WARN  - Provides all but debug and info
# ERROR - Provides all but debug, info and warn
#
# SEVERE and CRITICAL are also supported levels as extremes of ERROR
#
#################################################################################
#          ##      END OF GLOBAL VARIABLE CONFIGURATION      ##
#################################################################################

function logThis() {
    LOG_DIRECTORY="/home/naleblon/powerapi/repositories/benchmarking/logs.d/"
    LOG_FILE="$(date +%Y-%m-%d)-${1}.log"
    dateTime=$(date +%2H:%2M:%2S.%3N)

    if [[ -z "${1}" || -z "${2}" || -z "${3}" ]]
    then
        echo "${dateTime} - ERROR : LOGGING REQUIRES A TARGET, A MESSAGE AND A PRIORITY, IN THAT ORDER."
        echo "${dateTime} - ERROR : INPUTS WERE: ${1}, ${2} and ${3}."
        exit 1
    fi

    logMessage="${2}"
    logMessagePriority="${3}"

    declare -A logPriorities=([DEBUG]=0 [INFO]=1 [WARN]=2 [ERROR]=3 [SEVERE]=4 [CRITICAL]=5)
    [[ ${logPriorities[$logMessagePriority]} ]] || return 1
    (( ${logPriorities[$logMessagePriority]} < ${logPriorities[$SCRIPT_LOGGING_LEVEL]} )) && return 2

    echo "timestamp:${dateTime}|PID:$$|application_name:${APP_NAME}|log_level:${logMessagePriority}|message:${logMessage}" >> "${LOG_DIRECTORY}${LOG_FILE}"
}


