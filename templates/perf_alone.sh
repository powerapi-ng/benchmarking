{% for core_value in core_values %}
### PERF with {{ core_value }} CPU * {{ cpu_ops_by_core }} OPS
sudo perf stat -a -o {{ results_directory }}/perf_alone_{{ core_value }} {% for perf_event in perf_events.iter() %}-e "{{ perf_event }}" {% endfor %}  stress-ng --cpu {{ core_value }} --cpu-ops {{ core_value * cpu_ops_by_core }} -q 

{% endfor %}

