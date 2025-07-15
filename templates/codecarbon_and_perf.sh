### codecarbon with ${CORE_VALUE} CPU * ${CPU_OPS_PER_CORE} OPS
      TEMPERATURE_START=$(get_average_temperature)
      ${SUDO_CMD}bash -c "codecarbon monitor 1 --no-api > /tmp/codecarbon_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i} 2>&1 & echo \$!" > /tmp/codecarbon_pid_$i
      CODECARBON_PID=$(cat /tmp/codecarbon_pid_$i)
      ${SUDO_CMD}bash -c "perf stat -a -o /tmp/perf_and_codecarbon_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} & echo \$!" > /tmp/perf_pid_$i
      PERF_PID=$(cat /tmp/perf_pid_$i)
      while ! (grep 'Energy consumed for All CPU' /tmp/codecarbon_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i}); do sleep 0.02s ; done
      stress-ng --cpu ${CORE_VALUE} --cpu-ops $(( CORE_VALUE * CPU_OPS_PER_CORE )) -q
      sleep 1s
      TEMPERATURE_STOP=$(get_average_temperature)
      ${SUDO_CMD}kill -2 $CODECARBON_PID
      ${SUDO_CMD}kill -2 $PERF_PID
      cat /tmp/codecarbon_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i} | grep 'Energy consumed for All CPU' | tail -1 | cut -d':' -f4 | awk -v ITER=$i '{printf("%s,%s,%s\n","CPU",$1,ITER)}' >> {{ results_directory }}/codecarbon_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}.csv
      cat /tmp/codecarbon_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i} | grep 'Energy consumed for RAM' | tail -1 | cut -d':' -f4 | awk -v ITER=$i '{printf("%s,%s,%s\n","RAM",$1,ITER)}' >> {{ results_directory }}/codecarbon_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}.csv
      cat /tmp/perf_and_codecarbon_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i} >> {{ results_directory }}/perf_and_codecarbon_${CORE_VALUE}_${CPU_OPS_PER_CORE}
      echo "$TEMPERATURE_START, $TEMPERATURE_STOP, $i" >> {{ results_directory }}/perf_and_codecarbon_${CORE_VALUE}_${CPU_OPS_PER_CORE}_temperatures.csv

