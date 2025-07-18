#!/bin/bash

# 部分ubuntu操作系统在安装包时会出现交互式图形界面弹窗的形式,此处我们忽略
# 交互式提示的本质：DEBIAN_FRONTEND=noninteractive 是控制apt/dpkg非交互的核心,其他UCF变量和配置文件是补充,确保配置文件冲突时自动选择新 / 旧版本,避免弹窗。
# packagekit 的作用：该服务主要用于图形化包管理,在服务器环境中可停止但无需mask,mask会导致系统无法正常管理该服务及其依赖。

# 禁用包管理交互式提示（不影响系统服务）
export DEBIAN_FRONTEND=noninteractive
export UCF_FORCE_CONFFNEW=1
export UCF_FORCE_CONFFMISS=1
export UCF_FORCE_CONFFIGNORE=1

# 配置apt和dpkg的非交互行为
echo 'Dpkg::Options {
    "--force-confdef";
    "--force-confnew";
}' > /etc/apt/apt.conf.d/99noninteractive
echo 'force-confold' > /etc/dpkg/dpkg.cfg.d/force-confold

# 优化：仅停止packagekit（不mask）
systemctl stop packagekit


echo "########## 安装K8S必须root用户下执行 ###########"
# 检查是否为root用户
if [ "$(id -u)" != "0" ]; then
    echo "请以root用户身份运行此脚本"
    exit 1
fi

# echo "########## 先清理K8S缓存/环境 ###########"
# /opt/k8s_uninstall.sh || log_error "清理K8S环境失败,请检查脚本或手动清理残留"

# 新ubuntu18.04设备环境先换阿里源：
cp /etc/apt/sources.list /etc/apt/sources.list.bak
tee /etc/apt/sources.list << EOF
deb http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse
EOF
apt-get update -y

apt upgrade -y

apt install -y libtss2-esys0 -f 

# 设置脚本在出错时立即退出,并将错误信息输出
set -e
# set -o pipefail

# 函数：输出日志信息
log_info() {
    echo "[INFO] $1"
}

# 函数：输出错误信息并退出
log_error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# 关闭防火墙
# log_info "关闭防火墙..."
# ufw disable || log_error "关闭防火墙失败"

# selinux相关操作
log_info "安装selinux-utils..."
apt install -y selinux-utils || log_error "安装selinux-utils失败"
log_info "设置SELinux为Permissive模式..."
if grep -q "SELINUX=enforcing" /etc/selinux/config || grep -q "SELINUX=permissive" /etc/selinux/config; then
    echo "SELinux已开启"
    setenforce 0 || log_error "设置SELinux模式失败"
    sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config || log_error "修改SELinux配置文件失败"
else
    echo "SELinux未开启"
fi

#安装htop,vim,net-tools
apt install vim htop net-tools -y || log_error "安装htop,vim,net-tools失败"

# 禁止swap分区
log_info "禁止swap分区..."
swapoff -a || log_error "禁止swap分区失败"
# 注释掉swap一行
sed -i '/swap/s/^/#/' /etc/fstab || log_error "注释swap行失败"

# 桥接的IPV4流量传递到iptables 的链
log_info "配置桥接的IPV4流量传递到iptables的链..."
cat > /etc/sysctl.d/k8s.conf <<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sysctl --system || log_error "使sysctl配置生效失败"

# 新增k8s镜像源
log_info "新增k8s镜像源..."
curl -s https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | apt-key add - || log_error "添加k8s镜像源的密钥失败"
echo "deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list
apt-get update -y || log_error "更新apt源失败"

# 安装nfs
# log_info "安装nfs-common..."
# apt-get install -y nfs-common || log_error "安装nfs-common失败"
apt install -y aptitude

# 更新系统并安装必要工具
log_info "更新系统并安装必要工具..."
apt update -y || log_error "系统更新或升级失败"
apt install -y curl apt-transport-https ipvsadm gnupg2 software-properties-common || log_error "安装必要工具失败"

