  #HWPC RUN
  TEMPERATURE_START=$(get_average_temperature)
  docker run --rm -d --net=host --privileged --pid=host --name hwpc_{{ target_frequency }}_$i \
    -v /sys:/sys \
    -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
    -v /tmp/power-api-sensor-reporting:/reporting \
    -v $(pwd):{{ hwpc_home_directory }} \
    powerapi/hwpc-sensor:1.4.0 \
    -n hwpc_{{ target_frequency }}_$i \
    -f {{ 1000 / target_frequency }} \
    -p {{ hwpc_and_perf_configs.get(core_values[0]).unwrap().cgroup_basepath }} \
    -r {{ hwpc_and_perf_configs.get(core_values[0]).unwrap().output.type }} -U {{ hwpc_home_directory }}/${HWPC_AND_PERF_FREQUENCY_DIR}/frequency_{{ target_frequency }}_hwpc_and_perf_$i \
    {% if  hwpc_and_perf_configs.get(core_values[0]).unwrap().system.rapl.events.len() > 0 %} -s "rapl" -o {{ hwpc_and_perf_configs.get(core_values[0]).unwrap().system.rapl.monitoring_type }} {%~ for event in hwpc_and_perf_configs.get(core_values[0]).unwrap().system.rapl.events %}-e "{{ event }}" {% endfor %}{% endif %} {% if  hwpc_and_perf_configs.get(core_values[0]).unwrap().system.msr.events.len() > 0 %} -s "msr" {%~ for event in hwpc_and_perf_configs.get(core_values[0]).unwrap().system.msr.events %}-e "{{ event }}" {% endfor %} {% endif %} {% if  hwpc_and_perf_configs.get(core_values[0]).unwrap().system.core.events.len() > 0 %} -c "core" {%~ for event in hwpc_and_perf_configs.get(core_values[0]).unwrap().system.core.events %}-e "{{ event }}" {% endfor %} {% endif %}

  ${SUDO_CMD}perf stat -a -o /tmp/frequency_{{ target_frequency }}_perf_and_hwpc_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} sleep 40
  TEMPERATURE_STOP=$(get_average_temperature)
  docker stop hwpc_{{ target_frequency }}_$i
  cat /tmp/frequency_{{ target_frequency }}_perf_and_hwpc_$i >> $PERF_AND_HWPC_FREQUENCY_FILE || true
  echo "$TEMPERATURE_START,$TEMPERATURE_STOP,$i" >> $PERF_AND_HWPC_FREQUENCY_TEMPERATURES_FILE

  #CODECARBON RUN
  TEMPERATURE_START=$(get_average_temperature)
  ${SUDO_CMD}bash -c "codecarbon monitor {{ 1000 / target_frequency }} --no-api > /tmp/frequency_{{ target_frequency }}_codecarbon_and_perf_${i} 2>&1 & echo \$!" > /tmp/codecarbon_pid_$i
  CODECARBON_PID=$(cat /tmp/codecarbon_pid_$i)
  ${SUDO_CMD}perf stat -a -o /tmp/frequency_{{ target_frequency }}_perf_and_codecarbon_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} sleep 40
  TEMPERATURE_STOP=$(get_average_temperature)
  ${SUDO_CMD}kill -2 $CODECARBON_PID
  sleep 10
  cat /tmp/frequency_{{ target_frequency }}_codecarbon_and_perf_${i} | grep 'Energy consumed for All CPU' | awk -F' ' '{print $4" "$5 $12}' | tr ',' '.' | awk -F']' '{print $1" "$2}' | awk -v ITER=$i '{printf("%s,%s %s,%s,%s\n","CPU",$1,$2,$3,ITER)}' >> $CODECARBON_AND_PERF_FREQUENCY_FILE || true
  cat /tmp/frequency_{{ target_frequency }}_codecarbon_and_perf_${i} | grep 'Energy consumed for RAM' | awk -F' ' '{print $4" "$5 $11}' | tr ',' '.' | awk -F']' '{print $1" "$2}' | awk -v ITER=$i '{printf("%s,%s %s,%s,%s\n","RAM",$1,$2,$3,ITER)}' >> $CODECARBON_AND_PERF_FREQUENCY_FILE || true
  cat /tmp/frequency_{{ target_frequency }}_perf_and_codecarbon_${i} >> $PERF_AND_CODECARBON_FREQUENCY_FILE || true
  echo "$TEMPERATURE_START,$TEMPERATURE_STOP,$i" >> $PERF_AND_CODECARBON_FREQUENCY_TEMPERATURES_FILE



  #ALUMET
  TEMPERATURE_START=$(get_average_temperature)
  sed -i 's/poll_interval = "[0-9]*m\{0,1\}s"/poll_interval = "{{ 1000 / target_frequency }}ms"/' /home/{{ g5k_username }}/alumet-config.toml
  ${SUDO_CMD}bash -c "alumet --plugins 'csv,rapl' --output '/tmp/frequency_{{ target_frequency }}_alumet_and_perf_${i}.csv' & echo \$!" > /tmp/alumet_pid_$i
  ALUMET_PID=$(cat /tmp/alumet_pid_$i)
  ${SUDO_CMD}perf stat -a -o /tmp/frequency_{{ target_frequency }}_perf_and_alumet_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} sleep 40
  TEMPERATURE_STOP=$(get_average_temperature)
  ${SUDO_CMD}kill -2 $ALUMET_PID
  sleep 10
  cat /tmp/frequency_{{ target_frequency }}_alumet_and_perf_${i}.csv | grep rapl | awk -v ITER=$i -F';' '{printf("%s,%s,%s,%s\n",$8,$2,$3,ITER)}' >> $ALUMET_AND_PERF_FREQUENCY_FILE || true
  cat /tmp/frequency_{{ target_frequency }}_perf_and_alumet_$i >> $PERF_AND_ALUMET_FREQUENCY_FILE || true
  echo "$TEMPERATURE_START,$TEMPERATURE_STOP,$i" >> $PERF_AND_ALUMET_FREQUENCY_TEMPERATURES_FILE

  #SCAPHANDRE RUN
  TEMPERATURE_START=$(get_average_temperature)
  ${SUDO_CMD}bash -c "scaphandre json -s 0 --step-nano {{ 1000000000 / target_frequency }} -f /tmp/frequency_{{ target_frequency }}_scaphandre_and_perf_$i & echo \$!" > /tmp/scaphandre_pid_$i
  SCAPHANDRE_PID=$(cat /tmp/scaphandre_pid_$i)
  ${SUDO_CMD}perf stat -a -o /tmp/frequency_{{ target_frequency }}_perf_and_scaphandre_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} sleep 40
  TEMPERATURE_STOP=$(get_average_temperature)
  ${SUDO_CMD}kill -2 $SCAPHANDRE_PID
  sleep 10
  yq '.[].host | "package" + "," + .timestamp + "," + .consumption + "," + env(i)' /tmp/frequency_{{ target_frequency }}_scaphandre_and_perf_$i >> $SCAPHANDRE_AND_PERF_FREQUENCY_FILE || true
  cat /tmp/frequency_{{ target_frequency }}_perf_and_scaphandre_$i >> $PERF_AND_SCAPHANDRE_FREQUENCY_FILE
  echo "$TEMPERATURE_START,$TEMPERATURE_STOP,$i" >> $PERF_AND_SCAPHANDRE_FREQUENCY_TEMPERATURES_FILE


  #VJOULE RUN
  TEMPERATURE_START=$(get_average_temperature)
  sed -i "s/freq = [0-9]*/freq = {{ target_frequency }}/" /etc/vjoule/config.toml
  ${SUDO_CMD}systemctl restart vjoule_service.service
  sleep 10
  ${SUDO_CMD}bash -c "vjoule top --output /tmp/frequency_{{ target_frequency }}_vjoule_and_perf_$i 1>/dev/null & echo \$!" > /tmp/vjoule_pid_$i
  VJOULE_PID=$(cat /tmp/vjoule_pid_$i)
  ${SUDO_CMD}perf stat -a -o /tmp/frequency_{{ target_frequency }}_perf_and_vjoule_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} sleep 40
  ${SUDO_CMD}kill -2 $VJOULE_PID
  sleep 10
  TEMPERATURE_STOP=$(get_average_temperature)
  cat /tmp/frequency_{{ target_frequency }}_vjoule_and_perf_$i | tail -n +2 | awk -v ITER=$i -F';' '{printf("%s,%s,%s,%s\n","CPU",$1,$3,ITER)}' >> $VJOULE_AND_PERF_FREQUENCY_FILE || true
  cat /tmp/frequency_{{ target_frequency }}_vjoule_and_perf_$i | tail -n +2 | awk -v ITER=$i -F';' '{printf("%s,%s,%s,%s\n","RAM",$1,$4,ITER)}' >> $VJOULE_AND_PERF_FREQUENCY_FILE || true
  cat /tmp/frequency_{{ target_frequency }}_perf_and_vjoule_$i >> $PERF_AND_VJOULE_FREQUENCY_FILE || true
  echo "$TEMPERATURE_START,$TEMPERATURE_STOP,$i" >> $PERF_AND_VJOULE_FREQUENCY_TEMPERATURES_FILE
