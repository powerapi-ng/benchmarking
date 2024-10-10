#!/bin/bash

g5k-setup-docker -t

mkdir result-cpu-60-min-several-instances-$(date +"%FT%H%M")

docker run --rm -d --net=host --privileged --pid=host --name "hwpc-sensor" -v /sys:/sys -v /var/lib/docker/containers:/var/lib/docker/containers:ro -v /tmp/powerapi-sensor-reporting:/reporting -v $(pwd):/srv -v $(pwd)/result-cpu-60-min-several-instances-$(date +"%FT%H%M"):/result-cpu-60-min-several-instances-$(date >


for i in {1..13}
do
        docker run --rm --name "cpu-60-min-several-instances" ghcr.io/colinianking/stress-ng --cpu 0 --cpu-method all -t 60m --times >> result-cpu-60-min-several-instances-$(date +"%FT%H%M").txt
done

docker stop hwpc-sensor
