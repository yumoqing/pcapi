#!/bin/bash
set -e
mkdir -p /opt/offline/{k8s,containerd,kubevirt,nvidia,dependencies}

# -------------------------------
# 1. Ubuntu 22.04 系统依赖
# -------------------------------
sudo apt update
DEBS="curl conntrack socat ipvsadm iptables bridge-utils ethtool git wget tar"
mkdir -p /opt/offline/dependencies
for pkg in $DEBS; do
    apt download $pkg
    mv *.deb /opt/offline/dependencies/
done

# -------------------------------
# 2. Kubernetes 组件
# -------------------------------
K8S_VERSION="1.29.0"
mkdir -p /opt/offline/k8s
cd /opt/offline/k8s
curl -LO https://dl.k8s.io/release/v${K8S_VERSION}/bin/linux/amd64/kubeadm
curl -LO https://dl.k8s.io/release/v${K8S_VERSION}/bin/linux/amd64/kubelet
curl -LO https://dl.k8s.io/release/v${K8S_VERSION}/bin/linux/amd64/kubectl
chmod +x kubeadm kubelet kubectl

# -------------------------------
# 3. Containerd
# -------------------------------
CONTAINERD_VERSION="1.9.12"
cd /opt/offline/containerd
wget https://github.com/containerd/containerd/releases/download/v${CONTAINERD_VERSION}/containerd-${CONTAINERD_VERSION}-linux-amd64.tar.gz

# -------------------------------
# 4. NVIDIA Container Toolkit & Drivers
# -------------------------------
mkdir -p /opt/offline/nvidia
# 下载 NVIDIA driver (根据 GPU 型号自行选择)
# 示例: NVIDIA-Linux-x86_64-525.85.12.run
wget -O /opt/offline/nvidia/NVIDIA-DRIVER.run http://us.download.nvidia.com/XFree86/Linux-x86_64/525.85.12/NVIDIA-Linux-x86_64-525.85.12.run
# 下载 NVIDIA container toolkit
wget -O /opt/offline/nvidia/nvidia-container-toolkit.deb https://github.com/NVIDIA/nvidia-docker/releases/download/v2.13.0/nvidia-container-toolkit_2.13.0-1_all.deb
wget -O /opt/offline/nvidia/nvidia-container-runtime.deb https://github.com/NVIDIA/nvidia-docker/releases/download/v2.13.0/nvidia-container-runtime_2.13.0-1_amd64.deb

# -------------------------------
# 5. KubeVirt Operator + CR
# -------------------------------
mkdir -p /opt/offline/kubevirt
curl -L https://github.com/kubevirt/kubevirt/releases/download/v1.28.0/kubevirt-operator.yaml -o /opt/offline/kubevirt/kubevirt-operator.yaml
curl -L https://github.com/kubevirt/kubevirt/releases/download/v1.28.0/kubevirt-cr.yaml -o /opt/offline/kubevirt/kubevirt-cr.yaml

# -------------------------------
# 6. GPU Operator
# -------------------------------
mkdir -p /opt/offline/nvidia/gpu-operator
curl -L https://github.com/NVIDIA/gpu-operator/archive/refs/heads/main.tar.gz -o /opt/offline/nvidia/gpu-operator/gpu-operator.tar.gz

echo "Offline package download completed. All packages are in /opt/offline/"

