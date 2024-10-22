#!/bin/bash

function perf_command {
    local PERF_ARGS="$1"
    local SCRIPT_FILE="$2"
    local RESULT_FILE="$3"

    echo "local RESULT_FILE=$RESULT_FILE" >> $SCRIPT_FILE
    echo "sudo-g5k apt-get install stress-ng"
    echo $'echo energy-cores,energy-pkg,energy-gpu,energy-psys > $RESULT_FILE' >> $SCRIPT_FILE  

    echo 'for i in {1..5}; do' >> $SCRIPT_FILE
    echo '    sudo perf stat -a -o perf_${i}.stat -e power/energy-cores/,power/energy-pkg/,power/energy-gpu/,power/energy-psys/ stress-ng --cpu 1 --cpu-load 60 -q --timeout 20s' >> $SCRIPT_FILE
    echo $'    echo "$(grep Joules ./perf_${i}.stat | awk \'{print $2}\' | sed \'s/,/./g\' | paste -sd \',\')" >> $RESULT_FILE' >> $SCRIPT_FILE
    echo 'done' >> $SCRIPT_FILE

}



function generate_script_file {
    local TASK=$1
    local TASK_ARGS="arg1 arg2"
    local WALLTIME=$2
    local NODE=$3
    local RESULT_FILE=$4
    local QUEUE_TYPE="default"
    local EXOTIC=${5:-"FALSE"}

    local SCRIPT_FILE="./scripts.d/tangocharlie.sh"

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
            perf_command "$TASK_ARGS" "$SCRIPT_FILE" "$RESULT_FILE"
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
    
    chmod u+x $SCRIPT_FILE
}
