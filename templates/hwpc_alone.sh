{% for core_value in core_values %}
for i in {1..{{ nb_iterations }}}; do
    ### HWPC sensor dedicated to stress-ng with {{ core_value }} CPU * {{ cpu_ops_per_core }} OPS 
    docker run --rm -d --net=host --privileged --pid=host --name {{ hwpc_alone_configs.get(core_value).unwrap().name }}_$i \
        -v /sys:/sys \
        -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
        -v /tmp/power-api-sensor-reporting:/reporting \
        -v $(pwd):{{ hwpc_home_directory }} \
        powerapi/hwpc-sensor:1.4.0 \
        -n {{ hwpc_alone_configs.get(core_value).unwrap().name }}_$i \
        -p {{ hwpc_alone_configs.get(core_value).unwrap().cgroup_basepath }} \
        -r {{ hwpc_alone_configs.get(core_value).unwrap().output.type }} -U {{ hwpc_home_directory }}/{{ hwpc_alone_configs.get(core_value).unwrap().output.directory }}_$i \
        -s "rapl" {%~ for event in hwpc_alone_configs.get(core_value).unwrap().system.rapl.events %}-e "{{ event }}" {% endfor %} \
        -s "msr" {%~ for event in hwpc_alone_configs.get(core_value).unwrap().system.msr.events %}-e "{{ event }}" {% endfor %} \
        -c "core" {%~ for event in hwpc_alone_configs.get(core_value).unwrap().system.core.events %}-e "{{ event }}" {% endfor %} 
    stress-ng --cpu {{ core_value }} --cpu-ops {{ core_value * cpu_ops_per_core }} -q 
    docker rm -f {{ hwpc_alone_configs.get(core_value).unwrap().name }}_$i 
    sleep 15
done

{% endfor %}