# 安装docker
log_info "正在跳过安装docker..."
# 删除原有的Docker软件源
# if [ -f /etc/apt/sources.list.d/docker.list ]; then
#     rm /etc/apt/sources.list.d/docker.list    
# fi

# 添加阿里云的Docker镜像源
# 备份现有文件
# if [ -f /usr/share/keyrings/docker-archive-keyring.gpg ]; then
#     mv /usr/share/keyrings/docker-archive-keyring.gpg /usr/share/keyrings/docker-archive-keyring.gpg.bak
# fi
# 覆盖现有文件
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --batch --yes --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null


# 更新apt源
apt update -y || log_error "更新apt源失败"
# apt install docker-ce=5:20.10.24~3-0~ubuntu-focal docker-ce-cli=5:20.10.24~3-0~ubuntu-focal containerd.io --allow-downgrades -y || log_error "安装docker失败"
apt install containerd --allow-downgrades -y || log_error "安装containerd失败"
systemctl enable containerd || log_error "启动containerd服务失败"

# 配置containerd-crictl
if [ ! -f /etc/crictl.yaml ]; then
  sudo tee /etc/crictl.yaml > /dev/null <<EOF
runtime-endpoint: unix:///var/run/containerd/containerd.sock
image-endpoint: unix:///var/run/containerd/containerd.sock
timeout: 10
debug: false
pull-image-on-create: false
EOF
fi

# 安装kubeadm、kubelet、kubectl等
log_info "安装kubeadm、kubelet、kubectl等..."
# wget https://pkgs.k8s.io/core:/stable:/v1.21/deb/Release.key -O apt-key.gpg || log_error "下载kubeadm等的密钥失败"
# apt-key add apt-key.gpg && rm -f apt-key.gpg  || log_error "导入&删除apt-key.gpg文件失败"
curl -s https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | apt-key add - || log_error "添加k8s镜像源的密钥失败"
# curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
# echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list
echo "deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list
apt-get update -y || log_error "更新apt源以安装kubeadm等失败"

apt install -y kubelet=1.28.2-00 kubeadm=1.28.2-00 kubectl=1.28.2-00 --allow-downgrades --allow-change-held-packages || log_error "安装kubeadm,kubelet,kubectl失败"
apt-mark hold kubeadm kubelet kubectl  # 防止自动升级导致的问题

systemctl enable kubelet && systemctl start kubelet || log_error "启动kubelet服务失败"

# 备份docker的daemon.json文件
# if [ -f /etc/docker/daemon.json ]; then
#     cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
# fi

# 配置docker的daemon.json
# cat <<EOF > /etc/docker/daemon.json
# {"registry-mirrors":["https://registry.docker-cn.com","https://registry.cn-hangzhou.aliyuncs.com"],"exec-opts": ["native.cgroupdriver=systemd"]}
# EOF

# 重新加载docker配置并重启docker服务
systemctl daemon-reload
# systemctl restart docker

# 初始化节点
sudo modprobe br_netfilter
sudo sysctl net.bridge.bridge-nf-call-iptables=1

# 加载必要内核模块
sudo modprobe overlay
sudo modprobe br_netfilter

# 编辑 `/etc/modules-load.d/k8s.conf` 添加以下内容：
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

# 编辑 `/etc/sysctl.d/k8s.conf` 配置网络参数：
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

# 生效配置
sudo sysctl --system

# 将containerd默认配置写入文件
mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml

# 创建目录
sudo mkdir -p /etc/containerd/certs.d
mkdir -p /etc/containerd/certs.d/docker.io
mkdir -p /etc/containerd/certs.d/registry.k8s.io
mkdir -p /etc/containerd/certs.d/gcr.io

