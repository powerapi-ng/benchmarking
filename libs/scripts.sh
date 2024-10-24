#!/bin/bash

function perf_command {
    local SCRIPT_FILE="$1"
    local RESULT_FILE="$2"
    local PERF_EVENTS=$3
    local PERF_CPU=$4
    local PERF_CPU_LOAD=$5
    local PERF_TIMEOUT=$6
    local NB_ITER=$7
    local NB_CPU_VARIANTS=$8
    local NB_CPU_OPS_VARIANTS=$9

    logThis "scripts/perf_command" "Generating PERF commands in '$SCRIPT_FILE'" "DEBUG" || true
    echo "mkdir -p ${RESULT_FILE%/*}" >> $SCRIPT_FILE
    echo "RESULT_FILE=$RESULT_FILE" >> $SCRIPT_FILE
    echo "sudo-g5k apt-get install -y stress-ng" >> $SCRIPT_FILE

    echo "touch \$RESULT_FILE" >> $SCRIPT_FILE
    echo $'echo energy-ram,energy-pkg > $RESULT_FILE' >> $SCRIPT_FILE  

    echo 'for i in {1..5}; do' >> $SCRIPT_FILE
    echo "    sudo perf stat -a -o /tmp/perf_\${i}.stat -e ${PERF_EVENTS} stress-ng --cpu ${PERF_CPU} --cpu-load ${PERF_CPU_LOAD} -q --timeout ${PERF_TIMEOUT}s" >> $SCRIPT_FILE
    echo $'    echo "$(grep Joules /tmp/perf_${i}.stat | awk \'{print $1}\' | sed \'s/,//g\' | paste -sd \',\')" >> $RESULT_FILE' >> $SCRIPT_FILE
    echo 'done' >> $SCRIPT_FILE

}



function generate_script_file {
    local SCRIPT_FILE="$1"
    local TASK=$2
    local WALLTIME=$3
    local NODE=$4
    local RESULT_FILE=$5
    local QUEUE_TYPE="default"
    local METADATA_FILE=$6



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

    if [[ "$(yq '.exotic' $METADATA_FILE)" == "true" ]]; then
        echo "#OAR -t exotic" >> $SCRIPT_FILE
    fi
    
    case "$TASK" in
        perf)
            if [[ "$(yq '.processor.vendor' $METADATA_FILE)" == "Intel" ]]; then 
                local TASK_ARGS=("/power/energy-ram/,/power/energy-pkg/" "1" "60" "60")
            else
                local TASK_ARGS=("/power/energy-pkg/" "1" "60" "60")
            fi
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

function list_of_values {

  local MIN_VALUE=$1
  local MAX_VALUE=$2
  values_list=()
  
  value=$MIN_VALUE

  while [ $value -le $MAX_VALUE ]; do
      values_list+=($value)
      
      # Add random values around the power of 2
      if [ $value -gt 1 ]; then
          random_low=$((value - RANDOM % (value / 2)))
          random_high=$((value + RANDOM % (value / 2)))
          
          if [ $random_low -ge $MIN_VALUE ]; then
              values_list+=($random_low)
          fi
          
          if [ $random_high -le $MAX_VALUE ]; then
              values_list+=($random_high)
          fi
      fi
      
      value=$((value * 2))
  done
  
  # Remove duplicates and sort the VALUE list
  values_list=($(echo "${values_list[@]}" | tr ' ' '\n' | sort -n | uniq))
  
  echo "${values_list[@]}"
}
