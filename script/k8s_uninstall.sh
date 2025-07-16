#!/bin/bash

# 停止K8s相关服务
echo "停止K8s相关服务..."
ps -aux | grep Opera | grep -v grep | awk '{print $2}' | xargs kill -9
systemctl stop kubelet
echo "移除缓存忘卡配置"
ip link delete cni0
systemctl stop kube-apiserver

systemctl stop nfs-kernel-server
rm -rf /k8sdata/*

# 执行kubeadm reset
echo "执行kubeadm reset..."
kubeadm reset -f

apt-get purge kubelet kubectl kubeadm kubernetes-cni -y --allow-change-held-packages
rm -rf /etc/cni/net.d

rm -rf /var/lib/kubelet /var/lib/kubernetes
rm -rf /etc/kubernetes/manifests
rm -rf /etc/kubernetes/pki
rm -rf /etc/kubernetes
rm -rf /var/lib/etcd
rm -rf /var/lib/cni
rm -rf /var/lib/docker
rm -rf /var/lib/containerd
rm -rf /var/lib/etcd
rm -rf /var/lib/kubelet
rm -rf /var/lib/kube-proxy
# 删除K8s配置文件
echo "删除K8s配置文件..."
sudo rm -rf /etc/kubernetes

# 删除K8s相关二进制文件（假设在/usr/local/bin）
echo "删除K8s相关二进制文件..."
sudo rm /usr/local/bin/kube*

# 清理Containerd数据（谨慎操作）
echo "清理Containerd数据..."
sudo rm -rf /var/lib/containerd /usr/bin/containerd*
sudo apt purge -y containerd containerd.io cri-tools --allow-change-held-packages
rm -rf /etc/containerd /var/lib/containerd /run/containerd
rm -f /etc/systemd/system/multi-user.target.wants/containerd.service
rm /lib/systemd/system/containerd.service
systemctl daemon-reload

# 清理iptables规则
echo "清理iptables规则..."
# sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F && sudo iptables -X
# ipvsadm --clear
apt autoremove -y
apt autoclean -y
apt clean -y
apt update -y

# 停止docker
echo "停止docker并清理..."
docker rmi $(docker images -q)
docker stop $(docker ps -aq) && docker rm $(docker ps -aq) && sudo systemctl stop docker
sudo systemctl stop docker.service
sudo systemctl stop docker.socket
rm -rf /etc/docker/daemon.json
rm -rf /usr/bin/docker-compose

# 清理Docker
apt-get purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras -y --allow-change-held-packages
apt purge -y containerd.io containerd

# 检查并删除当前root用户的kubeconfig文件
echo "检查并删除当前root用户的kubeconfig文件..."
sudo rm -rf $HOME/.kube/config

# kubord
echo "清理kuboard相关配置..."
sed -i '/\/opt \*(rw,sync,no_root_squash)/d' /etc/exports

rm -rf /etc/apt/sources.list.d/docker*
rm -rf /etc/apt/sources.list.d/kubernetes*
rm -rf /etc/apt/sources.list.d/kuboard*

apt autoremove -y
apt autoclean -y
apt clean -y

echo "恭喜你!!! K8s相关内容已清理, 可准备重新安装。"
