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
        done 
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
