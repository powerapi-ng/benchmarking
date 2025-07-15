      TEMPERATURE_START=$(get_average_temperature)
      ${SUDO_CMD}bash -c "perf stat -a -o /tmp/perf_and_vjoule_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} & echo \$!" > /tmp/perf_pid_$i
      PERF_PID=$(cat /tmp/perf_pid_$i)
      vjoule stress-ng --cpu ${CORE_VALUE} --cpu-ops $(( CORE_VALUE * CPU_OPS_PER_CORE )) -- > /tmp/vjoule_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i
      TEMPERATURE_STOP=$(get_average_temperature)
      cat /tmp/vjoule_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i | grep "RAM" | awk -v ITER=$i '{printf("%s,%s,%s\n","RAM",$2,ITER)}' >> {{ results_directory }}/vjoule_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}.csv
      cat /tmp/vjoule_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i | grep "CPU" | awk -v ITER=$i '{printf("%s,%s,%s\n","CPU",$2,ITER)}' >> {{ results_directory }}/vjoule_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}.csv
      ${SUDO_CMD}kill -2 $PERF_PID
      cat /tmp/perf_and_vjoule_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i >> {{ results_directory }}/perf_and_vjoule_${CORE_VALUE}_${CPU_OPS_PER_CORE}
      echo "$TEMPERATURE_START, $TEMPERATURE_STOP, $i" >> {{ results_directory }}/perf_and_vjoule_${CORE_VALUE}_${CPU_OPS_PER_CORE}_temperatures.csv

