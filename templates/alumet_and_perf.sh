### ALUMET with ${CORE_VALUE} CPU * ${CPU_OPS_PER_CORE} OPS
      TEMPERATURE_START=$(get_average_temperature)
      sed -i 's/poll_interval = "[0-9]*m\{0,1\}s"/poll_interval = "1000ms"/' /home/{{ g5k_username }}/alumet-config.toml
      ${SUDO_CMD}bash -c "alumet --plugins 'csv,rapl' --output '/tmp/alumet_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i}.csv' & echo \$!" > /tmp/alumet_pid_$i
      ALUMET_PID=$(cat /tmp/alumet_pid_$i)
      ${SUDO_CMD}bash -c "perf stat -a -o /tmp/perf_and_alumet_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} & echo \$!" > /tmp/perf_pid_$i
      PERF_PID=$(cat /tmp/perf_pid_$i)
      while ! (grep 'rapl' /tmp/alumet_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i}.csv); do sleep 0.02s ; done
      stress-ng --cpu ${CORE_VALUE} --cpu-ops $(( CPU_OPS_PER_CORE * CORE_VALUE )) -q
      sleep 1s
      TEMPERATURE_STOP=$(get_average_temperature)
      ${SUDO_CMD}kill -2 $ALUMET_PID
      cat /tmp/alumet_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i}.csv | grep rapl | awk -v ITER=$i -F';' '{printf("%s,%s,%s\n",$8,$3,ITER)}' >> {{ results_directory }}/alumet_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}.csv
      ${SUDO_CMD}kill -2 $PERF_PID
      sleep 5s
      cat /tmp/perf_and_alumet_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i >> {{ results_directory }}/perf_and_alumet_${CORE_VALUE}_${CPU_OPS_PER_CORE}
      echo "$TEMPERATURE_START, $TEMPERATURE_STOP, $i" >> {{ results_directory }}/perf_and_alumet_${CORE_VALUE}_${CPU_OPS_PER_CORE}_temperatures.csv

