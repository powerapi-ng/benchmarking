#!/bin/bash

function setup_command {
    local SCRIPT_FILE="$1"
    local WALLTIME=$2
    local NODE=$3
    local QUEUE_TYPE="$4"
    local NB_ITER="$5"
    local DOCKER_HUB_USERNAME="${DOCKER_HUB_USERNAME:-""}"
    local DOCKER_HUB_PASSWORD="${DOCKER_HUB_PASSWORD:-""}"

    
    if [[ -z "$DOCKER_HUB_USERNAME" || -z "$DOCKER_HUB_PASSWORD" ]]; then
        echo "DOCKER_HUB_USERNAME and DOCKER_HUB_PASSWORD variables must be set, use a .env to do so"
        exit 1
    fi

    logThis "scripts/setup__command" "Generating SETUP commands in '$SCRIPT_FILE'" "DEBUG" || true

    echo "#!/bin/bash" >> $SCRIPT_FILE
    echo "set -x" >> $SCRIPT_FILE
    echo "set -ueo pipefail" >> $SCRIPT_FILE
    echo "" >> $SCRIPT_FILE

    echo "#OAR -q $QUEUE_TYPE" >> $SCRIPT_FILE
    echo "#OAR -p $NODE" >> $SCRIPT_FILE
    echo "#OAR -l host=1" >> $SCRIPT_FILE
    echo "#OAR -l walltime=$WALLTIME" >> $SCRIPT_FILE
    if [[ "$(yq '.exotic' $METADATA_FILE)" == "true" ]]; then
        echo "#OAR -t exotic" >> $SCRIPT_FILE
    fi
    echo "" >> $SCRIPT_FILE

    echo "sudo-g5k apt-get install -y stress-ng" >> $SCRIPT_FILE
    echo "g5k-setup-docker -t" >> $SCRIPT_FILE
    echo "docker login -u $DOCKER_HUB_USERNAME -p $DOCKER_HUB_PASSWORD" >> $SCRIPT_FILE
    echo "docker run --rm -d --name mongo_source -p 27017:27017 mongo:latest" >> $SCRIPT_FILE
    echo "sleep 30" >> $SCRIPT_FILE

    echo "for i in {1..$NB_ITER}; do" >> $SCRIPT_FILE
}

function free_job_command {
    local SCRIPT_FILE="$1"
    echo '    if [[ -n "$PERF_PID" ]]; then kill -2 $PERF_PID ; fi' >> $SCRIPT_FILE
    echo 'done' >> $SCRIPT_FILE
    echo "exit 0" >> $SCRIPT_FILE
}

function stress-ng_command {
    local SCRIPT_FILE="$1"
    local STRESS_NG_CPU=$2
    local STRESS_NG_OPS_PER_CORE=50000

    echo "    stress-ng --cpu ${STRESS_NG_CPU} --cpu-ops $(( STRESS_NG_CPU * STRESS_NG_OPS_PER_CORE )) -q" >> $SCRIPT_FILE
}

function perf_command {
    local SCRIPT_FILE="$1"
    local JOB_RESULT_DIR="$2"
    local PERF_EVENTS=$3

    logThis "scripts/perf_command" "Generating PERF commands in '$SCRIPT_FILE'" "DEBUG" || true
    echo "    mkdir -p "${JOB_RESULT_DIR}"" >> $SCRIPT_FILE 
    echo "    sudo perf stat -a -o ${JOB_RESULT_DIR}/perf_\${i}.stat -e ${PERF_EVENTS} &" >> $SCRIPT_FILE
    echo "    PERF_PID=\$!" >> $SCRIPT_FILE

}

