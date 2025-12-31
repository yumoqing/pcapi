#!/bin/bash
# control-plane-node-install.sh
# 运行在主控节点（假设 IP: 192.168.10.10）

set -e

OFFLINE_DIR=/opt/offline
K8S_VERSION=v1.29.6
CONTROL_PLANE_IP=192.168.10.10
API_SERVER_NAME=k8s-api.internal

echo "=== 解压离线包 ==="
tar -xzf ${OFFLINE_DIR}/k8s-offline-all.tar.gz -C /tmp/

# 安装基础依赖
dpkg -i ${OFFLINE_DIR}/debs/*.deb || apt-get -f install -y

echo "=== 安装 containerd ==="
mkdir -p /usr/local/bin
tar --no-overwrite-dir -C /usr/local -xzf ${OFFLINE_DIR}/containerd.tar.gz

# 写入 systemd 服务
cat > /etc/systemd/system/containerd.service << 'EOF'
[Unit]
Description=containerd daemon
After=network.target

[Service]
ExecStartPre=/sbin/modprobe overlay
ExecStart=/usr/local/bin/containerd
Restart=always
Type=notify
Delegate=yes
KillMode=process

[Install]
WantedBy=multi-user.target
EOF

systemctl enable containerd
systemctl start containerd

# 安装 CNI 插件
mkdir -p /opt/cni/bin
tar -xzf ${OFFLINE_DIR}/cni-plugins.tgz -C /opt/cni/bin/

# 安装 k8s 二进制
cp ${OFFLINE_DIR}/k8s-binaries/* /usr/bin/
chmod +x /usr/bin/kubeadm /usr/bin/kubelet /usr/bin/kubectl

# kubelet systemd 设置
cat > /etc/systemd/system/kubelet.service << 'EOF'
[Unit]
Description=kubelet
After=containerd.service
Requires=containerd.service

[Service]
ExecStart=/usr/bin/kubelet
Restart=always
StartLimitInterval=0
VolumeMountPropagation=private
Environment="KUBELET_EXTRA_ARGS=--container-runtime=remote --runtime-request-timeout=15m --container-runtime-endpoint=unix:///run/containerd/containerd.sock"

[Install]
WantedBy=multi-user.target
EOF

systemctl enable kubelet

echo "=== 初始化集群 ==="
kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --apiserver-advertise-address=${CONTROL_PLANE_IP} \
  --kubernetes-version=${K8S_VERSION} \
  --ignore-preflight-errors=all

mkdir -p $HOME/.kube
cp /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

echo "=== 安装 Flannel CNI ==="
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml

# 标记主节点不调度 Pod（可选）
kubectl taint nodes $(hostname) node-role.kubernetes.io/control-plane:NoSchedule

echo "✅ 控制节点安装完成"
echo "请将 ~/.kube/config 复制到其他节点或管理机"
