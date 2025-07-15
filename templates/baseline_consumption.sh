GLOBAL_BASELINE_MEASUREMENT_DURATION_SECONDS=900
# Timer for the baseline measurement
START_BASELINE=$(date +%s)
BASELINE_CONSUMPTION_FILE={{ results_directory }}/baseline_consumption.csv
NUMBER_OF_TOP_PROCESSES=10
ITERATION_STEP_INTERVAL_SECONDS=5
PERF_STAT_FILE=/tmp/perf_stat_file

echo "timestamp,pkg,average_temperature,cpu_percent,mem_percent,process_1,process_2,process_3,process_4,process_5,process_6,process_7,process_8,process_9,process_10" > "${BASELINE_CONSUMPTION_FILE}"
# Init because of strict variables check on expression evaluation
NOW=$(date +%s)
while [[ $((NOW - START_BASELINE)) -lt ${GLOBAL_BASELINE_MEASUREMENT_DURATION_SECONDS} ]] ; do
  # Timer for the current iteration of the measurement
  # We break into multiple small iteration to have view of running processors that could have an impact
  TEMPERATURE_START=$(get_average_temperature)
  PROCESSES=$(ps aux --sort -%cpu | head -$((NUMBER_OF_TOP_PROCESSES + 1)) | tail -${NUMBER_OF_TOP_PROCESSES} )
  ${SUDO_CMD}perf stat -a -o ${PERF_STAT_FILE} -e /power/energy-pkg/ sleep ${ITERATION_STEP_INTERVAL_SECONDS}
  TEMPERATURE_STOP=$(get_average_temperature)
  AVERAGE_TEMPERATURE=$(( (TEMPERATURE_START + TEMPERATURE_STOP) / 2 ))
  PKG_CONSUMPTION=$(grep "Joules" "${PERF_STAT_FILE}" | awk '{print $1}' | cut -d',' -f1)

  echo "$PROCESSES" | awk -v TIMESTAMP="$(date +%s)" -v TEMPERATURE="${AVERAGE_TEMPERATURE}" -v PKG_CONSUMPTION="${PKG_CONSUMPTION}" '{cpu+=$3; ram+=$4; names=names"\"" $11"\","} END {printf("%s,%s,%s,%s,%s,%s\n",TIMESTAMP,PKG_CONSUMPTION,TEMPERATURE,cpu,ram,substr(names,1,length(names)-1))}' >> "${BASELINE_CONSUMPTION_FILE}"
  NOW=$(date +%s)
done