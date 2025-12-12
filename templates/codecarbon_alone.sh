${SUDO_CMD}apt install -y python3.12-venv stress-ng
python3.12 -m venv codecarbon
cd codecarbon/
source bin/activate
pip install codecarbon
cd /home/{{ g5k_username }}

{% for core_value in core_values %}
  {% for cpu_ops_per_core in cpu_ops_per_core_list %}
echo "domain,energy,iteration" >  {{ results_directory }}/codecarbon_alone_{{ core_value }}_{{ cpu_ops_per_core }}.csv
for i in {1..{{ nb_iterations }}}; do
### codecarbon with {{ core_value }} CPU * {{ cpu_ops_per_core }} OPS
    ${SUDO_CMD}bash -c "codecarbon monitor 1 --no-api > /tmp/codecarbon_alone_{{ core_value }}_{{ cpu_ops_per_core }}_${i} 2>&1 & echo \$!" > /tmp/codecarbon_pid_$i
    CODECARBON_PID=$(cat /tmp/codecarbon_pid_$i)
    while ! (grep 'Energy consumed for all CPU' /tmp/codecarbon_alone_{{ core_value }}_{{ cpu_ops_per_core }}_${i}); do sleep 0.02s ; done
    stress-ng --cpu {{ core_value }} --cpu-ops {{ core_value * cpu_ops_per_core }} -q 
    sleep 1s
    ${SUDO_CMD}kill -2 $CODECARBON_PID
    cat /tmp/codecarbon_alone_{{ core_value }}_{{ cpu_ops_per_core }}_${i} | grep 'Energy consumed for all CPU' | tail -1 | cut -d':' -f4 | awk -v ITER=$i '{printf("%s,%s,%s\n","CPU",$1,ITER)}' >> {{ results_directory }}/codecarbon_alone_{{ core_value }}_{{ cpu_ops_per_core }}.csv
    cat /tmp/codecarbon_alone_{{ core_value }}_{{ cpu_ops_per_core }}_${i} | grep 'Energy consumed for RAM' | tail -1 | cut -d':' -f4 | awk -v ITER=$i '{printf("%s,%s,%s\n","RAM",$1,ITER)}' >> {{ results_directory }}/codecarbon_alone_{{ core_value }}_{{ cpu_ops_per_core }}.csv
done
  {% endfor %}
{% endfor %}

