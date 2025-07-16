#!/bin/bash

# 停止并删除所有容器和 Pod
echo "Stopping all containers..."
crictl stop $(crictl ps -q) || true
echo "Removing all containers..."
crictl rm $(crictl ps -a -q) || true
echo "Stopping all pods..."
crictl stopp $(crictl pods -q) || true
echo "Removing all pods..."
crictl rmp $(crictl pods -q) || true

# 删除所有镜像（crictl 方式）
echo "Deleting all images via crictl..."
crictl images --quiet | xargs -r crictl rmi || true

# 删除所有镜像（ctr 方式）
echo "Deleting all images via ctr in k8s.io namespace..."
ctr -n=k8s.io images list --quiet | xargs -r ctr -n=k8s.io image rm || true
echo "Deleting all images via ctr in default namespace..."
ctr -n=default images list --quiet | xargs -r ctr -n=default image rm || true

echo "All images and containers have been deleted."
