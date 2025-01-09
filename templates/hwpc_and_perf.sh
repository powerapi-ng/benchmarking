{% for core_value in core_values %}
  {% for cpu_ops_per_core in cpu_ops_per_core_list %}
touch {{ results_directory }}/perf_and_hwpc_{{ core_value }}_{{ cpu_ops_per_core }} 
mkdir -p {{ results_directory }}/hwpc_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}
for i in {1..{{ nb_iterations }}}; do
    ### HWPC sensor dedicated to stress-ng with {{ core_value }} CPU * {{ cpu_ops_per_core }} OPS 
    docker run --rm -d --net=host --privileged --pid=host --name {{ hwpc_and_perf_configs.get(core_value).unwrap().name }}_{{ cpu_ops_per_core }}_$i \
        -v /sys:/sys \
        -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
        -v /tmp/power-api-sensor-reporting:/reporting \
        -v $(pwd):{{ hwpc_home_directory }} \
        powerapi/hwpc-sensor:1.4.0 \
        -n {{ hwpc_and_perf_configs.get(core_value).unwrap().name }}_{{ cpu_ops_per_core }}_$i \
        -p {{ hwpc_and_perf_configs.get(core_value).unwrap().cgroup_basepath }} \
        -r {{ hwpc_and_perf_configs.get(core_value).unwrap().output.type }} -U {{ hwpc_home_directory }}/{{ results_directory }}/hwpc_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}/hwpc_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}_$i \
        {% if  hwpc_alone_configs.get(core_value).unwrap().system.rapl.events.len() > 0 %} -s "rapl" {%~ for event in hwpc_alone_configs.get(core_value).unwrap().system.rapl.events %}-e "{{ event }}" {% endfor %}{% endif %} {% if  hwpc_alone_configs.get(core_value).unwrap().system.msr.events.len() > 0 %} -s "msr" {%~ for event in hwpc_alone_configs.get(core_value).unwrap().system.msr.events %}-e "{{ event }}" {% endfor %} {% endif %} {% if  hwpc_alone_configs.get(core_value).unwrap().system.core.events.len() > 0 %} -c "core" {%~ for event in hwpc_alone_configs.get(core_value).unwrap().system.core.events %}-e "{{ event }}" {% endfor %} {% endif %}

    ${SUDO_CMD}bash -c "perf stat -a -o /tmp/perf_and_hwpc_{{ core_value }}_{{ cpu_ops_per_core }}_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} & echo \$!" > /tmp/perf_pid_$i
    PERF_PID=$(cat /tmp/perf_pid_$i)
    while ! [[ -e "{{ results_directory }}/hwpc_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}/hwpc_and_perf_{{ core_value }}_{{ cpu_ops_per_core }}_$i/rapl.csv" ]]; do sleep 0.02s ; done
    ### PERF with {{ core_value }} CPU * {{ cpu_ops_per_core }} OPS
    stress-ng --cpu {{ core_value }} --cpu-ops {{ core_value * cpu_ops_per_core }} -q 
    sleep 1s

    ${SUDO_CMD}kill -2 $PERF_PID
    docker stop {{ hwpc_and_perf_configs.get(core_value).unwrap().name }}_{{ cpu_ops_per_core }}_$i
    cat /tmp/perf_and_hwpc_{{ core_value }}_{{ cpu_ops_per_core }}_$i >> {{ results_directory }}/perf_and_hwpc_{{ core_value }}_{{ cpu_ops_per_core }}
    sleep 15
done

    {% endfor %}
{% endfor %}
