cd /tmp
wget https://github.com/davidson-consulting/vjoule/releases/download/v1.3.0/vjoule-tools_1.3.0.deb
dpkg -i vjoule-tools_1.3.0.deb
${SUDO_CMD}systemctl start vjoule_service
cd /home/{{ g5k_username }}

${SUDO_CMD}systemctl status vjoule_service
sleep 30
${SUDO_CMD}systemctl status vjoule_service


{% for core_value in core_values %}
  {% for cpu_ops_per_core in cpu_ops_per_core_list %}
touch {{ results_directory }}/vjoule_alone_{{ core_value }}_{{ cpu_ops_per_core }}.csv
echo "domain,energy,iteration" > {{ results_directory }}/vjoule_alone_{{ core_value }}_{{ cpu_ops_per_core }}.csv
for i in {1..{{ nb_iterations }}}; do
### vjoule with {{ core_value }} CPU * {{ cpu_ops_per_core }} OPS
    vjoule stress-ng --cpu {{ core_value }} --cpu-ops {{ core_value * cpu_ops_per_core }} -- > /tmp/vjoule_alone_{{ core_value }}_{{ cpu_ops_per_core }}_$i
    cat /tmp/vjoule_alone_{{ core_value }}_{{ cpu_ops_per_core }}_$i | grep "RAM" | awk -v ITER=$i '{printf("%s,%s,%s\n","RAM",$2,ITER)}' >> {{ results_directory }}/vjoule_alone_{{ core_value }}_{{ cpu_ops_per_core }}.csv
    cat /tmp/vjoule_alone_{{ core_value }}_{{ cpu_ops_per_core }}_$i | grep "CPU" | awk -v ITER=$i '{printf("%s,%s,%s\n","CPU",$2,ITER)}' >> {{ results_directory }}/vjoule_alone_{{ core_value }}_{{ cpu_ops_per_core }}.csv
done
  {% endfor %}
{% endfor %}