function hwpc_command {
    local SCRIPT_FILE="$1"
    local JOB_RESULT_DIR="$2"
    local HWPC_RAPL_EVENTS=$3
    local HWPC_MSR_EVENTS=$4
    local HWPC_CORE_EVENTS=$5
    local HWPC_CONFIG_FILE=$6

    local APP_HOME=/app

    logThis "scripts/hwpc_command" "Generating HWPC commands in '$SCRIPT_FILE'" "DEBUG" || true
    
    yq -i  '.name = "sensor"' $HWPC_CONFIG_FILE
    yq -i  '.verbose = true' $HWPC_CONFIG_FILE
    yq -i  ".cgroup_basepath = \"/sys/fs/cgroup/perf_event\"" $HWPC_CONFIG_FILE
    yq -i  '.frequency = 1000' $HWPC_CONFIG_FILE
    yq -i  '.output.type = "csv"' $HWPC_CONFIG_FILE
    yq -i  ".output.directory = \"${APP_HOME}/${JOB_RESULT_DIR}_hwpc_1\"" $HWPC_CONFIG_FILE
    yq -i  '.system.rapl.events = []' $HWPC_CONFIG_FILE
    yq -i  '.system.rapl.monitoring_type = "MONITOR_ONE_CPU_PER_SOCKET"' $HWPC_CONFIG_FILE
    yq -i  '.system.msr.events = []' $HWPC_CONFIG_FILE
    yq -i  '.system.core.events = []' $HWPC_CONFIG_FILE


    for EVENT in $(echo $HWPC_RAPL_EVENTS | xargs); do 
        yq -i  ".system.rapl.events += \"$EVENT\" " $HWPC_CONFIG_FILE
    done
    for EVENT in $(echo $HWPC_MSR_EVENTS | xargs); do 
        yq -i  ".system.msr.events += \"$EVENT\" " $HWPC_CONFIG_FILE
    done
    for EVENT in $(echo $HWPC_CORE_EVENTS | xargs); do 
        yq -i  ".system.core.events += \"$EVENT\" " $HWPC_CONFIG_FILE
    done
    echo "    docker ps -a | grep hwpc-sensor-\$(( i - 1)) && docker rm -f hwpc-sensor" >> $SCRIPT_FILE
    echo "    JOB_RESULT_DIR=${JOB_RESULT_DIR}_\${i}" >> $SCRIPT_FILE
    echo "    HWPC_CONFIG_FILE=$HWPC_CONFIG_FILE" >> $SCRIPT_FILE
    echo "    mkdir -p $JOB_RESULT_DIR" >> $SCRIPT_FILE
    echo "    docker run --rm -d --net=host --privileged --pid=host --name \"hwpc-sensor-\${i}\" -v /sys:/sys -v /var/lib/docker/containers:/var/lib/docker/containers:ro -v /tmp/powerapi-sensor-reporting:/reporting -v \$(pwd):${APP_HOME} powerapi/hwpc-sensor:1.4.0 --config-file ${APP_HOME}/\$HWPC_CONFIG_FILE" >> $SCRIPT_FILE
    echo "    NEXT_INDEX=\$(( i+1 ))" >> $SCRIPT_FILE
    echo "    sed -i \"s@\${JOB_RESULT_DIR}_hwpc_\${i}@\${JOB_RESULT_DIR}_hwpc_\${NEXT_INDEX}@\" \$HWPC_CONFIG_FILE" >> $SCRIPT_FILE

}


function generate_script_file {
    local SCRIPT_FILE="$1"
    local HWPC_CONFIG_FILE="$2"
    local WALLTIME=$3
    local NODE=$4
    local QUEUE_TYPE="$5"
    local TASK=$6
    local STRESS_NG_NB_CPU=$7
    local JOB_RESULT_DIR=$8
    local METADATA_FILE=$9
    local PROCESSOR_VENDOR="$(yq '.processor.vendor' $METADATA_FILE)"
    local PROCESSOR_MICROARCHITECTURE="$(yq '.processor.microarchitecture' $METADATA_FILE)"
    local PROCESSOR_VERSION="$(yq '.processor.version' $METADATA_FILE)"

    local EVENTS_BY_CONFIG_FILE="config/events_by_config.json"

    local PERF_EVENTS="$(concat_perf_events $EVENTS_BY_CONFIG_FILE $PROCESSOR_VENDOR $PROCESSOR_MICROARCHITECTURE "$PROCESSOR_VERSION")"
    local HWPC_RAPL_EVENTS="$(concat_hwpc_rapl_events $EVENTS_BY_CONFIG_FILE $PROCESSOR_VENDOR $PROCESSOR_MICROARCHITECTURE "$PROCESSOR_VERSION")"
    local HWPC_MSR_EVENTS="$(concat_hwpc_msr_events $EVENTS_BY_CONFIG_FILE $PROCESSOR_VENDOR $PROCESSOR_MICROARCHITECTURE "$PROCESSOR_VERSION")"
    local HWPC_CORE_EVENTS="$(concat_hwpc_core_events $EVENTS_BY_CONFIG_FILE $PROCESSOR_VENDOR $PROCESSOR_MICROARCHITECTURE "$PROCESSOR_VERSION")"

    logThis "scripts/generate_script_file" "Generating '$SCRIPT_FILE'" "DEBUG" || true
    

    mkdir -p "${SCRIPT_FILE%/*}"
    touch $SCRIPT_FILE

    mkdir -p "${HWPC_CONFIG_FILE%/*}"
    touch $HWPC_CONFIG_FILE

    setup_command $SCRIPT_FILE $WALLTIME $NODE $QUEUE_TYPE 30

    
    case "$TASK" in
        perf)
            perf_command "$SCRIPT_FILE" "$JOB_RESULT_DIR" "$PERF_EVENTS"
            ;;

        hwpc)
            hwpc_command "$SCRIPT_FILE" "$JOB_RESULT_DIR" "$HWPC_RAPL_EVENTS" "$HWPC_MSR_EVENTS" "$HWPC_CORE_EVENTS" "$HWPC_CONFIG_FILE"
            ;;

        hwpc_perf)
            perf_command "$SCRIPT_FILE" "$JOB_RESULT_DIR" "$PERF_EVENTS"
            hwpc_command "$SCRIPT_FILE" "$JOB_RESULT_DIR" "$HWPC_RAPL_EVENTS" "$HWPC_MSR_EVENTS" "$HWPC_CORE_EVENTS" "$HWPC_CONFIG_FILE"
            ;;

        *)
            echo "Only [perf|hwpc] are supported!"
            return 1
            ;;
        esac
    stress-ng_command "$SCRIPT_FILE" "$STRESS_NG_NB_CPU"
    free_job_command $SCRIPT_FILE

}

function make_script_executable {
    local SCRIPT_FILE=$1
    
    logThis "scripts/make_script_executable" "Make '$SCRIPT_FILE' exectuable" "DEBUG" || true
    chmod u+x $SCRIPT_FILE
}

