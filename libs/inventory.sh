#!/bin/bash
function get_api_call {

    local ENDPOINT="$1"
    logThis "inventory" "Scrapping ${ENDPOINT}" "INFO"  || true

    curl -s -u "$G5K_USERNAME:$G5K_PASSWORD" "$ENDPOINT"

}

function generate_inventory {
    if [[ -z "$G5K_USERNAME" || -z "$G5K_PASSWORD" ]]; then
        echo "Missing $G5K_USERNAME and/or $G5K_PASSWORD. Both are needed for API authentication"
        exit 1
    fi
    # Example complete url : https://api.grid5000.fr/stable/sites/lille/clusters/chiclet/nodes/chiclet-1.json?pretty
    local BASE_API_URI="https://api.grid5000.fr/stable/"
    local SITES_ENDPOINT="sites"
    local CLUSTERS_ENDPOINT="clusters"
    local NODES_ENDPOINT="nodes"
    local NODE_ENDPOINT=""
    local NODE_ENDPOINT_SUFFIX=".json?pretty"
    local INVENTORIES_DIR="$1"

    logThis "inventory" "Remove old inventory files to update" "INFO" || true
    find $INVENTORIES_DIR -type f -mtime +7 -exec rm {} \;
    
    SITES="$(get_api_call "${BASE_API_URI}${SITES_ENDPOINT}")"
    mapfile -t SITES_UID < <(echo "${SITES}" | yq '.items[] | .uid')
    
    for SITE_UID in "${SITES_UID[@]}"; do
        logThis "inventory" "Processing site: ${SITE_UID}" "DEBUG" || true
        mkdir -p "$INVENTORIES_DIR/$SITE_UID/"
        
        SITE_API_URI="${BASE_API_URI}${SITES_ENDPOINT}/${SITE_UID}/"
        CLUSTERS="$(get_api_call "${SITE_API_URI}${CLUSTERS_ENDPOINT}")"
        mapfile -t CLUSTERS_UID < <(echo "${CLUSTERS}" | yq '.items[] | .uid')

        for CLUSTER_UID in "${CLUSTERS_UID[@]}"; do
            logThis "inventory" "Processing cluster: ${SITE_UID}/${CLUSTER_UID}" "DEBUG" || true
            mkdir -p "$INVENTORIES_DIR/$SITE_UID/$CLUSTER_UID/"
            
            CLUSTER_API_URI="${SITE_API_URI}${CLUSTERS_ENDPOINT}/${CLUSTER_UID}/"
            NODES="$(get_api_call "${CLUSTER_API_URI}${NODES_ENDPOINT}")"
            mapfile -t NODES_UID < <(echo "${NODES}" | yq '.items[] | .uid')


            for NODE_UID in "${NODES_UID[@]}"; do
                logThis "inventory" "Processing node: ${SITE_UID}/${CLUSTER_UID}/${NODE_UID}" "DEBUG" || true
                NODE_SPECS_FILE_PATH="$INVENTORIES_DIR/$SITE_UID/$CLUSTER_UID/$NODE_UID.json"
                
                if ! [[ -f "${NODE_SPECS_FILE_PATH}" ]]; then
                    logThis "inventory" "$NODE_SPECS_FILE_PATH was too old or not present !" "DEBUG" || true
                    NODE_API_URI="${CLUSTER_API_URI}/${NODES_ENDPOINT}/${NODE_UID}${NODE_ENDPOINT_SUFFIX}"
                    get_api_call "${NODE_API_URI}" > "${NODE_SPECS_FILE_PATH}"
                else
                    logThis "inventory" "$NODE_SPECS_FILE_PATH is up to date !" "DEBUG" || true
                fi
                break
            done
            break
        done 
        break
    done
}

function get_inventory_sites {
    local INVENTORIES_DIR="$1"
    echo "$(find $INVENTORIES_DIR -maxdepth 1 -mindepth 1 -type d -exec basename {} \;)"
}
function get_inventory_site_clusters {
    local INVENTORIES_DIR="$1"
    local SITE="$2"
    echo "$(find $INVENTORIES_DIR/$SITE/ -maxdepth 1 -mindepth 1 -type d -exec basename {} \;)"
}

