#!/bin/bash

set -x
set -ueo pipefail

source .env

### JOBS 
JOBS_DIR="./jobs.d"
JOBS_FILE="${JOBS_DIR}/jobs.json"
source libs/jobs.sh

### LOGGING
LOGGIN_DIR="./logs.d"
SCRIPT_LOGGING_LEVEL="${LOG_LEVEL:-"DEBUG"}"
source libs/logging.sh

### Inventory
INVENTORY_DIR="./inventory.d"
source libs/inventory.sh

### Results
RESULTS_DIR="./results.d"
source libs/results.sh

logThis "main" "Starting Benchmarks !" "INFO" || true
logThis "main" "LOG_LEVEL is : $SCRIPT_LOGGING_LEVEL" "DEBUG" || true

function main {

    #generate_inventory $INVENTORY_DIR

    SKIP=${1:-""}
    if [[ -z $SKIP ]]; then
        generate_jobs $JOBS_FILE
    fi
    process_jobs $JOBS_FILE $RESULTS_DIR

    echo "process_results $RESULTS_DIR"

    echo "report_results $RESULTS_DIR"
}

# -e to match mkfifo kind of file if ever switch to
if [[ -e "${JOBS_FILE}" ]]; then
    read -n1 -p "Remaining JOBS found in ${JOBS_FILE}, do you wish to process those ? (Current bench will stop once done) [y,n]" processit
    case $processit in  
      y|Y) main ${JOBS_FILE};; 
      n|N) echo -e "\nBackup remaining jobs (only latest saved) and start whole benchmark process" \
           && (cp $JOBS_FILE ${JOBS_FILE}.bck \
               && echo "${JOBS_FILE}.bck file created for backup") \
           && rm -f $JOBS_FILE \
           && main ;;
      *) echo -e "\nERROR: only y or n accepted" ;; 
    esac
else
    main
fi
exit


