sudo-g5k apt-get install -y stress-ng
g5k-setup-docker
docker login -u {{ docker_hub_username }} -p {{ docker_hub_token }}
docker run --rm -d --name mongo -p 27017:27017 mongo:latest
sleep 30