## 定义阿里云镜像源地址
ALIYUN_DOCKER="https://registry.docker-cn.com"
ALIYUN_K8S="https://registry.aliyuncs.com/google_containers"
ALIYUN_GCR="$ALIYUN_K8S"  # gcr.io 同样使用阿里云镜像源

# 配置文件路径
CONFIG_TOML="/etc/containerd/config.toml"
CERTS_DIR="/etc/containerd/certs.d"

# 1. 修改 containerd 配置文件
echo "正在配置 containerd 的镜像加速..."
if ! grep -q 'config_path' "$CONFIG_TOML"; then
  # 在 config.toml 中添加 config_path 配置
  sudo sed -i '$a\  [plugins."io.containerd.grpc.v1.cri".registry]\n    config_path = "'"$CERTS_DIR"'"' "$CONFIG_TOML"
fi

# 2. 创建 certs.d 目录（如果不存在）
sudo mkdir -p "$CERTS_DIR"

# 3. 配置 Docker Hub 镜像加速
echo "配置 Docker Hub 镜像加速..."
sudo mkdir -p "$CERTS_DIR/docker.io"
cat <<EOF | sudo tee "$CERTS_DIR/docker.io/hosts.toml"
server = "https://docker.io"
[host."$ALIYUN_DOCKER"]
  capabilities = ["pull", "resolve"]
EOF

# 4. 配置 Kubernetes 官方镜像源
echo "配置 Kubernetes 官方镜像加速..."
sudo mkdir -p "$CERTS_DIR/registry.k8s.io"
cat <<EOF | sudo tee "$CERTS_DIR/registry.k8s.io/hosts.toml"
server = "https://registry.k8s.io"
[host."$ALIYUN_K8S"]
  capabilities = ["pull", "resolve"]
EOF

# 5. 配置 Google Container Registry (gcr.io)
echo "配置 Google Container Registry 镜像加速..."
sudo mkdir -p "$CERTS_DIR/gcr.io"
cat <<EOF | sudo tee "$CERTS_DIR/gcr.io/hosts.toml"
server = "https://gcr.io"
[host."$ALIYUN_GCR"]
  capabilities = ["pull", "resolve"]
EOF

# 5. 修复 pause 镜像地址（使用阿里云镜像）
sudo sed -i 's|sandbox_image = "registry.k8s.io/pause:.*"|sandbox_image = "registry.aliyuncs.com/google_containers/pause:3.9"|g' /etc/containerd/config.toml

# --- 修正配置项 ---


# 1. 检查并设置 [plugins."io.containerd.grpc.v1.cri".containerd].systemd_cgroup = true
# echo "Checking/fixing 'systemd_cgroup' configuration..."
# if ! grep -q 'systemd_cgroup = true' "$CONFIG_TOML"; then
#     # 使用 sed 直接替换整行,无需捕获组
#     sed -i "/^\s*systemd_cgroup\s*=\s*.*/c\
# systemd_cgroup = true" "$CONFIG_TOML"
#     echo "Modified 'systemd_cgroup' to 'true'."
# else
#     echo "'systemd_cgroup' is already set to 'true'."
# fi 

# 2. 检查并设置 [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options].SystemdCgroup = true
# 检查配置文件是否存在
if [ ! -f "$CONFIG_TOML" ]; then
    echo "Error: Config file not found at $CONFIG_TOML"
    exit 1
fi

echo "Checking/fixing 'SystemdCgroup' configuration..."
# 使用 sed 修改 SystemdCgroup 的值为 true,保留缩进
if ! grep -q '^\s*SystemdCgroup\s*=\s*true' "$CONFIG_TOML"; then
    # 替换等号右侧的值,保留左侧的缩进和键名
    sed -i 's/^\(\s*SystemdCgroup\s*=\s*\).*/\1true/' "$CONFIG_TOML"
    echo "Modified 'SystemdCgroup' to 'true'. 修改后的值为："
    grep '^\s*SystemdCgroup\s*=\s*true' "$CONFIG_TOML"
