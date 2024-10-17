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
INVENTORY_DIRECTORY="./inventories.d"

# SSH Proxy used to hit API
PROXY_SERVER=${1:-"g5k"}



### LOGGING
APP_NAME="inventory"
SCRIPT_LOGGING_LEVEL="${LOG_LEVEL:-"DEBUG"}"
source libs/logging.sh
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
    
    for SITE_UID in "${SITES_UID[@]}"; do
        inventoryLogThis "Processing site: ${SITE_UID}" "DEBUG"
        mkdir -p $INVENTORY_DIRECTORY/$SITE_UID/
        
        SITE_API_URI="${BASE_API_URI}${SITES_ENDPOINT}/${SITE_UID}/"
        CLUSTERS="$(api_call ${SITE_API_URI}${CLUSTERS_ENDPOINT})"
        mapfile -t CLUSTERS_UID < <(echo "${CLUSTERS}" | yq '.items[] | .uid')

        for CLUSTER_UID in "${CLUSTERS_UID[@]}"; do
            inventoryLogThis "Processing cluster: ${SITE_UID}/${CLUSTER_UID}" "DEBUG"
            mkdir $INVENTORY_DIRECTORY/$SITE_UID/$CLUSTER_UID/
            
            CLUSTER_API_URI="${SITE_API_URI}${CLUSTERS_ENDPOINT}/${CLUSTER_UID}/"
            NODES="$(api_call ${CLUSTER_API_URI}${NODES_ENDPOINT})"
            mapfile -t NODES_UID < <(echo "${NODES}" | yq '.items[] | .uid')


            for NODE_UID in "${NODES_UID[@]}"; do
                inventoryLogThis "Processing node: ${SITE_UID}/${CLUSTER_UID}/${NODE_UID}" "DEBUG"

                NODE_API_URI="${CLUSTER_API_URI}/${NODES_ENDPOINT}/${NODE_UID}${NODE_ENDPOINT_SUFFIX}"
                api_call ${NODE_API_URI} > "$INVENTORY_DIRECTORY/$SITE_UID/$CLUSTER_UID/$NODE_UID.json"

                break

            
            done
        done 

    done
}


main
