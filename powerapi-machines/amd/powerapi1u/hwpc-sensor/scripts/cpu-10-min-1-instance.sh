#!/bin/bash

docker run --rm -d --net=host --privileged --pid=host --name "hwpc-sensor" -v /sys:/sys -v /var/lib/docker/containers:/var/lib/docker/containers:ro -v /tmp/powerapi-sensor-reporting:/reporting -v $(pwd):/srv -v $(pwd)/result-cpu-10-min-1-instance-$(date +"%FT%H%M"):/result-cpu-10-min-1-instance-$(date +"%FT%H%M") powerapi/hwpc-sensor:latest -n "$(hostname -f)" -U /result-cpu-10-min-1-instance-$(date +"%FT%H%M") -s "rapl" -o -e "RAPL_ENERGY_PKG" -s "msr" -e "TSC" -e "APERF" -e "MPERF" -c "core" -e "CYCLES_NOT_IN_HALT" -e "RETIRED_INSTRUCTIONS" -e "RETIRED_UOPS" -p "/sys/fs/cgroup/perf_event"

for i in {1..20}
do
	docker run --rm --name "cpu-10-min-1-instance" ghcr.io/colinianking/stress-ng --cpu 1 --cpu-method all -t 10m --times >> result-cpu-10-min-1-instance-$(date +"%FT%H%M").txt
done

docker stop hwpc-sensor
