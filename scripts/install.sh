#!/bin/bash
set -e

REPO_URL="https://github.com/Seeed-Studio/SenseCraft-AI_Server.git"
BRANCH_TAG="jetson"
REPO_DIR="$HOME/sensecraft-ai_server"
YOLO_MODEL_URL="https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt"
DOCKER_VERSION="27.0"

function print_msg() {
  echo -e "\n==== $1 ====\n"
}

function check_command() {
  command -v "$1" >/dev/null 2>&1
}

function install_docker() {
  print_msg "Step 1: Installing Docker"

  if check_command docker; then
    echo "Docker is already installed, skipping."
  else
    echo "Updating apt and installing prerequisites..."
    sudo apt update
    sudo apt install -y nvidia-container-toolkit curl jq

    echo "Downloading Docker install script..."
    curl -fsSL https://get.docker.com -o install-docker.sh

    echo "Installing Docker version $DOCKER_VERSION..."
    sudo sh install-docker.sh --version $DOCKER_VERSION

    echo "Enabling Docker service..."
    sudo systemctl --now enable docker

    echo "Configuring NVIDIA Container Toolkit for Docker runtime..."
    sudo nvidia-ctk runtime configure --runtime=docker

    echo "Updating Docker daemon.json to set default-runtime to nvidia..."
    if [ -f /etc/docker/daemon.json ]; then
      sudo jq '. + {"default-runtime": "nvidia"}' /etc/docker/daemon.json | sudo tee /etc/docker/daemon.json.tmp
      sudo mv /etc/docker/daemon.json.tmp /etc/docker/daemon.json
    else
      echo '{"default-runtime": "nvidia"}' | sudo tee /etc/docker/daemon.json
    fi

    echo "Reloading and restarting Docker service..."
    sudo systemctl daemon-reload
    sudo systemctl restart docker

    echo "Cleaning up install script..."
    rm -f install-docker.sh

    echo "Docker installation completed."
  fi
}

function install_mqtt() {
  print_msg "Step 2: Installing MQTT Broker (Mosquitto)"

  if systemctl is-active --quiet mosquitto; then
    echo "Mosquitto service is already running, skipping installation."
  else
    echo "Installing mosquitto and clients..."
    sudo apt update
    sudo apt install -y mosquitto mosquitto-clients

    echo "Configuring Mosquitto to listen on all interfaces with anonymous access..."
    sudo bash -c 'echo -e "\nlistener 1883 0.0.0.0\nallow_anonymous true" >> /etc/mosquitto/mosquitto.conf'

    echo "Reloading systemd daemon and restarting Mosquitto service..."
    sudo systemctl daemon-reload
    sudo systemctl restart mosquitto
    sudo systemctl enable mosquitto

    echo "Mosquitto installation and configuration completed."
  fi
}

function install_service() {
  print_msg "Step 3: Installing SenseCraft AI Server"

  if [ -d "$REPO_DIR" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd "$REPO_DIR"
    git fetch
    git reset --hard origin/$BRANCH_TAG
  else
    echo "Cloning repository..."
    git clone --branch "$BRANCH_TAG" "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
  fi

  echo "Checking out "$BRANCH_TAG" branch..."
  git checkout "$BRANCH_TAG"

  echo "Running service startup script..."
  bash scripts/run.sh

  if [ ! -f "yolo11n.pt" ]; then
    echo "Downloading YOLOv11 general model..."
    wget "$YOLO_MODEL_URL"
  else
    echo "YOLOv11 model already downloaded, skipping."
  fi

  echo "SenseCraft AI Server setup completed."
}

function main() {
  print_msg "Starting One-Click Deployment Script for Jetson Ubuntu 22 with Jetpack 6.x"

  install_docker || { echo "Docker installation failed. Please check network and retry."; exit 1; }
  install_mqtt || { echo "MQTT installation failed. Please check apt sources and retry."; exit 1; }
  install_service || { echo "Service installation failed. Please check repository and retry."; exit 1; }

  print_msg "All steps completed successfully. You can now configure the model and camera source via the settings page and access the homepage."
}

main
