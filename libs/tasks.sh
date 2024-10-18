#!/bin/bash
function processes_tasks {
    local TASKS_FIFO=$1
    logThis "tasks" "Start submitting jobs" "INFO"
    while read task; do
      logThis "tasks" "Submit job > '$task'" "INFO"
      sleep 1
    done < "$TASKS_FIFO"
    logThis "tasks" "All jobs have been submitted" "INFO"
    
    rm -f "$TASKS_FIFO"
}



function generate_tasks {
    #generate_inventory "./inventories.d/"
    logThis "tasks" "Generate inventory done" "DEBUG" || true
    touch $TASKS_FIFO
    
    SITES="$(get_inventory_sites ./inventories.d/)"
    
    for SITE in ${SITES[@]}; do
        CLUSTERS="$(get_inventory_site_clusters ./inventories.d/ $SITE)"
        logThis "tasks" "Processing clusters in $SITE" "DEBUG"
        for CLUSTER in ${CLUSTERS[@]}; do
            NODES="$(get_inventory_site_cluster_nodes ./inventories.d/ $SITE $CLUSTER)"
            logThis "tasks" "Processing nodes in $CLUSTER" "DEBUG"
            for NODE in ${NODES[@]}; do
                echo "orsb -l $NODE 'dockr rn hwpc mes_ptit_param'"
                #echo "  PROCESSOR model : $(yq '.processor.model' ./inventories.d/$SITE/$CLUSTER/$NODE)"
                #echo "  PROCESSOR version : $(yq '.processor.version' ./inventories.d/$SITE/$CLUSTER/$NODE)"
                #echo "  PROCESSOR instruction_set : $(yq '.processor.instruction_set' ./inventories.d/$SITE/$CLUSTER/$NODE)"
                #echo "  PROCESSOR microarchitecture : $(yq '.processor.microarchitecture' ./inventories.d/$SITE/$CLUSTER/$NODE)"
            done >>"$TASKS_FIFO" 
        done
        exit
    done

    processes_tasks $TASKS_FIFO
}
