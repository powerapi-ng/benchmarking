GLOBAL_BASELINE_MEASUREMENT_DURATION_SECONDS=900
# Timer for the baseline measurement
START_BASELINE=$(date +%s)
BASELINE_CONSUMPTION_FILE={{ results_directory }}/baseline_consumption.csv
NUMBER_OF_TOP_PROCESSES=10
OBSERVATION_DURATION_SECONDS=120
ITERATION_STEP_INTERVAL_SECONDS=5
PERF_STAT_FILE=/tmp/perf_stat_file
TIMEOUT_STRESS=60
CPU_LOAD_STRESS=95


echo "timestamp,pkg,ram,average_temperature,cpu_percent,mem_percent,process_1,process_2,process_3,process_4,process_5,process_6,process_7,process_8,process_9,process_10" > "${BASELINE_CONSUMPTION_FILE}"
# Init because of strict variables check on expression evaluation
NOW=$(date +%s)

#### NOW
while [[ $((NOW - START_BASELINE)) -lt ${GLOBAL_BASELINE_MEASUREMENT_DURATION_SECONDS} ]] ; do


  stress-ng --cpu 0 --cpu-load ${CPU_LOAD_STRESS} --timeout ${TIMEOUT_STRESS} 

  # Observe for this temperature range
  OBSERVATION_START=$(date +%s)
  while [[ $((NOW - OBSERVATION_START)) -lt ${OBSERVATION_DURATION_SECONDS} ]] ; do

    TEMPERATURE_START=$(get_average_temperature)
    PROCESSES=$(ps aux --sort -%cpu | head -$((NUMBER_OF_TOP_PROCESSES + 1)) | tail -${NUMBER_OF_TOP_PROCESSES})
    ${SUDO_CMD} perf stat -a -o "${PERF_STAT_FILE}" {% for perf_event in perf_events.iter() %}-e {{ perf_event }} {% endfor %} sleep ${ITERATION_STEP_INTERVAL_SECONDS}
    TEMPERATURE_STOP=$(get_average_temperature)
    AVERAGE_TEMPERATURE=$(( (TEMPERATURE_START + TEMPERATURE_STOP) / 2 ))

    PKG_CONSUMPTION=$(grep "Joules" "${PERF_STAT_FILE}" | grep "pkg" | awk '{print $1}' | cut -d',' -f1 || echo "0")
    RAM_CONSUMPTION=$(grep "Joules" "${PERF_STAT_FILE}" | grep "ram" | awk '{print $1}' | cut -d',' -f1 || echo "0")
    echo "$PROCESSES" | awk -v TIMESTAMP="$(date +%s.%N)" -v TEMPERATURE="${AVERAGE_TEMPERATURE}" -v PKG_CONSUMPTION="${PKG_CONSUMPTION}" -v RAM_CONSUMPTION="${RAM_CONSUMPTION}" '{cpu+=$3; ram+=$4; names=names"\"" $11"\","} END {printf("%s,%s,%s,%s,%s,%s,%s\n",TIMESTAMP,PKG_CONSUMPTION,RAM_CONSUMPTION,TEMPERATURE,cpu,ram,substr(names,1,length(names)-1))}' >> "${BASELINE_CONSUMPTION_FILE}"

    NOW=$(date +%s)
  done

done

echo "Baseline measurement complete."