function get_inventory_site_cluster_nodes {
    local INVENTORIES_DIR="$1"
    local SITE="$2"
    local CLUSTER="$3"
    echo "$(find $INVENTORIES_DIR/$SITE/$CLUSTER/ -maxdepth 1 -mindepth 1 -type f -exec basename {} \;)"
}

function generate_events_by_config_bootstrap {
    set -x
    local EVENTS_BY_CONFIG_FILE="$1"
    local INVENTORIES_DIR="$2"
    local AMD_PERF_DEFAULT_EVENTS="/power/energy-pkg/"
    local AMD_HWPC_RAPL_DEFAULT_EVENTS="RAPL_ENERGY_PKG"
    local AMD_HWPC_MSR_DEFAULT_EVENTS="TSC APERF MPERF"
    local AMD_HWPC_CORE_DEFAULT_EVENTS="CYCLES_NOT_IN_HALTS RETIRED_INSTRUCTIONS RETIRED_UOPS"
    local INTEL_PERF_DEFAULT_EVENTS="/power/energy-pkg/,/power/energy-ram/"
    local INTEL_HWPC_RAPL_DEFAULT_EVENTS="RAPL_ENERGY_PKG"
    local INTEL_HWPC_MSR_DEFAULT_EVENTS="TSC APERF MPERF"
    local INTEL_HWPC_CORE_DEFAULT_EVENTS="CPU_CLK_THREAD_UNHALTED:REF_P CPU_CLK_THREAD_UNHALTED:THREAD_P LLC_MISSES INSTRUCTIONS_RETIRED"
    touch $EVENTS_BY_CONFIG_FILE
    yq -i '.vendors = []' $EVENTS_BY_CONFIG_FILE

    SITES="$(get_inventory_sites ${INVENTORIES_DIR})"
    for SITE in ${SITES[@]}; do
        CLUSTERS="$(get_inventory_site_clusters ${INVENTORIES_DIR} $SITE)"
        for CLUSTER in ${CLUSTERS[@]}; do
            local FIRST_NODE_METADATA_FILE="$INVENTORIES_DIR/$SITE/$CLUSTER/${CLUSTER}-1.json"
            local PROCESSOR_VENDOR="$(yq '.processor.vendor' $FIRST_NODE_METADATA_FILE | xargs)"
            local PROCESSOR_VERSION="$(yq '.processor.version' $FIRST_NODE_METADATA_FILE | xargs)"
            local PROCESSOR_MICROARCHITECTURE="$(yq '.processor.microarchitecture' $FIRST_NODE_METADATA_FILE | xargs)"
           
            if [[ "$(yq ".vendors[] | select(.name == \"$PROCESSOR_VENDOR\")" $EVENTS_BY_CONFIG_FILE)" == "" ]]; then
                if [[ "$PROCESSOR_VENDOR" == "AMD" ]]; then
                yq -i ".vendors += {\"name\": \"$PROCESSOR_VENDOR\", \"microarchitectures\": [],  \"perf_default_events\": \"$AMD_PERF_DEFAULT_EVENTS\", \"hwpc_default_events\": {\"rapl\": \"$AMD_HWPC_RAPL_DEFAULT_EVENTS\", \"msr\": \"$AMD_HWPC_MSR_DEFAULT_EVENTS\" , \"core\": \"$AMD_HWPC_CORE_DEFAULT_EVENTS\" }}" $EVENTS_BY_CONFIG_FILE
                elif [[ "$PROCESSOR_VENDOR" == "Intel" ]]; then
                yq -i ".vendors += {\"name\": \"$PROCESSOR_VENDOR\", \"microarchitectures\": [],  \"perf_default_events\": \"$INTEL_PERF_DEFAULT_EVENTS\", \"hwpc_default_events\": {\"rapl\": \"$INTEL_HWPC_RAPL_DEFAULT_EVENTS\", \"msr\": \"$INTEL_HWPC_MSR_DEFAULT_EVENTS\" , \"core\": \"$INTEL_HWPC_CORE_DEFAULT_EVENTS\" }}" $EVENTS_BY_CONFIG_FILE
                else
                yq -i ".vendors += {\"name\": \"$PROCESSOR_VENDOR\", \"microarchitectures\": [],  \"perf_default_events\": \"\", \"hwpc_default_events\": {\"rapl\": \"\", \"msr\": \"\", \"core\": \"\"}}" $EVENTS_BY_CONFIG_FILE
                fi
            fi

            if [[ "$(yq ".vendors[] | select(.name == \"$PROCESSOR_VENDOR\").microarchitectures[] | select(.name == \"$PROCESSOR_MICROARCHITECTURE\")" $EVENTS_BY_CONFIG_FILE)" == "" ]]; then
                yq -i "(.vendors[] | select(.name == \"$PROCESSOR_VENDOR\")).microarchitectures += {\"name\": \"$PROCESSOR_MICROARCHITECTURE\", \"perf_specific_events\": \"\", \"hwpc_specific_events\": {\"rapl\": \"\", \"msr\":\"\", \"core\":\"\"}}" $EVENTS_BY_CONFIG_FILE 
            fi

            if [[ "$(yq ".vendors[] | select(.name == \"$PROCESSOR_VENDOR\").microarchitectures[] | select(.name == \"$PROCESSOR_MICROARCHITECTURE\").versions[] | select(.name == \"$PROCESSOR_VERSION\")" $EVENTS_BY_CONFIG_FILE)" == "" ]]; then
                yq -i "((.vendors[] | select(.name == \"$PROCESSOR_VENDOR\")).microarchitectures[] | select(.name == \"$PROCESSOR_MICROARCHITECTURE\")).versions += {\"name\": \"$PROCESSOR_VERSION\"}" $EVENTS_BY_CONFIG_FILE 
            fi

        done
    done
}

function concat_perf_events {

    local EVENTS_BY_CONFIG_FILE=$1
    local PROCESSOR_VENDOR=$2
    local PROCESSOR_MICROARCHITECTURE=$3
    local PROCESSOR_VERSION=$4

    echo "$(yq "(.vendors[] | select(.name == $PROCESSOR_VENDOR)).perf_default_events + ((.vendors[] | select(.name == $PROCESSOR_VENDOR)).microarchitectures[] | select(.name == $PROCESSOR_MICROARCHITECTURE).perf_specific_events)" $EVENTS_BY_CONFIG_FILE )"

}

function concat_hwpc_rapl_events {

    local EVENTS_BY_CONFIG_FILE=$1
    local PROCESSOR_VENDOR=$2
    local PROCESSOR_MICROARCHITECTURE=$3
    local PROCESSOR_VERSION=$4

    echo "$(yq "(.vendors[] | select(.name == $PROCESSOR_VENDOR)).hwpc_default_events.rapl + ((.vendors[] | select(.name == $PROCESSOR_VENDOR)).microarchitectures[] | select(.name == $PROCESSOR_MICROARCHITECTURE).hwpc_specific_events.rapl)" $EVENTS_BY_CONFIG_FILE )"

}

function concat_hwpc_msr_events {

    local EVENTS_BY_CONFIG_FILE=$1
    local PROCESSOR_VENDOR=$2
    local PROCESSOR_MICROARCHITECTURE=$3
    local PROCESSOR_VERSION=$4

    echo "$(yq "(.vendors[] | select(.name == $PROCESSOR_VENDOR)).hwpc_default_events.msr + ((.vendors[] | select(.name == $PROCESSOR_VENDOR)).microarchitectures[] | select(.name == $PROCESSOR_MICROARCHITECTURE).hwpc_specific_events.msr)" $EVENTS_BY_CONFIG_FILE )"

}

function concat_hwpc_core_events {

    local EVENTS_BY_CONFIG_FILE=$1
    local PROCESSOR_VENDOR=$2
    local PROCESSOR_MICROARCHITECTURE=$3
    local PROCESSOR_VERSION=$4

    echo "$(yq "(.vendors[] | select(.name == $PROCESSOR_VENDOR)).hwpc_default_events.core + ((.vendors[] | select(.name == $PROCESSOR_VENDOR)).microarchitectures[] | select(.name == $PROCESSOR_MICROARCHITECTURE).hwpc_specific_events.core)" $EVENTS_BY_CONFIG_FILE )"

}

