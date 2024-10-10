#!/bin/bash

g5k-setup-docker -t

mkdir result-cpu-10-min-1-instance-$(date +"%FT%H%M")

docker run --rm -d --net=host --privileged --pid=host --name "hwpc-sensor" -v /sys:/sys -v /var/lib/docker/containers:/var/lib/docker/containers:ro -v /tmp/powerapi-sensor-reporting:/reporting -v $(pwd):/srv -v $(pwd)/result-cpu-10-min-1-instance-$(date +"%FT%H%M"):/result-cpu-10-min-1-instance-$(date +"%FT%H%M") powerapi/hwpc-sensor:latest -n "$(hostname -f)" -U /result-cpu-10-min-1-instance-$(date +"%FT%H%M") -s "rapl" -o -e "RAPL_ENERGY_PKG" -s "msr" -e "TSC" -e "APERF" -e "MPERF" -c "core" -e "CPU_CLK_THREAD_UNHALTED:REF_P" -e "CPU_CLK_THREAD_UNHALTED:THREAD_P" -e "LLC_MISSES" -e "INSTRUCTIONS_RETIRED" -p "/sys/fs/cgroup/perf_event"

for i in {1..20}
do
	docker run --rm --name "cpu-10-min-1-instance" ghcr.io/colinianking/stress-ng --cpu 1 --cpu-method all -t 10m --times >> result-cpu-10-min-1-instance-$(date +"%FT%H%M").txt
done

docker stop hwpc-sensor
