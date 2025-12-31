#!/bin/bash
# worker-cpu-install.sh
# 所有无 GPU 的工作节点运行此脚本

set -e

OFFLINE_DIR=/opt/offline

# 安装 containerd、CNI、k8s 二进制（同 control plane）
tar --no-overwrite-dir -C /usr/local -xzf ${OFFLINE_DIR}/containerd.tar.gz
mkdir -p /opt/cni/bin
tar -xzf ${OFFLINE_DIR}/cni-plugins.tgz -C /opt/cni/bin/

cp ${OFFLINE_DIR}/k8s-binaries/kubeadm /usr/bin/
cp ${OFFLINE_DIR}/k8s-binaries/kubelet /usr/bin/
chmod +x /usr/bin/kubeadm /usr/bin/kubelet

# 同样配置 containerd 和 kubelet
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

echo "✅ 准备加入集群，请在主控节点获取 join 命令："
echo "kubeadm token create --print-join-command"
echo "然后在此节点执行输出的命令"
