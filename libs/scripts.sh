#!/bin/bash

function perf_command {
    local SCRIPT_FILE="$1"
    local RESULT_FILE="$2"
    local PERF_EVENTS=$3
    local PERF_CPU=$4
    local PERF_CPU_LOAD=$5
    local PERF_TIMEOUT=$6

    logThis "scripts/perf_command" "Generating PERF commands in '$SCRIPT_FILE'" "DEBUG" || true
    echo "mkdir -p ${RESULT_FILE%/*}"
    echo "local RESULT_FILE=$RESULT_FILE" >> $SCRIPT_FILE
    echo "sudo-g5k apt-get install stress-ng"
    echo $'echo energy-cores,energy-pkg,energy-gpu,energy-psys > $RESULT_FILE' >> $SCRIPT_FILE  

    echo 'for i in {1..5}; do' >> $SCRIPT_FILE
    echo "    sudo perf stat -a -o perf_\${i}.stat -e ${PERF_EVENTS} stress-ng --cpu ${PERF_CPU} --cpu-load ${PERF_CPU_LOAD} -q --timeout ${PERF_TIMEOUT}s" >> $SCRIPT_FILE
    echo $'    echo "$(grep Joules ./perf_${i}.stat | awk \'{print $2}\' | sed \'s/,/./g\' | paste -sd \',\')" >> $RESULT_FILE' >> $SCRIPT_FILE
    echo 'done' >> $SCRIPT_FILE

}



function generate_script_file {
    local SCRIPT_FILE="$1"
    local TASK=$2
    local TASK_ARGS=("power/energy-cores/,power/energy-pkg/,power/energy-gpu/,power/energy-psys/" "1" "60" "60")
    local WALLTIME=$3
    local NODE=$4
    local RESULT_FILE=$5
    local QUEUE_TYPE="default"
    local EXOTIC=${6:-"FALSE"}

    logThis "scripts/generate_script_file" "Generating '$SCRIPT_FILE'" "DEBUG" || true
    
    mkdir -p "${SCRIPT_FILE%/*}"
    touch $SCRIPT_FILE
    echo "#!/bin/bash" > $SCRIPT_FILE
    echo "set -x" >> $SCRIPT_FILE
    echo "set -ueo pipefail" >> $SCRIPT_FILE
    echo "" >> $SCRIPT_FILE

    echo "#OAR -q $QUEUE_TYPE" >> $SCRIPT_FILE
    echo "#OAR -p $NODE" >> $SCRIPT_FILE
    echo "#OAR -l host=1" >> $SCRIPT_FILE
    echo "#OAR -l walltime=$WALLTIME" >> $SCRIPT_FILE
    if [[ $"EXOTIC" == "TRUE" ]]; then 
        echo "#OAR -t exotic" >> $SCRIPT_FILE
    fi
    
    case "$TASK" in
        perf)
            perf_command "$SCRIPT_FILE" "$RESULT_FILE" "${TASK_ARGS[@]}"
            ;;

        hwpc)
            echo "$(hwpc_command $TASK_ARGS)" >> $SCRIPT_FILE
            ;;

        smartwatts)
            echo "$(smartwatts_command $TASK_ARGS)" >> $SCRIPT_FILE
            ;;

        *)
            echo "Only [perf|hwpc|smartwatts] are supported!"
            return 1
            ;;
        esac


}

function make_script_executable {
    local SCRIPT_FILE=$1
    
    logThis "scripts/make_script_executable" "Make '$SCRIPT_FILE' exectuable" "DEBUG" || true
    chmod u+x $SCRIPT_FILE
}
