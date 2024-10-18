#!/bin/bash

set +x
set -ueo pipefail

source .env

### TASKS 
TASKS_DIR="./tasks.d"
TASKS_FIFO=${TASKS_DIR}/tasks_fifo.tmp
source libs/tasks.sh

### LOGGING
SCRIPT_LOGGING_LEVEL="${LOG_LEVEL:-"DEBUG"}"
source libs/logging.sh

### Inventory
source libs/inventory.sh

logThis "main" "Starting Benchmarks !" "INFO" || true
logThis "main" "LOG_LEVEL is : $SCRIPT_LOGGING_LEVEL" "DEBUG" || true
if [[ -e "$TASKS_FIFO" ]]; then
    
    read -n1 -p "Remaining TASKS found in $TASKS_FIFO, do you wish to process those ? (Current bench will stop once done) [y,n]" processit
    case $processit in  
      y|Y) processes_tasks $TASKS_FIFO;; 
      n|N) echo "Backup remaining tasks (only latest saved) and start whole benchmark process" && cp $TASKS_FIFO ${TASKS_FIFO}.bck && rm -f $TASKS_FIFO && main ;;
      *) echo "" && echo "ERROR: only y or n accepted" ;; 
    esac
else
    main
fi
exit

