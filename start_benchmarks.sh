#!/bin/bash
set +x
source ./*.sh

fn usage() {
  echo "usage: $0 INVENTORY_FILE"
  exit
}

# Variables

INVENTORY_FILE=$1
TASKS_SETS=$2

# Check that tools are available or offer to download or crash

prepare_toolbox

# Read inventory

read_inventory $INVENTORY_FILE

## Read tasks sets

read_tasks_sets $2

## Generate tasks stack

TASKS=generate_tasks

for TAKS in $TASKS
do
    push_task_to_stack $TASK
done

while ! empty_stack
do
    TASK=pick_from_tasks_stack
    if submission_available
    do
        oarsub $TASK
        scp results
        scp metadata
        add_metadata_to_results
    else
        sleep 60
    fi
done

echo "Let's cool off !"


