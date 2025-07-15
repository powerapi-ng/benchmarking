{% if os_flavor != super::DEFAULT_OS_FLAVOR %}
curl -sSL https://get.docker.com/ | sh
sudo curl -sSL "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo mkdir -p /etc/docker
echo "{ \"registry-mirrors\": [\"http://docker-cache.grid5000.fr\"] }" | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
sudo chmod o+rw /var/run/docker.sock
SUDO_CMD=""
{% else %}
g5k-setup-docker
SUDO_CMD="sudo-g5k "
{% endif %}


${SUDO_CMD}apt-get install -y stress-ng
${SUDO_CMD}apt-get install -y lm-sensors

${SUDO_CMD}rm -f /etc/apt/sources.list.d/repo.radeon.com-amdgpu.list
docker login -u {{ docker_hub_username }} -p {{ docker_hub_token }}
docker run --rm -d --name mongo -p 27017:27017 mongo:latest
sleep 30

${SUDO_CMD}wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/local/bin/yq
${SUDO_CMD}chmod +x /usr/local/bin/yq