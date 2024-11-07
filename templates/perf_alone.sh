{% for core_value in core_values %}
touch {{ results_directory }}/perf_alone_{{ core_value }} 
for i in {1..{{ nb_iterations }}}; do
### PERF with {{ core_value }} CPU * {{ cpu_ops_per_core }} OPS
    sudo perf stat -a -o /tmp/perf_alone_{{ core_value }}_$i {% for perf_event in perf_events.iter() %}-e "{{ perf_event }}" {% endfor %}  stress-ng --cpu {{ core_value }} --cpu-ops {{ core_value * cpu_ops_per_core }} -q 
    cat /tmp/perf_alone_{{ core_value }}_$i >> {{ results_directory }}/perf_alone_{{ core_value }} 
done
{% endfor %}

