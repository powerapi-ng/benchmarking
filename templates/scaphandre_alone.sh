${SUDO_CMD}apt install -y build-essential libssl-dev pkg-config
cd /tmp
git clone https://github.com/hubblo-org/scaphandre.git
git config --global --add safe.directory /tmp/scaphandre
cd scaphandre
git checkout "v1.0.1"
cargo build --release
${SUDO_CMD}ln -s $(realpath ./target/release/scaphandre) /usr/local/bin/scaphandre
cd /home/nleblond

{% for core_value in core_values %}
  {% for cpu_ops_per_core in cpu_ops_per_core_list %}
echo "domain,energy,iteration" > {{ results_directory }}/scaphandre_alone_{{ core_value }}_{{ cpu_ops_per_core }}.csv
for i in {1..{{ nb_iterations }}}; do
### SCAPHANDRE with {{ core_value }} CPU * {{ cpu_ops_per_core }} OPS
    ${SUDO_CMD}bash -c "scaphandre stdout --timeout=-1 -s 1 -p 0 > /tmp/scaphandre_alone_{{ core_value }}_{{ cpu_ops_per_core }}_$i & echo \$!" > /tmp/scaphandre_pid_$i
    SCAPHANDRE_PID=$(cat /tmp/scaphandre_pid_$i)
    while ! (grep 'consumers' /tmp/scaphandre_alone_{{ core_value }}_{{ cpu_ops_per_core }}_${i}); do sleep 0.02s ; done
    stress-ng --cpu {{ core_value }} --cpu-ops {{ core_value * cpu_ops_per_core }} -q 
    sleep 1s
    ${SUDO_CMD}kill -2 $SCAPHANDRE_PID
    cat /tmp/scaphandre_alone_{{ core_value }}_{{ cpu_ops_per_core}}_$i | grep "Host" | awk -v ITER=$i '{printf("%s,%s,%s\n","pkg",$2,ITER)}' >> {{ results_directory }}/scaphandre_alone_{{ core_value }}_{{ cpu_ops_per_core }}.csv
done
  {% endfor %}
{% endfor %}

