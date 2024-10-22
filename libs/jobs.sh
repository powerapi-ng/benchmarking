#!/bin/bash
function process_jobs {
    local JOBS_FIFO=$1
    logThis "jobs/process_jobs" "Start submitting jobs" "INFO" || true
    while read job; do
      logThis "jobs/process_jobs" "Submit job > '$job'" "INFO" || true
      sleep 1
    done < "$JOBS_FIFO"
    logThis "jobs/process_jobs" "All jobs have been submitted" "INFO" || true
    
    rm -f "$JOBS_FIFO"
}

function submit_job {
    local WALLTIME="$1"
    local SITE="$2"
    local CLUSTER="$3"
    local NODE="$4"
    local COMMAND="$5"
    local RESULT_FILE="$6"
    local PID="$7"
    logThis "jobs/submit_job" "Submited : hhs $SITE oarsub -p $NODE -l host=1,walltime=$WALLTIME $COMMAND $RESULT_FILE" "INFO" || true
    echo $PID
}

function add_job {
    local STATE="Waiting"
    local JOBS_FILE="$1"
    local ID="$2"
    local OAR_JOB_ID="$3"
    local TASK="$4"
    local COMMAND="$5"
    local RESULT_FILE="$6"
    local METADATA_FILE="$7"

    yq -i ".jobs += {\"id\": $(( ID )), \"oar_job_id\": $(( OAR_JOB_ID )), \"state\":\"$STATE\", \"task\":\"$TASK\", \"command\":\"$COMMAND\", \"result_file\":\"$RESULT_FILE\", \"metadata_file\": \"$METADATA_FILE\" }" $JOBS_FILE
}

function generate_jobs {
    local JOBS_FILE="$1"
    local WALLTIME="00:30:00"
    touch $JOBS_FILE
    yq -i '.jobs = []' $JOBS_FILE
    ID=1
    SITES="$(get_inventory_sites ./inventories.d/)"
    
    for SITE in ${SITES[@]}; do
        CLUSTERS="$(get_inventory_site_clusters ./inventories.d/ $SITE)"
        logThis "jobs/generate_jobs" "Processing clusters in $SITE" "DEBUG" || true
        for CLUSTER in ${CLUSTERS[@]}; do
            NODES="$(get_inventory_site_cluster_nodes ./inventories.d/ $SITE $CLUSTER)"
            logThis "jobs/generate_jobs" "Processing nodes in $CLUSTER" "DEBUG" || true
            for NODE in ${NODES[@]}; do
                NODE_NAME="$(basename $NODE .json)"
                TASK="perf"
                COMMAND="dockr rn hwpc mes_ptit_param"
                RESULT_FILE="./results.d/${SITE}/${CLUSTER}/${NODE_NAME}-${TASK}.json"
                METADATA_FILE="./inventories.d/${SITE}/${CLUSTER}/${NODE_NAME}.json"

                OAR_JOB_ID="$(submit_job "$WALLTIME" "$SITE" "$CLUSTER" "$NODE_NAME" "$COMMAND" "$RESULT_FILE" "$ID")"
                add_job "$JOBS_FILE" "$ID" "$OAR_JOB_ID" "$TASK" "$COMMAND" "$RESULT_FILE" "$METADATA_FILE"

                ID=$(( ID + 1 ))
                #echo "  PROCESSOR model : $(yq '.processor.model' ./inventories.d/$SITE/$CLUSTER/$NODE)"
                #echo "  PROCESSOR version : $(yq '.processor.version' ./inventories.d/$SITE/$CLUSTER/$NODE)"
                #echo "  PROCESSOR instruction_set : $(yq '.processor.instruction_set' ./inventories.d/$SITE/$CLUSTER/$NODE)"
                #echo "  PROCESSOR microarchitecture : $(yq '.processor.microarchitecture' ./inventories.d/$SITE/$CLUSTER/$NODE)"
            done
        done
    done
}

function check_on_unfinished_jobs {
    local JOBS_FILE="$1"
    
    local WAITING_JOBS="$(yq -e '.jobs[] | select(.state == "Waiting") | .oar_job_id' $JOBS_FILE)"

    for WAITING_JOB in ${WAITING_JOBS[@]}; do
        CURRENT_STATE="$(ssh lille oarstat -f -j $WAITING_JOB | grep 'state = ' | awk -F' ' '{print $3 }')"
        if [[ "$CURRENT_STATE" == "Waiting" ]]; then
            logThis "jobs/check_on_unfinished_jobs" "Job $WAITING_JOB still waiting" "DEBUG" || true
        else
            yq -i ".jobs[] | select(.oar_job_id == $(( WAITING_JOB ))) | .state = $CURRENT_STATE" $JOBS_FILE
        fi
    done

    local RUNNING_JOBS="$(yq -e '.jobs[] | select(.state == "Running") | .oar_job_id' $JOBS_FILE)"

    for RUNNING_JOB in ${RUNNING_JOBS[@]}; do
        CURRENT_STATE="$(ssh lille oarstat -f -j $RUNNING_JOB | grep 'state = ' | awk -F' ' '{print $3 }')"
        if [[ "$CURRENT_STATE" == "Running" ]]; then
            logThis "jobs/check_on_unfinished_jobs" "Job $RUNNING_JOB still running" "DEBUG" || true
        else
            yq -i ".jobs[] | select(.oar_job_id == $(( RUNNING_JOB ))) | .state = $CURRENT_STATE" $JOBS_FILE
        fi
    done
}

function job_is_done {
    local JOBS_FILE="$1"

    if [[ "$(yq -e '[.jobs[] | select(.status == "Waiting" or "Running")] | length' $JOBS_FILE)" == "0" ]]; then
        return 0
    else
        return 1
    fi
}
