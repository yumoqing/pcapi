#!/bin/bash
# GPU节点
# sudo bash install_offline.sh gpu
# 控制节点或普通工作节点
# sudo bash install_offline.sh
set -e

OFFLINE_DIR="/opt/offline"

# -------------------------------
# 1. 安装依赖
# -------------------------------
dpkg -i $OFFLINE_DIR/dependencies/*.deb || apt-get -f install -y

# -------------------------------
# 2. 安装 containerd
# -------------------------------
tar -C /usr/local -xzf $OFFLINE_DIR/containerd/containerd-*.tar.gz
ln -s /usr/local/bin/containerd /usr/bin/containerd
ln -s /usr/local/bin/containerd-shim /usr/bin/containerd-shim
ln -s /usr/local/bin/ctr /usr/bin/ctr
containerd --version

# -------------------------------
# 3. 安装 Kubernetes
# -------------------------------
cp $OFFLINE_DIR/k8s/kubeadm /usr/bin/
cp $OFFLINE_DIR/k8s/kubelet /usr/bin/
cp $OFFLINE_DIR/k8s/kubectl /usr/bin/
chmod +x /usr/bin/kubeadm /usr/bin/kubelet /usr/bin/kubectl

# -------------------------------
# 4. GPU 节点额外安装 NVIDIA 驱动与 runtime
# -------------------------------
if [ "$1" == "gpu" ]; then
    chmod +x $OFFLINE_DIR/nvidia/NVIDIA-DRIVER.run
    $OFFLINE_DIR/nvidia/NVIDIA-DRIVER.run --silent
    dpkg -i $OFFLINE_DIR/nvidia/nvidia-container-toolkit.deb
    dpkg -i $OFFLINE_DIR/nvidia/nvidia-container-runtime.deb
fi

# -------------------------------
# 5. 启动 containerd & kubelet
# -------------------------------
systemctl enable containerd --now
systemctl enable kubelet --now

echo "Offline install completed on $(hostname)"

