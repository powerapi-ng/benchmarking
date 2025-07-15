#!/bin/bash
set -x
set -ueo pipefail

{% include "oar_directives.sh" %}

SECONDS=0


{% include "install_packages.sh" %}
{% include "rust_setup.sh" %}

{% if codecarbon_alone || codecarbon_and_perf %}
${SUDO_CMD}apt install -y python3.12-venv stress-ng python3-pip
cd /tmp
git clone https://github.com/mlco2/codecarbon.git
python3.12 -m venv codecarbon/
source codecarbon/bin/activate
sed -i 's/Timer(self.interval, self._run)/Timer(self.interval\/1000, self._run)/' codecarbon/codecarbon/external/scheduler.py
pip install /tmp/codecarbon
${SUDO_CMD}ln -s /home/nleblond/.local/bin/codecarbon /usr/local/bin/codecarbon
{% endif %}


{% if alumet_alone || alumet_and_perf %}
${SUDO_CMD}apt install -y build-essential libssl-dev pkg-config
cd /tmp
git clone https://github.com/alumet-dev/alumet.git
git config --global --add safe.directory /tmp/alumet
cd alumet
git checkout "v0.7.0"
cd app-agent
cargo build --release --features local_x86
${SUDO_CMD}ln -s $(realpath ../target/release/alumet-local-agent) /usr/local/bin/alumet
cd /home/nleblond
alumet regen-config
{% endif %}

{% if scaphandre_alone || scaphandre_and_perf %}
${SUDO_CMD}apt install -y build-essential libssl-dev pkg-config
cd /tmp
git clone https://github.com/hubblo-org/scaphandre.git
git clone https://github.com/borntyping/rust-riemann_client.git
git config --global --add safe.directory /tmp/rust-riemann_client
git config --global --add safe.directory /tmp/scaphandre
sed -i 's/\#!\[rustfmt::skip\]//' rust-riemann_client/src/proto/mod_pb.rs | head -10
cd scaphandre
git checkout "v1.0.1"
sed -i 's/riemann_client = { version = "0.9.0"/riemann_client = { path = "..\/rust-riemann_client"/' Cargo.toml
cargo build --release
${SUDO_CMD}ln -s $(realpath ./target/release/scaphandre) /usr/local/bin/scaphandre
cd /home/nleblond
{% endif %}

{% if vjoule_alone || vjoule_and_perf %}
cd /tmp
wget https://github.com/davidson-consulting/vjoule/releases/download/v1.3.0/vjoule-tools_1.3.0.deb
dpkg -i vjoule-tools_1.3.0.deb
${SUDO_CMD}systemctl start vjoule_service
cd /home/nleblond

${SUDO_CMD}systemctl status vjoule_service
sleep 30
${SUDO_CMD}systemctl status vjoule_service
{% endif %}

{% include "results_directory_preparation.sh" %}


get_average_temperature() {
	NB_SENSORS=$(sensors | grep "Package id" | wc -l)
	SUM_TEMP=$(sensors | grep "Package id" | awk '{print $4}' | cut -d'+' -f2 | cut -d'.' -f1 | paste -sd'+' | bc)
	AVG_TMP=$(( SUM_TEMP / NB_SENSORS ))
	echo $AVG_TMP
}

{% include "baseline_consumption.sh" %}

{% include "warmup.sh" %}

{% for target_frequency in target_frequencies %}

PERF_AND_HWPC_FREQUENCY_FILE="{{ results_directory }}/frequency_{{ target_frequency }}_perf_and_hwpc"
PERF_AND_HWPC_FREQUENCY_TEMPERATURES_FILE="{{ results_directory }}/temperatures_frequency_{{ target_frequency }}_perf_and_hwpc.csv"
HWPC_AND_PERF_FREQUENCY_DIR="{{ results_directory }}/frequency_{{ target_frequency }}_hwpc_and_perf"
touch $PERF_AND_HWPC_FREQUENCY_FILE
mkdir -p $HWPC_AND_PERF_FREQUENCY_DIR
echo "temperature_start,temperature_stop,iteration" > $PERF_AND_HWPC_FREQUENCY_TEMPERATURES_FILE

PERF_AND_CODECARBON_FREQUENCY_FILE="{{ results_directory }}/frequency_{{ target_frequency }}_perf_and_codecarbon"
PERF_AND_CODECARBON_FREQUENCY_TEMPERATURES_FILE="{{ results_directory }}/temperatures_frequency_{{ target_frequency }}_perf_and_codecarbon.csv"
CODECARBON_AND_PERF_FREQUENCY_FILE="{{ results_directory }}/frequency_{{ target_frequency }}_codecarbon_and_perf.csv"
touch $PERF_AND_CODECARBON_FREQUENCY_FILE
echo "domain,timestamp,energy,iteration" > $CODECARBON_AND_PERF_FREQUENCY_FILE
echo "temperature_start,temperature_stop,iteration" > $PERF_AND_CODECARBON_FREQUENCY_TEMPERATURES_FILE

PERF_AND_ALUMET_FREQUENCY_FILE="{{ results_directory }}/frequency_{{ target_frequency }}_perf_and_alumet"
PERF_AND_ALUMET_FREQUENCY_TEMPERATURES_FILE="{{ results_directory }}/temperatures_frequency_{{ target_frequency }}_perf_and_alumet.csv"
ALUMET_AND_PERF_FREQUENCY_FILE="{{ results_directory }}/frequency_{{ target_frequency }}_alumet_and_perf.csv"
ALUMET_AND_PERF_FREQUENCY_DIR="{{ results_directory }}/frequency_{{ target_frequency }}_alumet_and_perf"
touch $PERF_AND_ALUMET_FREQUENCY_FILE
echo "domain,timestamp,energy,iteration" > $ALUMET_AND_PERF_FREQUENCY_FILE
echo "temperature_start,temperature_stop,iteration" > $PERF_AND_ALUMET_FREQUENCY_TEMPERATURES_FILE
mkdir -p $ALUMET_AND_PERF_FREQUENCY_DIR

