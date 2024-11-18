{% for core_value in core_values %}
  {% for cpu_ops_per_core in cpu_ops_per_core_list %}
touch {{ results_directory }}/perf_alone_{{ core_value }}_{{ cpu_ops_per_core }} 
for i in {1..{{ nb_iterations }}}; do
### PERF with {{ core_value }} CPU * {{ cpu_ops_per_core }} OPS
    sudo-g5k bash -c "perf stat -a -o /tmp/perf_alone_{{ core_value }}_{{ cpu_ops_per_core }}_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} & echo \$!" > /tmp/perf_pid_$i
    PERF_PID=$(cat /tmp/perf_pid_$i)
    stress-ng --cpu {{ core_value }} --cpu-ops {{ core_value * cpu_ops_per_core }} -q 
    sleep 1s
    sudo-g5k kill -2 $PERF_PID
    cat /tmp/perf_alone_{{ core_value }}_{{ cpu_ops_per_core }}_$i >> {{ results_directory }}/perf_alone_{{ core_value }}_{{ cpu_ops_per_core }}
done
  {% endfor %}
{% endfor %}

