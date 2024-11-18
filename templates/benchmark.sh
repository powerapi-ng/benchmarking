#!/bin/bash
set -x
set -ueo pipefail

{% include "oar_directives.sh" %}

SECONDS=0
########################
### INSTALL PACKAGES ###
########################
{% include "install_packages.sh" %}

#################################
### CREATES RESULTS_DIRECTORY ###
#################################
{% include "results_directory_preparation.sh" %}

{% if perf_alone %}
#################
### ONLY PERF ###
#################
{% include "perf_alone.sh" %}
{% endif %}

{% if hwpc_alone %}
#################
### ONLY HWPC ###
#################
{% include "hwpc_alone.sh" %}
{% endif %}

{% if hwpc_and_perf %}
###################
### HWPC & PERF ###
###################
{% include "hwpc_and_perf.sh" %}
{% endif %}

#############################
### ZIP RESULTS_DIRECTORY ###
#############################
{% include "zip_results.sh" %}

############
### EXIT ###
############
duration=$SECONDS
echo "$(($diff / 3600)) hours, $((duration / 60)) minutes and $((duration % 60)) seconds elapsed."
{% include "exit.sh" %}