PERF_AND_SCAPHANDRE_FREQUENCY_FILE="{{ results_directory }}/frequency_{{ target_frequency }}_perf_and_scaphandre"
PERF_AND_SCAPHANDRE_FREQUENCY_TEMPERATURES_FILE="{{ results_directory }}/temperatures_frequency_{{ target_frequency }}_perf_and_scaphandre.csv"
SCAPHANDRE_AND_PERF_FREQUENCY_FILE="{{ results_directory }}/frequency_{{ target_frequency }}_scaphandre_and_perf.csv"
touch $PERF_AND_SCAPHANDRE_FREQUENCY_FILE
echo "domain,timestamp,energy,iteration" > $SCAPHANDRE_AND_PERF_FREQUENCY_FILE
echo "temperature_start,temperature_stop,iteration" > $PERF_AND_SCAPHANDRE_FREQUENCY_TEMPERATURES_FILE

PERF_AND_VJOULE_FREQUENCY_FILE="{{ results_directory }}/frequency_{{ target_frequency }}_perf_and_vjoule"
PERF_AND_VJOULE_FREQUENCY_TEMPERATURES_FILE="{{ results_directory }}/temperatures_frequency_{{ target_frequency }}_perf_and_vjoule.csv"
VJOULE_AND_PERF_FREQUENCY_FILE="{{ results_directory }}/frequency_{{ target_frequency }}_vjoule_and_perf.csv"
touch $PERF_AND_VJOULE_FREQUENCY_FILE
echo "domain,timestamp,energy,iteration" > $VJOULE_AND_PERF_FREQUENCY_FILE
echo "temperature_start,temperature_stop,iteration" > $PERF_AND_VJOULE_FREQUENCY_TEMPERATURES_FILE

for i in {1..{{ nb_iterations_frequencies }}}; do
  export i=$i

{% if frequencies_benchmark %}
{% include "frequencies_benchmark.sh" %}
{% endif %}

done

{% endfor %}


{% for core_value in core_values %}
CORE_VALUE={{ core_value }}
  {% for cpu_ops_per_core in cpu_ops_per_core_list %}
CPU_OPS_PER_CORE={{ cpu_ops_per_core }}

touch {{ results_directory }}/perf_and_hwpc_{{ core_value }}_{{ cpu_ops_per_core }}
mkdir -p {{ results_directory }}/hwpc_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}
echo "temperature_start, temperature_stop, iteration" > {{ results_directory }}/perf_and_hwpc_{{ core_value }}_{{ cpu_ops_per_core }}_temperatures.csv

echo "domain,energy,iteration" >  {{ results_directory }}/codecarbon_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}.csv
echo "temperature_start, temperature_stop, iteration" > {{ results_directory }}/perf_and_codecarbon_{{ core_value }}_{{ cpu_ops_per_core }}_temperatures.csv
touch {{ results_directory }}/perf_and_codecarbon_${CORE_VALUE}_${CPU_OPS_PER_CORE}

echo "domain,energy,iteration" > {{ results_directory }}/alumet_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}.csv
echo "temperature_start, temperature_stop, iteration" > {{ results_directory }}/perf_and_alumet_{{ core_value }}_{{ cpu_ops_per_core }}_temperatures.csv
mkdir -p {{ results_directory }}/alumet_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}
touch {{ results_directory }}/perf_and_alumet_${CORE_VALUE}_${CPU_OPS_PER_CORE}

echo "domain,energy,iteration" > {{ results_directory }}/scaphandre_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}.csv
echo "temperature_start, temperature_stop, iteration" > {{ results_directory }}/perf_and_scaphandre_{{ core_value }}_{{ cpu_ops_per_core }}_temperatures.csv
touch {{ results_directory }}/perf_and_scaphandre_{{ core_value }}_{{ cpu_ops_per_core }}

touch {{ results_directory }}/vjoule_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}.csv
echo "domain,energy,iteration" > {{ results_directory }}/vjoule_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}.csv
touch {{ results_directory }}/perf_and_vjoule_{{ core_value }}_{{ cpu_ops_per_core }}
echo "temperature_start, temperature_stop, iteration" > {{ results_directory }}/perf_and_vjoule_{{ core_value }}_{{ cpu_ops_per_core }}_temperatures.csv

for i in {1..{{ nb_iterations }}}; do

{% if perf_alone %}
{% include "perf_alone.sh" %}
{% endif %}

{% if hwpc_alone %}
{% include "hwpc_alone.sh" %}
{% endif %}

{% if codecarbon_alone %}
{% include "codecarbon_alone.sh" %}
{% endif %}

{% if alumet_alone %}
{% include "alumet_alone.sh" %}
{% endif %}

{% if scaphandre_alone %}
{% include "scaphandre_alone.sh" %}
{% endif %}

{% if vjoule_alone %}
{% include "vjoule_alone.sh" %}
{% endif %}

{% if hwpc_and_perf %}
{% include "hwpc_and_perf.sh" %}
{% endif %}

{% if codecarbon_and_perf %}
{% include "codecarbon_and_perf.sh" %}
{% endif %}

{% if alumet_and_perf %}
{% include "alumet_and_perf.sh" %}
{% endif %}

{% if scaphandre_and_perf %}
{% include "scaphandre_and_perf.sh" %}
{% endif %}

{% if vjoule_and_perf %}
{% include "vjoule_and_perf.sh" %}
{% endif %}

done

  {% endfor %}
{% endfor %}


{% include "zip_results.sh" %}


{% include "exit.sh" %}
