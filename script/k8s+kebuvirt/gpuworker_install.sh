#!/bin/bash
# worker-gpu-install.sh
# 在每个有 A100 的 GPU 节点上运行

set -e

OFFLINE_DIR=/opt/offline

# 安装 containerd、k8s 二进制（同上）
tar --no-overwrite-dir -C /usr/local -xzf ${OFFLINE_DIR}/containerd.tar.gz
mkdir -p /opt/cni/bin
tar -xzf ${OFFLINE_DIR}/cni-plugins.tgz -C /opt/cni/bin/

cp ${OFFLINE_DIR}/k8s-binaries/kubeadm /usr/bin/
cp ${OFFLINE_DIR}/k8s-binaries/kubelet /usr/bin/
chmod +x /usr/bin/kubeadm /usr/bin/kubelet

# 配置 containerd 和 kubelet（同上）
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

# 安装 NVIDIA 驱动
echo "=== 安装 NVIDIA 驱动 ==="
chmod +x ${OFFLINE_DIR}/nvidia/NVIDIA-Linux-x86_64-*.run
${OFFLINE_DIR}/nvidia/NVIDIA-Linux-x86_64-535.161.08.run -s --dkms --no-opengl-files

# 加载内核模块
modprobe nvidia
modprobe nvidia-uvm

# 安装 NVIDIA Container Toolkit
dpkg -i ${OFFLINE_DIR}/nvidia/nvidia-container-toolkit*.deb
systemctl restart containerd

# 开启 MIG 模式（A100 必须）
echo "=== 配置 MIG 模式 ==="
# 示例：每张卡切分为 2 个 MIG 实例（可根据需求调整）
nvidia-smi -i 0 -mig 1
sleep 5
# 创建实例（示例：创建两个 3g.20gb 实例）
nvidia-smi mig -i 0 -cgi 3g.20gb,3g.20gb -C
nvidia-smi mig -i 1 -cgi 3g.20gb,3g.20gb -C
# ... 对所有卡重复

# 标记节点为 GPU 节点
cat > /tmp/gpu-label.yaml << 'EOF'
apiVersion: v1
kind: Node
metadata:
  name: $(hostname)
  labels:
    node-type: gpu-worker
    nvidia.com/gpu.present: "true"
EOF

# 注意：join 后再应用 label
echo "✅ 安装完成，请先加入集群"
echo "然后在 master 上运行：kubectl label node $(hostname) node-type=gpu-worker nvidia.com/gpu.present=true"
