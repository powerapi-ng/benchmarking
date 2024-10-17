#!/bin/bash
set +x
set -euo pipefail
IFS=$'\n\t'

# Example complete url : https://api.grid5000.fr/stable/sites/lille/clusters/chiclet/nodes/chiclet-1.json?pretty
BASE_API_URI="https://api.grid5000.fr/stable/"
SITES_ENDPOINT="sites"
CLUSTERS_ENDPOINT="clusters"
NODES_ENDPOINT="nodes"
NODE_ENDPOINT=""
NODE_ENDPOINT_SUFFIX=".json?pretty"

# SSH Proxy used to hit API
PROXY_SERVER=${1:-"g5k"}

### LOGGING
APP_NAME="inventory"
SCRIPT_LOGGING_LEVEL="${LOG_LEVEL:-"DEBUG"}"
source ./logging.sh
function inventoryLogThis {
    logThis "inventory" "$1" "$2"
}

function api_call {

    local ENDPOINT=$1
    inventoryLogThis "Scrapping ${ENDPOINT}" "INFO"

    ssh "${PROXY_SERVER}" curl -s "$ENDPOINT"

}

function main {
    inventoryLogThis "Starting Benchmarks !" "INFO"

    SITES="$(api_call ${BASE_API_URI}${SITES_ENDPOINT})"
    mapfile -t SITES_UID < <(echo "${SITES}" | yq '.items[] | .uid')
    inventoryLogThis "Found sites: ${SITES_UID[*]}" "DEBUG"
    
    for SITE_UID in "${SITES_UID[@]}"; do
        inventoryLogThis "Processing site: ${SITE_UID}" "DEBUG"
        
        SITE_API_URI="${BASE_API_URI}${SITES_ENDPOINT}/${SITE_UID}/"
        CLUSTERS="$(api_call ${SITE_API_URI}${CLUSTERS_ENDPOINT})"
        mapfile -t CLUSTERS_UID < <(echo "${CLUSTERS}" | yq '.items[] | .uid')
        inventoryLogThis "Found clusters: ${CLUSTERS_UID[*]}" "DEBUG"

        for CLUSTER_UID in "${CLUSTERS_UID[@]}"; do
            inventoryLogThis "Processing cluster: ${SITE_UID}/${CLUSTER_UID}" "DEBUG"
            
            CLUSTER_API_URI="${SITE_API_URI}${CLUSTERS_ENDPOINT}/${CLUSTER_UID}/"
            NODES="$(api_call ${CLUSTER_API_URI}${NODES_ENDPOINT})"
            mapfile -t NODES_UID < <(echo "${NODES}" | yq '.items[] | .uid')
            inventoryLogThis "Found nodes: ${NODES_UID[*]}" "DEBUG"


            for NODE_UID in "${NODES_UID[@]}"; do
                inventoryLogThis "Processing node: ${SITE_UID}/${CLUSTER_UID}/${NODE_UID}" "DEBUG"
                
                NODE_API_URI="${CLUSTER_API_URI}/${NODES_ENDPOINT}/${NODE_UID}${NODE_ENDPOINT_SUFFIX}"
                NODE_SPEC="$(api_call ${NODE_API_URI})"

                inventoryLogThis "Found node: ${NODES_UID} with configuration ${NODE_SPEC}" "DEBUG"
            
                exit
            done
        done 

    done
}


main
