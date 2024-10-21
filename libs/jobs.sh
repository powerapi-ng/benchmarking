#!/bin/bash
function process_jobs {
    local JOBS_FIFO=$1
    logThis "jobs/process_jobs" "Start submitting jobs" "INFO"
    while read job; do
      logThis "jobs/process_jobs" "Submit job > '$job'" "INFO"
      sleep 1
    done < "$JOBS_FIFO"
    logThis "jobs/process_jobs" "All jobs have been submitted" "INFO"
    
    rm -f "$JOBS_FIFO"
}

function add_job {
    local STATUS="TODO"
    local JOBS_FILE="$1"
    local ID="$2"
    local OAR_JOB_ID=""
    local TASK="$3"
    local COMMAND="$4"
    local RESULT_FILE="$5"
    local METADATA_FILE="$6"

    yq -i ".jobs += {\"id\": $(( ID )), \"oar_job_id\": null, \"status\":\"$STATUS\", \"task\":\"$TASK\", \"command\":\"$COMMAND\", \"result_file\":\"$RESULT_FILE\", \"metadata_file\": \"$METADATA_FILE\" }" $JOBS_FILE
}

function generate_jobs {
    local JOBS_FILE="$1"
    touch $JOBS_FILE
    yq -i '.jobs = []' $JOBS_FILE
    ID=1
    SITES="$(get_inventory_sites ./inventories.d/)"
    
    for SITE in ${SITES[@]}; do
        CLUSTERS="$(get_inventory_site_clusters ./inventories.d/ $SITE)"
        logThis "jobs/generate_jobs" "Processing clusters in $SITE" "DEBUG"
        for CLUSTER in ${CLUSTERS[@]}; do
            NODES="$(get_inventory_site_cluster_nodes ./inventories.d/ $SITE $CLUSTER)"
            logThis "jobs/generate_jobs" "Processing nodes in $CLUSTER" "DEBUG"
            for NODE in ${NODES[@]}; do
                NODE_NAME="$(basename $NODE .json)"
                TASK="perf"
                COMMAND="dockr rn hwpc mes_ptit_param"
                RESULT_FILE="./results.d/${SITE}/${CLUSTER}/${NODE_NAME}-${TASK}.json"
                METADATA_FILE="./inventories.d/${SITE}/${CLUSTER}/${NODE_NAME}.json"

                add_job "$JOBS_FILE" "$ID" "$TASK" "$COMMAND" "$RESULT_FILE" "$METADATA_FILE"

                ID=$(( ID + 1 ))
                #echo "  PROCESSOR model : $(yq '.processor.model' ./inventories.d/$SITE/$CLUSTER/$NODE)"
                #echo "  PROCESSOR version : $(yq '.processor.version' ./inventories.d/$SITE/$CLUSTER/$NODE)"
                #echo "  PROCESSOR instruction_set : $(yq '.processor.instruction_set' ./inventories.d/$SITE/$CLUSTER/$NODE)"
                #echo "  PROCESSOR microarchitecture : $(yq '.processor.microarchitecture' ./inventories.d/$SITE/$CLUSTER/$NODE)"
            done
        done
    done
}
