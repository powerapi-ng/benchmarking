### SCAPHANDRE with ${CORE_VALUE} CPU * ${CPU_OPS_PER_CORE} OPS
      TEMPERATURE_START=$(get_average_temperature)
      ${SUDO_CMD}bash -c "scaphandre stdout --timeout=-1 -s 1 -p 0 > /tmp/scaphandre_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i & echo \$!" > /tmp/scaphandre_pid_$i
      SCAPHANDRE_PID=$(cat /tmp/scaphandre_pid_$i)
      ${SUDO_CMD}bash -c "perf stat -a -o /tmp/perf_and_scaphandre_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} & echo \$!" > /tmp/perf_pid_$i
      PERF_PID=$(cat /tmp/perf_pid_$i)
      while ! (grep 'consumers' /tmp/scaphandre_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}_${i}); do sleep 0.02s ; done
      stress-ng --cpu ${CORE_VALUE} --cpu-ops $(( CPU_OPS_PER_CORE * CORE_VALUE )) -q
      sleep 1s
      TEMPERATURE_STOP=$(get_average_temperature)
      ${SUDO_CMD}kill -2 $SCAPHANDRE_PID
      cat /tmp/scaphandre_and_perf_${CORE_VALUE}_{{ cpu_ops_per_core}}_$i | grep "Host" | awk -v ITER=$i '{printf("%s,%s,%s\n","pkg",$2,ITER)}' >> {{ results_directory }}/scaphandre_and_perf_${CORE_VALUE}_${CPU_OPS_PER_CORE}.csv
      ${SUDO_CMD}kill -2 $PERF_PID
      cat /tmp/perf_and_scaphandre_${CORE_VALUE}_${CPU_OPS_PER_CORE}_$i >> {{ results_directory }}/perf_and_scaphandre_${CORE_VALUE}_${CPU_OPS_PER_CORE}
      echo "$TEMPERATURE_START, $TEMPERATURE_STOP, $i" >> {{ results_directory }}/perf_and_scaphandre_${CORE_VALUE}_${CPU_OPS_PER_CORE}_temperatures.csv

