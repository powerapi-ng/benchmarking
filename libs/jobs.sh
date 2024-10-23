#!/bin/bash

source ./libs/scripts.sh

function submit_job {
    local SITE="$1"
    local SCRIPT_FILE="$2"

    make_script_executable $SCRIPT_FILE
    
    ssh $SITE mkdir -p "${SCRIPT_FILE%/*}"

    logThis "jobs/submit_job" "Upload : $SCRIPT_FILE to $SITE:$SCRIPT_FILE " "INFO" || true
    scp $SCRIPT_FILE $SITE:$SCRIPT_FILE

    logThis "jobs/submit_job" "Submited on site $SITE : oarsub -S $SCRIPT_FILE" "INFO" || true
    OAR_JOB_ID="$(ssh $SITE oarsub -S $SCRIPT_FILE 2> /dev/null | grep "OAR_JOB_ID" | cut -d'=' -f2)"

    echo $OAR_JOB_ID
}

function add_job {
    if [[ -z "$OAR_JOB_ID" ]]; then
        local STATE="Failed"
    else
        local STATE="Waiting"
    fi

    local JOBS_FILE="$1"
    local ID="$2"
    local OAR_JOB_ID="$3"
    local TASK="$4"
    local SCRIPT_FILE="$5"
    local RESULT_FILE="$6"
    local METADATA_FILE="$7"
    local SITE="$8"

    logThis "jobs/add_job" "Add Job '$OAR_JOB_ID' metadata to Jobs file '$JOBS_FILE'" "DEBUG" || true
    yq -i ".jobs += {\"id\": $(( ID )), \"oar_job_id\": $(( OAR_JOB_ID )), \"state\":\"$STATE\", \"task\":\"$TASK\", \"script_file\":\"$SCRIPT_FILE\", \"result_file\":\"$RESULT_FILE\", \"metadata_file\": \"$METADATA_FILE\", \"site\":\"$SITE\"}" $JOBS_FILE
}

function generate_jobs {
    local JOBS_FILE="$1"
    local INVENTORIES_DIR="$2"
    local WALLTIME="00:30:00"
    touch $JOBS_FILE
    yq -i '.jobs = []' $JOBS_FILE
    ID=1
    SITES="$(get_inventory_sites ${INVENTORIES_DIR})"
    
    for SITE in ${SITES[@]}; do
        CLUSTERS="$(get_inventory_site_clusters ${INVENTORIES_DIR} $SITE)"
        logThis "jobs/generate_jobs" "Processing clusters in $SITE" "DEBUG" || true
        for CLUSTER in ${CLUSTERS[@]}; do
            NODES="$(get_inventory_site_cluster_nodes ${INVENTORIES_DIR} $SITE $CLUSTER)"
            logThis "jobs/generate_jobs" "Processing nodes in $CLUSTER" "DEBUG" || true
            for NODE in ${NODES[@]}; do
                NODE_NAME="$(basename $NODE .json)"
                TASK="perf"
                SCRIPT_FILE="./scripts.d/${SITE}/${CLUSTER}/${NODE_NAME}_${TASK}.sh"
                RESULT_FILE="./results.d/${SITE}/${CLUSTER}/${NODE_NAME}-${TASK}-raw.csv"
                METADATA_FILE="${INVENTORIES_DIR}${SITE}/${CLUSTER}/${NODE_NAME}.json"
                
                generate_script_file $SCRIPT_FILE $TASK $WALLTIME $NODE_NAME $RESULT_FILE "FALSE" 

                OAR_JOB_ID="$(submit_job "$SITE" "$SCRIPT_FILE" "$NODE_NAME" "$ID")"
                add_job "$JOBS_FILE" "$ID" "$OAR_JOB_ID" "$TASK" "$SCRIPT_FILE" "$RESULT_FILE" "$METADATA_FILE" "$SITE"

                echo "########################"
                echo "########################"
                echo "########################"
                echo "########################"
                echo "Waiting after submission"
                echo "########################"
                echo "########################"
                echo "########################"
                echo "########################"

                sleep 10
                ID=$(( ID + 1 ))
                break
            done
            break
        done
        break
    done
}

function check_on_unfinished_jobs {
    local JOBS_FILE="$1"
    local WAITING_JOBS="$(yq -e '.jobs[] | select(.state == "Waiting") | .oar_job_id' $JOBS_FILE 2> /dev/null)"

    if [[ -n "$WAITING_JOBS" ]]; then
        for WAITING_JOB in ${WAITING_JOBS[@]}; do
            local SITE=$(yq -e ".jobs[] | select(.oar_job_id == $WAITING_JOB) | .site" $JOBS_FILE) 
            local SITE="rennes"
            CURRENT_STATE="$(ssh $SITE oarstat -f -j $WAITING_JOB | grep 'state = ' | awk -F' ' '{print $3 }')"
            if [[ "$CURRENT_STATE" == "Waiting" ]]; then
                logThis "jobs/check_on_unfinished_jobs" "Job $WAITING_JOB still waiting" "DEBUG" || true
            else
                yq -i ".jobs[] | select(.oar_job_id == $(( WAITING_JOB ))) | .state = \"$CURRENT_STATE\"" $JOBS_FILE
            fi
        done
    fi


    local RUNNING_JOBS="$(yq -e '.jobs[] | select(.state == "Running") | .oar_job_id' $JOBS_FILE 2> /dev/null)"

    if [[ -n "$RUNNING_JOBS" ]]; then
        for RUNNING_JOB in ${RUNNING_JOBS[@]}; do
            local SITE="$(yq -e ".jobs[] | select(.oar_job_id == $RUNNING_JOB) | .site" $JOBS_FILE 2> /dev/null)"
            CURRENT_STATE="$(ssh $SITE oarstat -f -j $RUNNING_JOB | grep 'state = ' | awk -F' ' '{print $3 }')"
            if [[ "$CURRENT_STATE" == "Running" ]]; then
                logThis "jobs/check_on_unfinished_jobs" "Job $RUNNING_JOB still running" "DEBUG" || true
            else
                yq -i ".jobs[] | select(.oar_job_id == $(( RUNNING_JOB ))) | .state = \"$CURRENT_STATE\"" $JOBS_FILE
            fi
        done
    fi
}

function job_is_done {
    local JOBS_FILE="$1"

    if [[ "$(yq -e '[.jobs[] | select(.state == "Waiting" or .state == "Running")] | length' $JOBS_FILE)" == "0" ]]; then
        return 0
    else
        return 1
    fi
}
