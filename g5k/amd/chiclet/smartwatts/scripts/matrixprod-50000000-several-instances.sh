#!/bin/bash

g5k-setup-docker -t

docker run --rm -d --name mongo_source -p 27017:27017 mongo:latest

sleep 15

docker run --rm -d --net=host --privileged --pid=host --name "hwpc-sensor" -v /sys:/sys -v /var/lib/docker/containers:/var/lib/docker/containers:ro -v /tmp/powerapi-sensor-reporting:/reporting -v $(pwd):/srv powerapi/hwpc-sensor:latest -n "$(hostname -f)" -r "mongodb" -U "mongodb://127.0.0.1" -D "db_hwpc" -C "report" -s "rapl" -o -e "RAPL_ENERGY_PKG" -s "msr" -e "TSC" -e "APERF" -e "MPERF" -c "core" -e "CYCLES_NOT_IN_HALT" -e "RETIRED_INSTRUCTIONS" -e "RETIRED_UOPS" -p "/sys/fs/cgroup/perf_event"

sleep 15

mkdir result-matrixprod-50000000-op-several-instances-$(date +"%FT%H%M")

chmod -R a+rw result-matrixprod-50000000-op-several-instances-$(date +"%FT%H%M")

docker run --rm -d --name smartwatts --net=host --privileged -v $(pwd)/result-matrixprod-50000000-op-several-instances-$(date +"%FT%H%M"):/result-matrixprod-50000000-op-several-instances-$(date +"%FT%H%M") powerapi/smartwatts-formula:latest --stream --input mongodb --model HWPCReport --uri mongodb://127.0.0.1 --db db_hwpc --collection report --output csv --model PowerReport --directory /result-matrixprod-50000000-op-several-instances-$(date +"%FT%H%M") --cpu-base-freq 2200 --cpu-error-threshold 2.0 --disable-dram-formula --sensor-reports-frequency 1000



for i in {1..20}
do
	docker run --rm --name "matrixprod-50000000-op-several-instances" ghcr.io/colinianking/stress-ng --cpu 0 --cpu-method matrixprod --cpu-ops 50000000 --times >> result-matrixprod-50000000-op-several-instances-$(date +"%FT%H%M").txt
done

docker stop hwpc-sensor
docker stop smartwatts
docker stop mongo_source
