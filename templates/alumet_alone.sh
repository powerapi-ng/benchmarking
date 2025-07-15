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

{% for core_value in core_values %}
  {% for cpu_ops_per_core in cpu_ops_per_core_list %}
mkdir -p {{ results_directory }}/alumet_alone_${CORE_VALUE}_${CPU_OPS_PER_CORE}
echo "domain,energy,iteration" > {{ results_directory }}/alumet_alone_${CORE_VALUE}_${CPU_OPS_PER_CORE}.csv
for i in {1..{{ nb_iterations }}}; do
### ALUMET with ${CORE_VALUE} CPU * ${CPU_OPS_PER_CORE} OPS
    ${SUDO_CMD}bash -c "alumet --plugins 'csv,rapl' --output '/tmp/alumet_alone_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i}.csv' & echo \$!" > /tmp/alumet_pid_$i
    ALUMET_PID=$(cat /tmp/alumet_pid_$i)
    while ! (grep 'rapl' /tmp/alumet_alone_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i}.csv); do sleep 0.02s ; done
    stress-ng --cpu ${CORE_VALUE} --cpu-ops $(( CPU_OPS_PER_CORE * CORE_VALUE )) -q
    sleep 1s
    ${SUDO_CMD}kill -2 $ALUMET_PID
    cat /tmp/alumet_alone_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i}.csv | grep rapl | awk -v ITER=$i -F';' '{printf("%s,%s,%s\n",$8,$3,ITER)}' >> {{ results_directory }}/alumet_alone_${CORE_VALUE}_${CPU_OPS_PER_CORE}.csv
done
  {% endfor %}
{% endfor %}