else
    echo "'SystemdCgroup' is already set to 'true'."
fi

# 3. 重启 containerd 服务
echo "Restarting containerd..."
sudo systemctl restart containerd
if [ $? -eq 0 ]; then
    echo "containerd restarted successfully."
else
    echo "Failed to restart containerd. Check logs for errors."
fi

# 验证配置
echo "Verifying configuration..."
crictl info | grep -i "systemd_cgroup" && crictl info | grep -i "SystemdCgroup"
echo "containerd配置初始纠正完成."

echo "开始更新containerd配置以适配GPU实例"

# 检查 NVIDIA GPU
if lspci | grep -i nvidia > /dev/null 2>&1; then
    if [ "$1" == "worker" ]; then
        log_info "检测到NVIDIA GPU,开始配置nvidia-container-runtime..."

        # 检查 .deb 文件是否存在
        DEB_FILES=(/opt/*_amd64.deb)
        if [ ! -e "${DEB_FILES[0]}" ]; then
            log_error "/opt/ 下没有 .deb 文件"
            exit 1
        fi

        # 安装 .deb 包
        for deb in "${DEB_FILES[@]}"; do
            dpkg -i "$deb" || {
                log_error "安装 $deb 失败"
                exit 1
            }
        done

        # 配置 containerd
        CONTAINERD_CONFIG="/etc/containerd/config.toml"
        log_info "正在更新 $CONTAINERD_CONFIG 配置..."

        # 1. 添加 nvidia 运行时配置到 runtimes 块内部
        # 添加 nvidia runtime 配置到 runtimes 块下
        NVIDIA_SECTION='plugins\."io\.containerd\.grpc\.v1\.cri"\.containerd\.runtimes\.nvidia'
#         if ! grep -qF "[${NVIDIA_SECTION}]" "$CONTAINERD_CONFIG"; then
#             sudo sed -i '/^
# $$
# plugins\."io\.containerd\.grpc\.v1\.cri"\.containerd\.runtimes
# $$
# $/a \
#     [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia]\n\
#         privileged_without_host_devices = false\n\
#         runtime_type = "io.containerd.runc.v2"\n\
#         [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia.options]\n\
#             BinaryName = "/usr/bin/nvidia-container-runtime"' /etc/containerd/config.toml
#         fi

#         # 2. 修改默认运行时为 nvidia
#         if ! grep -qF 'default_runtime_name = "nvidia"' "$CONTAINERD_CONFIG"; then
#             sudo sed -i 's/default_runtime_name = "runc"/default_runtime_name = "nvidia"/' "$CONTAINERD_CONFIG"
#         fi
        cp -v /opt/config.toml /etc/containerd/config.toml || log_error "直接复制containerd配置文件失败"

        # 3. 重启 containerd 并检查状态
        log_info "重启 containerd 服务..."
        if systemctl restart containerd; then
            log_info "containerd 重启成功"
        else
            log_error "containerd 重启失败,请检查配置文件"
            exit 1
        fi

        # 4. 配置 CUDA 环境变量
        log_info "配置 CUDA 环境变量..."
        grep -qxF 'export PATH=/usr/local/cuda/bin:$PATH' ~/.bashrc || echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
        grep -qxF 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' ~/.bashrc || echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc

        # 应用环境变量（非交互式shell提示手动执行）
        if [[ "$-" == *i* ]]; then
            source ~/.bashrc
            log_info "环境变量已生效"
        else
            log_info "请手动执行 'source ~/.bashrc' 使环境变量生效"
        fi

        # 5. 验证 CUDA 安装
        # nvcc -V

        log_info "nvidia-container-runtime 配置完成,containerd已重启"
    fi
else
    log_info "未检测到NVIDIA GPU,跳过nvidia-container-runtime配置"
fi

# 修改 DNS 为阿里云公共 DNS（提升镜像拉取速度）
#     sudo tee /etc/resolv.conf <<EOF
# nameserver 223.5.5.5
# nameserver 223.6.6.6
# nameserver 8.8.8.8
# nameserver 114.114.114.114
# EOF

# 5. 验证配置是否生效
# sudo crictl --runtime-endpoint unix:///run/containerd/containerd.sock info
crictl info

# 开启ip转发
# 处理[ERROR FileContent--proc-sys-net-ipv4-ip_forward]: /proc/sys/net/ipv4/ip_forward contents are not set to 1问题
if ! grep -q "^net.ipv4.ip_forward = 1" /etc/sysctl.conf; then
  echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf > /dev/null
  sudo sysctl -p
fi

# nfs_server_ip="192.168.0.3"  # 替换为实际的NFS服务器IP
# nfs_share_path="/d/k8s_nss"
echo "======== 动态获取NFS服务器IP和共享目录 ========"
nfs_server_ip="$2"  # 替换为实际的NFS服务器IP
nfs_share_path="$3"  # 替换为实际的NFS服务器共享目录

# 不改变原有逻辑的基础上,将 K8s相关数据目录迁移到 $nfs_share_path 目录
log_info "迁移K8s相关数据目录到$nfs_share_path挂载点..."

# 迁移containerd数据目录
if [ ! -d $nfs_share_path/containerd ]; then
    mkdir -p $nfs_share_path/containerd
fi
if [ -d /var/lib/containerd ] && [ ! -L /var/lib/containerd ]; then
    systemctl stop containerd
    mv /var/lib/containerd/* $nfs_share_path/containerd/ 2>/dev/null || true
    rm -rf /var/lib/containerd
    ln -sf $nfs_share_path/containerd /var/lib/
    systemctl start containerd
fi

# 迁移kubelet数据目录
if [ ! -d $nfs_share_path/kubelet ]; then
    mkdir -p $nfs_share_path/kubelet
fi
if [ ! -L /var/lib/kubelet ]; then
    systemctl stop kubelet
    mv /var/lib/kubelet/* $nfs_share_path/kubelet/ 2>/dev/null || true
    rm -rf /var/lib/kubelet
    ln -sf $nfs_share_path/kubelet /var/lib/
    systemctl start kubelet
fi

# 迁移kubeadm数据目录
if [ ! -d $nfs_share_path/kubeadm ]; then
    mkdir -p $nfs_share_path/kubeadm
fi
if [ ! -L /var/lib/kubeadm ]; then
    mv /var/lib/kubeadm/* $nfs_share_path/kubeadm/ 2>/dev/null || true
    rm -rf /var/lib/kubeadm
    ln -sf $nfs_share_path/kubeadm /var/lib/
fi

# 迁移etcd数据目录（仅master节点）
if [ "$1" == "master" ]; then
    if [ ! -d $nfs_share_path/etcd ]; then
        mkdir -p $nfs_share_path/etcd
    fi
    if [ ! -L /var/lib/etcd ]; then
        systemctl stop kubelet 2>/dev/null || true
        mv /var/lib/etcd/* $nfs_share_path/etcd/ 2>/dev/null || true
        rm -rf /var/lib/etcd
        ln -sf $nfs_share_path/etcd /var/lib/
        systemctl start kubelet 2>/dev/null || true
    fi
fi

# 权限修正
chown -R root:root $nfs_share_path/containerd $nfs_share_path/kubelet $nfs_share_path/kubeadm $nfs_share_path/etcd 2>/dev/null || true

log_info "K8s数据目录迁移完成,所有数据将存储于$nfs_share_path下。"

# 防火墙开放端口
log_info "开放防火墙端口..."
# 安装并配置 ufw（仅开放必要端口）
# 开放 Kubernetes 控制平面端口
sudo ufw allow 6443/tcp
sudo ufw allow 10257/tcp
sudo ufw allow 2379:2380/tcp

# 开放 kubelet 和组件通信端口（仅限集群内部）
# 注意：10250 端口需严格限制访问,避免暴露到公网
sudo ufw allow 10250:10252/tcp

# 开放 NodePort 服务端口范围
sudo ufw allow 30000:32767/tcp

# 开放 CNI 插件端口（如 Calico）
sudo ufw allow 4789/udp
sudo ufw allow 179/tcp

# 开放 Ingress 端口（如 Nginx Ingress）
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# sudo ufw enable

# 判断是主节点还是副节点
if [ "$1" == "master" ]; then
    #  写入hosts
    # if ! grep -q "k8s-master" /etc/hosts; then
    #     echo "127.0.0.1 k8s-master" | sudo tee -a /etc/hosts > /dev/null
    # fi
    # 修改主机名,这里假设新主机名为 k8s-node,可根据实际情况修改
    hostnamectl set-hostname k8s-master || log_error "修改主机名失败"

    # 主节点安装步骤
    log_info "正在master节点进行安装core和初始化"
    # kubeadm config images list

    # 导入本地镜像减少拉取时间
    chmod 755 /opt/import_images.sh && /opt/import_images.sh
    
    sleep 1
    log_info "初始化主节点..."
    # kubeadm init --image-repository=registry.aliyuncs.com/google_containers --pod-network-cidr=10.244.0.0/16 --service-cidr=10.96.0.0/12 || log_error "主节点初始化失败"
    # kubeadm init --config=kubeadm.yaml --pod-network-cidr=10.244.0.0/16 --service-cidr=10.96.0.0/12
    kubeadm init --image-repository=registry.aliyuncs.com/google_containers --pod-network-cidr=10.244.0.0/16 --service-cidr=10.96.0.0/12 --kubernetes-version=v1.28.2 || log_error "主节点初始化失败"
    # sudo chmod 644 /etc/kubernetes/pki/*
    # sudo chown -R root:root /etc/kubernetes/pki

    # 在主节点上执行以下命令来生成副节点加入的 join 指令
    log_info "生成工作节点加入的join指令..."
    join_command=$(kubeadm token create --print-join-command 2>/dev/null)
    # join_command=$(kubeadm token create --print-join-command --ttl 0 2>/dev/null)
    if [ -z "$join_command" ]; then
        log_error "生成join指令失败"
    else
        echo "$join_command" > join_command.txt
        echo "已将join命令保存到join_command.txt文件中,请在新窗口cat查看并拷贝到worker node进行集群注册"
        # 这里可以继续执行后面的步骤
        # 配置kubectl
        log_info "配置kubectl..."
        mkdir -p $HOME/.kube
        cp -i /etc/kubernetes/admin.conf $HOME/.kube/config || log_error "复制kubeconfig文件失败"
        chown $(id -u):$(id -g) $HOME/.kube/config || log_error "更改kubeconfig文件权限失败"

        echo "master节点安装完毕..."
        sleep 1
        # 安装网络插件
        log_info "正在安装网络插件(flannel)"
        kubectl apply -f /opt/kube-flannel.yml || log_error "本地安装flannel网络插件失败"
        # log_info "正在安装Ingress-nginx-controller插件"
        # kubectl apply -f /opt/ingress-nginx-controller.yaml || log_error "本地安装ingress-nginx-controller插件失败"
        log_info "正在安装nfs-client-provisioner插件"
        aptitude -y install nfs-kernel-server nfs-common=1:1.3.4-2.5ubuntu3.7
        # log_info "正在安装MetricsServer插件"
        # kubectl apply -f /opt/components.yaml || log_error "本地安装MetricsServer插件失败"
        # log_info "正在安装GPU模式必要插件"
        # kubectl apply -f /opt/nvidia-device-plugin.yml || log_error "本地安装GPU模式必要插件失败"
        if [ $? -ne 0 ]; then
            echo "NFS 服务器端安装失败,请检查网络连接或软件源。"
            exit 1
        fi
        
        # 创建集群共享目录
        # 检查 NFS 共享目录是否存在,若不存在则创建
        # 目前是控制节点承担所有共享存储,后期需要换成动态的NFS服务器
        mkdir -p $nfs_share_path

        # 定义要添加到 /etc/exports 的配置行
        line="$nfs_share_path *(rw,sync,no_root_squash,no_subtree_check)"

        # 检查 /etc/exports 文件是否已经包含指定行
        if ! grep -qF "$line" /etc/exports; then
            # 若不包含,则添加该行
            echo "$line" >> /etc/exports
            if [ $? -ne 0 ]; then
                echo "共享目录配置文件修改失败,请检查文件权限。"
                exit 1
            else
                echo "成功添加共享目录配置。"
            fi
        else
            echo "共享目录配置已存在,无需重复添加。"
        fi

        # 启动 NFS 服务
        echo "启动 NFS 服务..."
        systemctl restart nfs-kernel-server
        if [ $? -ne 0 ]; then
            echo "NFS 服务启动失败,请检查配置文件。"
            exit 1
        fi
        kubectl apply -f /opt/storage_class.yaml || log_error "集群存储类nfs-storage-class初始化失败"
        #kubectl apply -f /opt/nfs-provisioner-deploy.yaml || log_error "动态存储nfs-provisioner-deploy初始化失败"
        echo "!!! 此处更换成读取动态的NFS服务器: xxx.xx.xx.xxx 及共享目录: /a/b/c !!!"
        nfs_provisioner_yaml='
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nfs-client-provisioner
  labels:
    app: nfs-client-provisioner
spec:
  replicas: 1
  strategy:
    type: Recreate                   ## 设置升级策略为删除再创建(默认为滚动更新)
  selector:
    matchLabels:
      app: nfs-client-provisioner
  template:
    metadata:
      labels:
        app: nfs-client-provisioner
    spec:
      serviceAccountName: nfs-client-provisioner
      containers:
        - name: nfs-client-provisioner
          #image: gcr.io/k8s-staging-sig-storage/nfs-subdir-external-provisioner:v4.0.0
          image: registry.cn-beijing.aliyuncs.com/xngczl/nfs-subdir-external-provisione:v4.0.0
          volumeMounts:
            - name: nfs-client-root
              mountPath: /persistentvolumes
          env:
            - name: PROVISIONER_NAME     ## Provisioner的名称,以后设置的storageclass要和这个保持一致
              value: k8s-sigs.io/nfs-subdir-external-provisioner
            - name: NFS_SERVER           ## NFS服务器地址,需和valumes参数中配置的保持一致
              value: '"$nfs_server_ip"'  ## 替换为实际的NFS服务器IP
            - name: NFS_PATH             ## NFS服务器数据存储目录,需和valumes参数中配置的保持一致
              value: '"$nfs_share_path"'  ## 替换为实际的NFS服务器共享目录
      volumes:
        - name: nfs-client-root
          nfs:
            server: '"$nfs_server_ip"'     ## NFS服务器地址
            path: '"$nfs_share_path"'            ## NFS服务器数据存储目录
            readOnly: false
'
        echo "$nfs_provisioner_yaml" | kubectl apply -f -
        if [ $? -ne 0 ]; then
            echo "nfs动态工具链创建失败"
            exit 1
        fi
        kubectl apply -f /opt/nfs-rbac.yaml || log_error "集群共享存储权限nfs-rbac初始化失败"
        # 修改 deployment.yaml 文件,设置 NFS 服务器地址和共享目录
        # sed -i 's|NFS_SERVER|your_nfs_server_ip|g' deployment.yaml
        # sed -i 's|NFS_PATH|your_nfs_shared_directory|g' deployment.yaml

        # # 创建资源
        # kubectl apply -f rbac.yaml
        # kubectl apply -f deployment.yaml
        # kubectl apply -f class.yaml

        sleep 3

        # 查询组件状态
        log_info "查询组件状态..."
        # 检查是否有组件状态为 Unhealthy
        if kubectl get componentstatuses 2>/dev/null | grep -q 'Unhealthy'; then
            echo "检测到组件状态为 Unhealthy, 开始修复..."
            
            # 注释掉 --port=0 参数（添加备份文件）
            sed -i.bak '/--port=0/s/^/#/' /etc/kubernetes/manifests/kube-controller-manager.yaml
            sed -i.bak '/--port=0/s/^/#/' /etc/kubernetes/manifests/kube-scheduler.yaml
            
            echo "已生成备份文件: kube-controller-manager.yaml.bak 和 kube-scheduler.yaml.bak"
            echo "修复完成,等待组件重启..."
            
        else
            echo "所有组件状态正常,无需修复。"
        fi
        sleep 5
        systemctl restart kubelet.service || log_error "重启kubelet服务失败"
        log_info "30秒后再次查看组件状态..."
        sleep 30
        # 再次查看组件状态（需要稍等）
        kubectl get cs || log_info "再次获取组件状态失败"

        echo "验证集群状态(安装完毕后手动执行),查看pod状态"
        log_info "查看pod状态..."
        kubectl get nodes || log_info "获取节点状态失败"
        kubectl get pods --all-namespaces || log_info "获取所有命名空间的pod状态失败"
    fi
    
elif [ "$1" == "worker" ]; then
    # 修改主机名
    apt install telnet -y
    aptitude -y install nfs-common=1:1.3.4-2.5ubuntu3.7
    #  写入hosts
    # if ! grep -q "k8s-worker" /etc/hosts; then
    #     echo "127.0.0.1 k8s-worker" | sudo tee -a /etc/hosts > /dev/null
    # fi
    # 这里假设新主机名为 k8s-node,可根据实际情况修改
    hostnamectl set-hostname "k8s-worker-$(date +%Y%m%d%H%M%S)" || log_error "修改主机名失败"
    # 副节点安装步骤
    log_info "正在worker节点进行安装"
    apt update -y || log_error "更新apt源失败"
    # 从节点重启kubeadm,可解决曾启动过导致端口被占用的问题
    log_info "从节点重启kubeadm,可解决曾启动过导致端口被占用的问题..."
    kubeadm reset -f|| log_error "重置kubeadm失败"
    # 获取主节点的join命令（假设已提前获取并保存为join_command.txt）
    
    # 导入本地网络插件部分镜像减少拉取时间
    chmod 755 /opt/import_images.sh && /opt/import_images.sh

    echo "请输入加入对方kubernetes集群的命令: (任何时候)"
    # read join_command
    # eval "$join_command" || log_error "加入k8s集群失败"
else
    echo "请指定正确的节点类型,master或worker"
    exit 1
fi

# 检查安装过程是否有错误（这里只是简单示例,实际可能需要更详细的检查）
if [ $? -ne 0 ]; then
    log_error "安装过程中出现错误,请手动解决后再重新执行"
fi

log_info "安装脚本执行完毕"
# 输出安装完成提示
log_info "Kubernetes 安装脚本执行完毕,请根据提示进行后续操作。"
log_info "如果是主节点,请在新窗口cat join_command.txt查看并拷贝到worker node进行集群注册"
log_info "如果是worker节点,请在新窗口输入主节点提供的join命令进行集群注册"
log_info "请注意,在执行完脚本后,可能需要等待一段时间以确保所有组件正常运行。"
log_info "可以使用 'kubectl get nodes' 和 'kubectl get pods --all-namespaces' 命令来检查集群状态。"
log_info "如果有任何问题,请检查日志或联系管理员Ahexl。"
log_info "感谢使用本脚本,祝您使用愉快！"