#!/bin/bash

set -eo pipefail # 脚本遇到任何错误立即退出，未捕捉的管道错误也退出

get_script_path(){
	# 获取脚本真实路径（解析软链接）
	SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
	echo "$SCRIPT_DIR"
}
# ==============================================================================
# 配置区域
# ==============================================================================
MYPATH=$(get_script_path)
OFFLINE_ASSETS_DIR="${MYPATH}/k8s-offline-bundle"

K8S_VERSION="v1.28.2"
CALICO_VERSION="v3.26.1"
KUBEVIRT_VERSION="v1.1.0"
MULTUS_VERSION="v4.0.2" # Multus CNI 镜像版本
NFS_PROVISIONER_VERSION="v4.0.2" # NFS Provisioner 镜像标签
NFS_CHART_VERSION="4.0.18" # Helm Chart 版本

K8S_MASTER_IP="192.168.16.5" # 控制节点的IP，用于API Server绑定和广告
LOCAL_REGISTRY_PORT="5000"
LOCAL_REGISTRY_ADDR="${K8S_MASTER_IP}:${LOCAL_REGISTRY_PORT}" # 本地镜像仓库地址

K8S_APISERVER_ADVERTISE_ADDRESS="${K8S_MASTER_IP}" # kubeadm init 使用的API Server广告地址
POD_CIDR="10.244.0.0/16"
SERVICE_CIDR="10.96.0.0/12"

NFS_SERVER="192.168.16.2"
NFS_PATH="/d/share/101206"
NFS_STORAGE_CLASS_NAME="nfs-client"

TEMP_DIR="/tmp/k8s-master-setup" # 临时工作目录
NAMESPACE="default" # 默认命名空间，用于 ctr 命令
CONTAINERD_CONFIG="/etc/containerd/config.toml"
CERTS_D_PATH="/etc/containerd/certs.d"
# /etc/containerd/config.toml文件做以下修改
# SystemdCgroup = false 在 [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options] 下。这个也需要改为 true。
# ==============================================================================
# 启动前日志输出
# ==============================================================================
echo "=================================================="
echo " Kubernetes 控制节点离线安装脚本 "
echo "=================================================="
echo "配置参数:"
echo "  K8s 版本: ${K8S_VERSION}"
echo "  本地镜像仓库: ${LOCAL_REGISTRY_ADDR}"
echo "  K8s API Server IP: ${K8S_APISERVER_ADVERTISE_ADDRESS}"
echo "  Pod CIDR: ${POD_CIDR}"
echo "  Service CIDR: ${SERVICE_CIDR}"
echo "  NFS Server: ${NFS_SERVER}:${NFS_PATH}"
echo "--------------------------------------------------"

# ==============================================================================
# 通用函数
# ==============================================================================

log_info() {
    echo -e "\e[32m[INFO] $(date +'%Y-%m-%d %H:%M:%S') $1\e[0m"
}

log_warn() {
    echo -e "\e[33m[WARN] $(date +'%Y-%m-%d %H:%M:%S') $1\e[0m" >&2
}

log_error() {
    echo -e "\e[31m[ERROR] $(date +'%Y-%m-%d %H:%M:%S') $1\e[0m" >&2
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
		log_error "此脚本必须以 root 用户或使用 sudo 运行。"
    fi
}

configure_sysctl() {
    log_info "配置系统内核参数..."
    cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf > /dev/null
overlay
br_netfilter
EOF
    sudo modprobe overlay
    sudo modprobe br_netfilter

    cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf > /dev/null
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
    sudo sysctl --system > /dev/null
    log_info "系统内核参数配置完成。"
}

disable_swap() {
    log_info "禁用 Swap 分区..."
    if grep -q "swap" /etc/fstab; then
        sudo swapoff -a
        sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
        log_info "Swap 分区已禁用并从 fstab 中注释。"
    else
        log_info "未检测到 Swap 分区或已禁用。"
    fi
}

# ==============================================================================
# 0. 前置检查与环境初始化
# ==============================================================================
check_root
configure_sysctl
disable_swap

log_info "创建临时工作目录: ${TEMP_DIR}"
sudo mkdir -p "${TEMP_DIR}"
sudo rm -rf "${TEMP_DIR}/*" # 清理旧的临时文件

log_info "将离线资源目录添加到 PATH。"
export PATH="${OFFLINE_ASSETS_DIR}/bin:$PATH"
echo "export PATH=${OFFLINE_ASSETS_DIR}/bin:\$PATH" | sudo tee /etc/profile.d/offline-k8s.sh > /dev/null
# ==============================================================================
# 1. 安装操作系统依赖 (DEB 包)
# ==============================================================================
log_info "开始安装操作系统依赖 (DEB 包)..."
DEBS_DIR="${OFFLINE_ASSETS_DIR}/debs"
if [ ! -d "$DEBS_DIR" ]; then
    log_error "DEB 包目录 ${DEBS_DIR} 不存在。请确保将所有 .deb 文件放在此目录中。"
fi

cd "${DEBS_DIR}" || log_error "无法进入 DEB 包目录 ${DEBS_DIR}。"

log_info "尝试安装所有 DEB 包。这可能需要一些时间，并会尝试多次以解决依赖顺序问题。"
# 尝试多次安装，以解决部分依赖顺序问题
# for i in {1..3}; do
#     log_info "第 ${i} 次尝试安装 DEB 包..."
#     sudo dpkg -i *.deb &>/dev/null || true
# done

# 最终检查是否有未满足的依赖，尝试修复
log_info "检查并尝试解决任何未满足的 DEB 包依赖..."
if ! sudo apt-get install -f --assume-yes &>/dev/null; then
    log_warn "部分 DEB 包依赖可能未完全满足。请手动检查并解决 (例如运行 'sudo apt-get install -f')。"
else
    log_info "所有 DEB 包及其依赖已成功安装或已解决。"
fi

cd - > /dev/null # 返回之前的工作目录
log_info "操作系统依赖 (DEB 包) 安装完成。"

# ==============================================================================
# 2. 安装 Docker (仅用于本地镜像仓库)
# ==============================================================================
log_info "安装 Docker daemon (仅用于本地镜像仓库) ..."
if ! command_exists docker; then
    log_error "未检测到 Docker CLI。请确保已安装 Docker (或其他兼容的容器引擎如Podman)。"
fi

log_info "配置 Docker daemon 信任本地仓库 ${LOCAL_REGISTRY_ADDR} (针对非 HTTPS)..."
sudo mkdir -p /etc/docker
cat <<EOF | sudo tee /etc/docker/daemon.json > /dev/null
{
  "insecure-registries": ["${LOCAL_REGISTRY_ADDR}"],
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  }
}
EOF
sudo groupadd docker &>/dev/null || true # 如果组已存在，忽略错误
sudo systemctl daemon-reload
sudo systemctl enable docker.socket
sudo systemctl enable docker
sudo systemctl restart docker.socket
sudo systemctl restart docker
sudo systemctl status docker --no-pager || log_error "Docker daemon 启动失败。"
log_info "Docker daemon 已配置信任本地仓库并重启。"

# ==============================================================================
# 3. 安装 Containerd 运行时
# ==============================================================================
log_info "安装 Containerd 运行时..."
CONTAINERD_TAR_GZ=$(find "${OFFLINE_ASSETS_DIR}/bin" -name "containerd-*.tar.gz" | head -n 1)
if [ -z "$CONTAINERD_TAR_GZ" ]; then
    log_error "未找到 Containerd 压缩包。"
fi

sudo tar Cxzvf /usr/local "$CONTAINERD_TAR_GZ" || log_error "解压 Containerd 失败。"

# 确保 containerd systemd 服务文件存在
CONTAINERD_SERVICE_FILE="${OFFLINE_ASSETS_DIR}/service/containerd.service"
if [ ! -f "$CONTAINERD_SERVICE_FILE" ]; then
    log_error "未找到 containerd.service 文件: ${CONTAINERD_SERVICE_FILE}"
fi
sudo cp "$CONTAINERD_SERVICE_FILE" /etc/systemd/system/containerd.service
sudo systemctl daemon-reload # 重新加载服务配置

log_info "生成并配置 Containerd 默认配置文件..."
sudo mkdir -p /etc/containerd
sudo containerd config default | sudo tee /etc/containerd/config.toml > /dev/null

# --- 配置 containerd registry mirrors using config_path ---
log_info "配置 containerd 镜像仓库代理..."

# 创建必要的目录
for reg in "${LOCAL_REGISTRY_ADDR}" registry.k8s.io ghcr.io quay.io docker.io nvcr.io; do
    sudo mkdir -p "${CERTS_D_PATH}/${reg}"
done

# 为本地 Registry 配置 hosts.toml (http, skip_verify)
sudo tee "${CERTS_D_PATH}/${LOCAL_REGISTRY_ADDR}/hosts.toml" > /dev/null <<EOF
server = "http://${LOCAL_REGISTRY_ADDR}"
[host."http://${LOCAL_REGISTRY_ADDR}"]
  capabilities = ["pull", "resolve"]
  skip_verify = true
EOF

# 为所有上游仓库配置镜像到本地，回退到官方
REGISTRY_SOURCES=(
    "registry.k8s.io"
    "ghcr.io"
    "quay.io"
    "docker.io"
    "nvcr.io"
)

for source in "${REGISTRY_SOURCES[@]}"; do
    sudo tee "${CERTS_D_PATH}/${source}/hosts.toml" > /dev/null <<EOF
server = "https://${source}"
[host."http://${LOCAL_REGISTRY_ADDR}"]
  capabilities = ["pull", "resolve"]
  skip_verify = true
[host."https://${source}"]
  capabilities = ["pull", "resolve"]
EOF
done

# 修改 /etc/containerd/config.toml
log_info "修改 ${CONTAINERD_CONFIG} 配置..."
# 设置 sandbox_image
sudo sed -i "s|sandbox_image = \"registry.k8s.io/pause:3.6\"|sandbox_image = \"${LOCAL_REGISTRY_ADDR}/pause:3.9\"|g" "$CONTAINERD_CONFIG"
sudo sed -i "s|SystemdCgroup = false|SystemdCgroup = true|g" "$CONTAINERD_CONFIG" || true
# 设置 config_path
if grep -q "config_path =" "$CONTAINERD_CONFIG"; then
    sudo sed -i "s|^[[:space:]]*config_path = .*|      config_path = \"${CERTS_D_PATH}\"|" "$CONTAINERD_CONFIG"
else
    # 在 [plugins."io.containerd.grpc.v1.cri".registry] 块中添加 config_path
    if ! grep -q "\[plugins.\"io.containerd.grpc.v1.cri\".registry\]" "$CONTAINERD_CONFIG"; then
        log_warn "未找到 [plugins.\"io.containerd.grpc.v1.cri\".registry] 块，将尝试追加。"
        echo -e "\n[plugins.\"io.containerd.grpc.v1.cri\".registry]\n      config_path = \"${CERTS_D_PATH}\"" | sudo tee -a "$CONTAINERD_CONFIG" > /dev/null
    else
        sudo sed -i "/\[plugins.\"io.containerd.grpc.v1.cri\".registry\]/a \\\n      config_path = \"${CERTS_D_PATH}\"" "$CONTAINERD_CONFIG"
    fi
fi

# 移除旧的 mirrors 和 configs (弃用警告相关的部分)
# 使用多行 sed 表达式删除整个块
sudo sed -i '/^\[plugins\."io\.containerd\.grpc\.v1\.cri"\.registry\.mirrors\."registry\.k8s\.io"\]/,/^endpoint = \[/d' "$CONTAINERD_CONFIG" || true
sudo sed -i '/^\[plugins\."io\.containerd\.grpc\.v1\.cri"\.registry\.configs\."192\.168\.16\.5:5000"\.tls\]/,/^insecure_skip_verify = /d' "$CONTAINERD_CONFIG" || true
# 确保删除所有相关的空行或残留的块头
sudo sed -i '/^\[plugins\."io\.containerd\.grpc\.v1\.cri"\.registry\.mirrors\]/d' "$CONTAINERD_CONFIG" || true
sudo sed -i '/^\[plugins\."io\.containerd\.grpc\.v1\.cri"\.registry\.configs\]/d' "$CONTAINERD_CONFIG" || true

log_info "重启 containerd 服务..."
sudo systemctl daemon-reload
sudo systemctl restart containerd || log_error "Containerd 服务启动失败。"
sudo systemctl status containerd --no-pager || log_error "Containerd 服务状态异常。"
log_info "Containerd 配置完成并已启动。"

# 配置 crictl
log_info "配置 crictl..."
cat <<EOF | sudo tee /etc/crictl.yaml > /dev/null
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
EOF
log_info "crictl 配置完成。"

# ==============================================================================
# 4. 安装 CNI 插件
# ==============================================================================
log_info "安装 CNI 插件..."
CNI_PLUGINS_TAR_GZ=$(find "${OFFLINE_ASSETS_DIR}/bin" -name "cni-plugins-*.tgz" | head -n 1)
if [ -z "$CNI_PLUGINS_TAR_GZ" ]; then
    log_error "未找到 CNI 插件压缩包。"
fi

sudo mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin "$CNI_PLUGINS_TAR_GZ" || log_error "解压 CNI 插件失败。"
log_info "CNI 插件安装完成。"

# ==============================================================================
# 5. 安装 Kubernetes Binaries (kubelet, kubeadm, kubectl)
# ==============================================================================
log_info "安装 Kubernetes Binaries..."
BIN_DIR="${OFFLINE_ASSETS_DIR}/bin"
for bin in kubelet kubeadm kubectl helm; do
    if [ ! -f "${BIN_DIR}/${bin}" ]; then
        log_error "Kubernetes 二进制文件 ${bin} 未找到在 ${BIN_DIR}。"
    fi
    sudo cp "${BIN_DIR}/${bin}" /usr/local/bin/
    sudo chmod +x "/usr/local/bin/${bin}"
done

# 配置 kubelet systemd 服务 (从模板生成)
log_info "配置 kubelet systemd 服务..."
cat <<'EOF' | sudo tee /etc/systemd/system/kubelet.service
[Unit]
Description=kubelet: The Kubernetes Node Agent
Documentation=https://kubernetes.io/docs/
After=containerd.service
Wants=containerd.service

[Service]
ExecStart=/usr/local/bin/kubelet
Restart=always
StartLimitInterval=0
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mkdir -p /etc/systemd/system/kubelet.service.d
cat <<'EOF' | sudo tee /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
[Service]
Environment="KUBELET_KUBECONFIG_ARGS=--bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfig=/etc/kubernetes/kubelet.conf"
Environment="KUBELET_CONFIG_ARGS=--config=/var/lib/kubelet/config.yaml"
EnvironmentFile=-/etc/default/kubelet
ExecStart=
ExecStart=/usr/local/bin/kubelet $KUBELET_KUBECONFIG_ARGS $KUBELET_CONFIG_ARGS $KUBELET_EXTRA_ARGS
EOF


sudo systemctl daemon-reload
sudo systemctl enable kubelet || log_error "启用 kubelet 服务失败。"
log_info "Kubernetes Binaries 安装完成，kubelet 服务已启用但未启动。"

# ==============================================================================
# 6. 启动本地镜像仓库 (仅在控制节点，192.168.16.5)
# ==============================================================================
log_info "启动本地镜像仓库 ${LOCAL_REGISTRY_ADDR} ..."

# 加载 registry 镜像
cd "${OFFLINE_ASSETS_DIR}/images"
REGISTRY_TAR=$(find . -name "registry_2.tar" | head -n 1)
if [ -z "$REGISTRY_TAR" ]; then
    log_error "未找到本地镜像仓库 registry:2 的 tar 包。"
fi
sudo docker load -i "$REGISTRY_TAR" || log_error "加载 registry:2 镜像失败。"

# 停止并删除旧的 registry 容器，确保干净启动
sudo docker stop registry &>/dev/null || true
sudo docker rm -v registry &>/dev/null || true

# 启动 registry 容器
sudo docker run -d -p "${LOCAL_REGISTRY_PORT}:5000" --restart=always --name registry registry:2 || log_error "启动本地镜像仓库容器失败。"
log_info "本地镜像仓库已在 ${LOCAL_REGISTRY_ADDR} 启动。"
cd - > /dev/null

# ==============================================================================
# 7. 导入并标记所有镜像到 containerd
# ==============================================================================
log_info "导入所有离线镜像到 containerd 仓库并标记..."

IMAGE_DIR="${OFFLINE_ASSETS_DIR}/images"
if [ ! -d "$IMAGE_DIR" ]; then
    log_error "镜像文件目录 ${IMAGE_DIR} 不存在。"
fi

# 清理 containerd 本地存储中的所有镜像 (除registry:2外，避免误删)
log_info "清理 containerd 中已存在的镜像..."
# 使用 ctr images ls --quiet 获取所有镜像的 digest
# 然后过滤掉那些可能是本地 registry 相关的镜像，避免干扰
ctr_images_to_delete=$(ctr -n "$NAMESPACE" images ls --quiet | while read -r digest; do
    # 检查该 digest 对应的 REF 是否包含 LOCAL_REGISTRY_ADDR 或 registry:2
    # 这里有点复杂，因为一个 digest 可能有多个 REF
    refs=$(ctr -n "$NAMESPACE" images ls --no-header | grep "$digest" | awk '{print $1}')
    skip_delete=false
    for ref in $refs; do
        if [[ "$ref" == *"/registry:2"* ]]; then
            log_info "    跳过删除 registry 镜像: $ref ($digest)"
            skip_delete=true
            break
        fi
    done
    if [ "$skip_delete" = false ]; then
        echo "$digest" # 输出需要删除的 digest
    fi
done)

if [ -n "$ctr_images_to_delete" ]; then
    echo "$ctr_images_to_delete" | while read -r digest_to_delete; do
        log_info "  删除 containerd 镜像 (digest): $digest_to_delete"
        ctr -n "$NAMESPACE" images rm "$digest_to_delete" &>/dev/null || log_warn "删除镜像 $digest_to_delete 失败 (可能被使用或不存在)。"
    done
fi
log_info "Containerd 镜像清理完成。"

for tarfile in "$IMAGE_DIR"/*.tar; do
    [ -e "$tarfile" ] || continue

    echo ""
    echo ">>> Processing $tarfile"

    # 1️⃣ 获取导入前的镜像列表
    IMAGES_BEFORE=$(mktemp)
    # ctr images ls 的第一列就是 REF (镜像名称)，使用 awk 提取
    if ! ctr -n "$NAMESPACE" images ls | awk 'NR>1 {print $1}' | sort > "$IMAGES_BEFORE"; then
        log_info "❌ Failed to get images list before import."
        continue
    fi

    # Debug:
    log_info "Images BEFORE import for $tarfile:"
    cat "$IMAGES_BEFORE"

    # 2️⃣ 导入镜像
    if ! ctr -n "$NAMESPACE" images import "$tarfile"; then
        log_info "❌ Failed to import image from $tarfile."
        rm -f "$IMAGES_BEFORE" # 清理临时文件
        continue
    fi

    # 3️⃣ 获取导入后的镜像列表
    IMAGES_AFTER=$(mktemp)
    if ! ctr -n "$NAMESPACE" images ls | awk 'NR>1 {print $1}' | sort > "$IMAGES_AFTER"; then
        echo "❌ Failed to get images list after import."
        rm -f "$IMAGES_BEFORE" # 清理临时文件
        continue
    fi

    # Debug:
    log_info "Images AFTER import for $tarfile:"
    # cat "$IMAGES_AFTER"
    # echo "Raw difference (comm -13):"
    # comm -13 "$IMAGES_BEFORE" "$IMAGES_AFTER"

    # 4️⃣ 找出新增的镜像 (即原始镜像)。排除掉带有本地Registry前缀的镜像本身。
    # 过滤条件：排除本地 registry 已存在的镜像，以及 <none> 引用。
    # 因为导入的 tarfile 可能会包含多个 tag，我们只取第一个符合条件的
    ORIGIN_IMG=$(comm -13 "$IMAGES_BEFORE" "$IMAGES_AFTER" | grep -vE "${LOCAL_REGISTRY_ADDR}|<none>" | head -n1|| true)

    if [ "$ORIGIN_IMG" = "" ]; then
        continue
    fi
    log_info "JUST A TEST"
    rm -f "$IMAGES_BEFORE" "$IMAGES_AFTER" # 清理临时文件

    if [[ -z "$ORIGIN_IMG" ]]; then
        echo "❌ Failed to detect original image name, skipping..."
        continue
    fi
    echo "Original image: $ORIGIN_IMG"

    NEW_IMG=""
    if [[ "$ORIGIN_IMG" == "registry.k8s.io/"* ]]; then
	if [[ "$ORIGIN_IMG" == "registry.k8s.io/coredns/"* ]]; then
		NEW_IMG="${LOCAL_REGISTRY_ADDR}/${ORIGIN_IMG#registry.k8s.io/coredns/}"
	else
		NEW_IMG="${LOCAL_REGISTRY_ADDR}/${ORIGIN_IMG#registry.k8s.io/}"
	fi
    elif [[ "$ORIGIN_IMG" == "ghcr.io/"* ]]; then
        NEW_IMG="${LOCAL_REGISTRY_ADDR}/${ORIGIN_IMG#ghcr.io/}"
    elif [[ "$ORIGIN_IMG" == "quay.io/"* ]]; then
        NEW_IMG="${LOCAL_REGISTRY_ADDR}/${ORIGIN_IMG#quay.io/}"
    elif [[ "$ORIGIN_IMG" == "nvcr.io/"* ]]; then
        NEW_IMG="${LOCAL_REGISTRY_ADDR}/${ORIGIN_IMG#nvcr.io/}"
    elif [[ "$ORIGIN_IMG" == "docker.io/"* ]]; then
        if [[ "$ORIGIN_IMG" == "docker.io/library/"* ]]; then
            NEW_IMG="${LOCAL_REGISTRY_ADDR}/${ORIGIN_IMG#docker.io/library/}"
        else
            NEW_IMG="${LOCAL_REGISTRY_ADDR}/${ORIGIN_IMG#docker.io/}"
        fi
    else
        echo "Warning: Unknown original registry prefix for $ORIGIN_IMG. Directly prepending LOCAL_REGISTRY_ADDR."
        NEW_IMG="${LOCAL_REGISTRY_ADDR}/${ORIGIN_IMG}"
    fi

    echo "Retag as: $NEW_IMG"

    # 4️⃣ 打 tag
    ctr -n "$NAMESPACE" images tag "$ORIGIN_IMG" "$NEW_IMG"

    # 5️⃣ 推送到本地 registry
    ctr -n "$NAMESPACE" images push --plain-http "$NEW_IMG"
    echo "tarfile=$tarfile ORIGIN_IMG=$ORIGIN_IMG NEW_IMG=$NEW_IMG"

    echo "✅ Done: $NEW_IMG"
done

log_info "所有镜像已导入 containerd 仓库并正确标记。"
log_info "当前 containerd 镜像列表 (前 20 条):"
ctr -n "$NAMESPACE" images ls | head -n 20 || true # 打印最终镜像列表以供检查

# ==============================================================================
# 8. 初始化 Kubernetes 控制平面
# ==============================================================================
log_info "初始化 Kubernetes 控制平面..."

# 确保 /etc/kubernetes 目录干净，防止 kubeadm init 失败
log_info "清理 /etc/kubernetes 目录..."
sudo kubeadm reset --force &>/dev/null || true # 强制重置 kubeadm 配置
sudo rm -rf /etc/kubernetes/* || log_warn "清理 /etc/kubernetes 目录失败，可能存在权限问题或文件被占用。"
sudo rm -rf "$HOME/.kube" # 清理用户 kubeconfig
log_info "已清理 /etc/kubernetes 目录和用户 .kube 配置。"

# 生成 kubeadm 配置
log_info "生成 kubeadm-config.yaml 配置..."
cat <<EOF | sudo tee ${TEMP_DIR}/kubeadm-config.yaml > /dev/null
apiVersion: kubeadm.k8s.io/v1beta3
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: "${K8S_APISERVER_ADVERTISE_ADDRESS}"   # 替换为实际 IP，比如 192.168.16.10
  bindPort: 6443
---
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
kubernetesVersion: ${K8S_VERSION}
imageRepository: ${LOCAL_REGISTRY_ADDR}    # ⬅️ 关键！指定本地镜像仓库
networking:
  podSubnet: ${POD_CIDR}
  serviceSubnet: ${SERVICE_CIDR}
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd                # 根据你的环境选择 systemd 或 cgroupfs
EOF

log_info "kubeadm-config.yaml 已生成，内容如下:"
cat ${TEMP_DIR}/kubeadm-config.yaml

# 运行 kubeadm init
log_info "运行 kubeadm init 命令..."
# --upload-certs: 上传证书到集群以便工作节点获取
# --config: 指定配置
# --ignore-preflight-errors=all: 忽略所有预检错误，但在生产环境建议逐一排查。
sudo kubeadm init --config=${TEMP_DIR}/kubeadm-config.yaml --upload-certs --ignore-preflight-errors=all

if [ $? -ne 0 ]; then
    log_error "kubeadm init 失败。"
fi

log_info "Kubernetes 控制平面初始化完成。"

# 配置 kubectl
log_info "配置 kubectl 访问集群..."
mkdir -p "$HOME/.kube"
sudo cp /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown $(id -u):$(id -g) "$HOME/.kube/config"
export KUBECONFIG=$HOME/.kube/config # 确保当前会话可用
log_info "kubectl 配置完成。"

log_info "等待 Kubernetes 控制平面 Pod 启动 (最多 5 分钟)..."
# 等待 kube-apiserver, kube-controller-manager, kube-scheduler Pod 启动
sleep 1
kubectl wait --for=condition=ready pod -l component=kube-apiserver -n kube-system --timeout=300s || log_error "kube-apiserver Pod 未能在指定时间内启动。"
kubectl wait --for=condition=ready pod -l component=kube-controller-manager -n kube-system --timeout=300s || log_error "kube-controller-manager Pod 未能在指定时间内启动。"
kubectl wait --for=condition=ready pod -l component=kube-scheduler -n kube-system --timeout=300s || log_error "kube-scheduler Pod 未能在指定时间内启动。"

log_info "核心控制平面组件已就绪。"
log_info "查看集群节点状态:"
kubectl get nodes

# ========
# 设置环境变量
# ========
mkdir -p $HOME/.kube
sudo cp /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# ==============================================================================
# 9. 安装 CNI 网络插件 (Calico)
# ==============================================================================
log_info "安装 CNI 网络插件 (Calico)..."

CALICO_MANIFEST_ORIG="${OFFLINE_ASSETS_DIR}/manifests/calico.yaml"
if [ ! -f "$CALICO_MANIFEST_ORIG" ]; then
    log_error "Calico 原始 manifest 文件 ${CALICO_MANIFEST_ORIG} 不存在。"
fi
CALICO_MANIFEST_TEMP="${TEMP_DIR}/calico.yaml"
cp "${CALICO_MANIFEST_ORIG}" "${CALICO_MANIFEST_TEMP}" || log_error "复制 Calico manifest 文件失败。"

# 替换 Calico 镜像地址
log_info "替换 Calico 镜像地址为本地仓库: ${LOCAL_REGISTRY_ADDR} ..."
# 注意：Calico 的镜像通常在 docker.io 下，所以替换规则不同于 k8s.io
sudo sed -i "s|docker.io/calico/cni:${CALICO_VERSION}|${LOCAL_REGISTRY_ADDR}/calico/cni:${CALICO_VERSION}|g" "${CALICO_MANIFEST_TEMP}"
sudo sed -i "s|docker.io/calico/node:${CALICO_VERSION}|${LOCAL_REGISTRY_ADDR}/calico/node:${CALICO_VERSION}|g" "${CALICO_MANIFEST_TEMP}"
sudo sed -i "s|docker.io/calico/kube-controllers:${CALICO_VERSION}|${LOCAL_REGISTRY_ADDR}/calico/kube-controllers:${CALICO_VERSION}|g" "${CALICO_MANIFEST_TEMP}"

# 设置 Pod CIDR
log_info "配置 Calico Pod CIDR: ${POD_CIDR} ..."
# 确保 # - name: CALICO_IPV4POOL_CIDR 及其下面的 value 行被取消注释并设置
sudo sed -i "s|# - name: CALICO_IPV4POOL_CIDR|- name: CALICO_IPV4POOL_CIDR|g" "${CALICO_MANIFEST_TEMP}"
sudo sed -i "s|#   value: \"192.168.0.0/16\"|  value: \"${POD_CIDR}\"|g" "${CALICO_MANIFEST_TEMP}"

# 在 calico.yaml 文件末尾添加 IPPool 资源 (如果文件中没有，或者确保它存在且配置正确)
if ! grep -q "kind: IPPool" "${CALICO_MANIFEST_TEMP}"; then
    log_info "在 Calico manifest 中添加 IPPool 资源定义..."
    echo -e "\n---\napiVersion: crd.projectcalico.org/v1\nkind: IPPool\nmetadata:\n  name: default-pool-ipv4\nspec:\n  cidr: ${POD_CIDR}\n  natOutgoing: true\n  disabled: false\n  ipipMode: Always" | sudo tee -a "${CALICO_MANIFEST_TEMP}" > /dev/null
else
    log_info "Calico IPPool 定义已存在，跳过添加。"
fi

log_info "应用 Calico manifest 文件..., 内容如下："
cat ${CALICO_MANIFEST_TEMP}
kubectl apply -f "${CALICO_MANIFEST_TEMP}" || log_error "应用 Calico manifest 失败。"
log_info "Calico 网络插件安装完成。"

log_info "等待 Calico Pod 启动 (最多 20 分钟)..."
sleep 10
kubectl wait --for=condition=ready pod -l k8s-app=calico-node -n kube-system --timeout=1900s || log_error "Calico Node Pod 未能在指定时间内启动。"
log_info "Calico Pods 已就绪。"

#============

# ==============================================================================
# 10. 安装 Multus CNI (用于 KubeVirt 虚拟机多网卡)
# ==============================================================================
log_info "安装 Multus CNI 插件..."
MULTUS_MANIFEST_ORIG="${OFFLINE_ASSETS_DIR}/manifests/multus-daemonset.yaml"
if [ ! -f "$MULTUS_MANIFEST_ORIG" ]; then
    log_error "Multus 原始 manifest 文件 ${MULTUS_MANIFEST_ORIG} 不存在。"
fi
MULTUS_MANIFEST_TEMP="${TEMP_DIR}/multus-daemonset.yaml"
cp "${MULTUS_MANIFEST_ORIG}" "${MULTUS_MANIFEST_TEMP}" || log_error "复制 Multus manifest 文件失败。"

log_info "替换 Multus CNI 镜像地址为本地仓库: ${LOCAL_REGISTRY_ADDR} ..."
# Multus CNI 的镜像通常在 ghcr.io/k8snetworkplumbingwg/ 或 docker.io 下
sudo sed -i "s|ghcr.io/k8snetworkplumbingwg/multus-cni:snapshot|${LOCAL_REGISTRY_ADDR}/k8snetworkplumbingwg/multus-cni:${MULTUS_VERSION}|g" "${MULTUS_MANIFEST_TEMP}"
sudo sed -i "s|docker.io/k8snetworkplumbingwg/multus-cni:snapshot|${LOCAL_REGISTRY_ADDR}/k8snetworkplumbingwg/multus-cni:${MULTUS_VERSION}|g" "${MULTUS_MANIFEST_TEMP}"

log_info "应用 Multus CNI manifest 文件..."
kubectl apply -f "${MULTUS_MANIFEST_TEMP}" || log_error "应用 Multus CNI manifest 失败。"
log_info "Multus CNI 插件安装完成。"

log_info "等待 Multus Pod 启动 (最多 5 分钟)..."
sleep 1
kubectl wait --for=condition=ready pod -l app=multus -n kube-system --timeout=300s || log_error "Multus Pod 未能在指定时间内启动。"
log_info "Multus Pods 已就绪。"

# ==============================================================================
# 11. 安装 KubeVirt (用于虚拟机管理)
# ==============================================================================
log_info "安装 KubeVirt..."

KUBEVIRT_OPERATOR_ORIG="${OFFLINE_ASSETS_DIR}/manifests/kubevirt-operator.yaml"

if [ ! -f "$KUBEVIRT_OPERATOR_ORIG" ]; then
    log_error "KubeVirt Operator 文件 ${KUBEVIRT_OPERATOR_ORIG} 不存在。"
fi

KUBEVIRT_OPERATOR_TEMP="${TEMP_DIR}/kubevirt-operator.yaml"
cp "${KUBEVIRT_OPERATOR_ORIG}" "${KUBEVIRT_OPERATOR_TEMP}" || log_error "复制 KubeVirt Operator 文件失败。"

log_info "替换 KubeVirt Operator 镜像地址为本地仓库: ${LOCAL_REGISTRY_ADDR} ..."
# KubeVirt 镜像通常在 quay.io/kubevirt
# 这里需要替换 operator 和所有由 operator 部署的组件的镜像
sudo sed -i "s|quay.io/kubevirt/virt-operator:${KUBEVIRT_VERSION}|${LOCAL_REGISTRY_ADDR}/kubevirt/virt-operator:${KUBEVIRT_VERSION}|g" "${KUBEVIRT_OPERATOR_TEMP}"
# sudo sed -i "s|quay.io/kubevirt/virt-controller:${KUBEVIRT_VERSION}|${LOCAL_REGISTRY_ADDR}/kubevirt/virt-controller:${KUBEVIRT_VERSION}|g" "${KUBEVIRT_OPERATOR_TEMP}"
# sudo sed -i "s|quay.io/kubevirt/virt-handler:${KUBEVIRT_VERSION}|${LOCAL_REGISTRY_ADDR}/kubevirt/virt-handler:${KUBEVIRT_VERSION}|g" "${KUBEVIRT_OPERATOR_TEMP}"
# sudo sed -i "s|quay.io/kubevirt/virt-launcher:${KUBEVIRT_VERSION}|${LOCAL_REGISTRY_ADDR}/kubevirt/virt-launcher:${KUBEVIRT_VERSION}|g" "${KUBEVIRT_OPERATOR_TEMP}"
# sudo sed -i "s|quay.io/kubevirt/virt-api:${KUBEVIRT_VERSION}|${LOCAL_REGISTRY_ADDR}/kubevirt/virt-api:${KUBEVIRT_VERSION}|g" "${KUBEVIRT_OPERATOR_TEMP}"
# sudo sed -i "s|quay.io/kubevirt/libguestfs-tools:${KUBEVIRT_VERSION}|${LOCAL_REGISTRY_ADDR}/kubevirt/libguestfs-tools:${KUBEVIRT_VERSION}|g" "${KUBEVIRT_OPERATOR_TEMP}"
# sudo sed -i "s|quay.io/kubevirt/bridge-marker:${KUBEVIRT_VERSION}|${LOCAL_REGISTRY_ADDR}/kubevirt/bridge-marker:${KUBEVIRT_VERSION}|g" "${KUBEVIRT_OPERATOR_TEMP}"
# sudo sed -i "s|quay.io/kubevirt/sidecar-shim:${KUBEVIRT_VERSION}|${LOCAL_REGISTRY_ADDR}/kubevirt/sidecar-shim:${KUBEVIRT_VERSION}|g" "${KUBEVIRT_OPERATOR_TEMP}"
# sudo sed -i "s|quay.io/kubevirt/qemu-bridge-helper:${KUBEVIRT_VERSION}|${LOCAL_REGISTRY_ADDR}/kubevirt/qemu-bridge-helper:${KUBEVIRT_VERSION}|g" "${KUBEVIRT_OPERATOR_TEMP}"
awk '
/^kind: Deployment/ {inDeployment=1}
inDeployment && /^  template:/ {inTemplate=1}
inTemplate && /^    spec:/ {inSpec=1}
inSpec && /^      tolerations:/ {
    print
    # 插入控制平面 toleration
    indent = match($0,/[^ ]/) - 1
    spaces = "                            "
    printf("%s- key: \"node-role.kubernetes.io/control-plane\"\n", substr(spaces, 1, indent))
    printf("%s  operator: \"Exists\"\n", substr(spaces, 1, indent))
    printf("%s  effect: \"NoSchedule\"\n", substr(spaces, 1, indent))
    # 标记已经插入，防止重复插入
    inserted=1
    next
}
# 如果已经插入，就不再修改其他 tolerations
{print}
' "${KUBEVIRT_OPERATOR_TEMP}" > ${TEMP_DIR}/kubevirt-operator-mod.yaml

cp ${TEMP_DIR}/kubevirt-operator-mod.yaml ${KUBEVIRT_OPERATOR_TEMP}
log_info "应用 KubeVirt Operator manifest 文件..."
kubectl apply -f "${KUBEVIRT_OPERATOR_TEMP}" || log_error "应用 KubeVirt Operator 失败。"
log_info "KubeVirt Operator 应用完成。"

log_info "等待 KubeVirt Operator 启动 (最多 15 分钟)..."
sleep 1
kubectl wait --for=condition=ready pod -l kubevirt.io=virt-operator -n kubevirt --timeout=900s || log_error "KubeVirt Operator Pod 未能在指定时间内启动。"
log_info "KubeVirt Operator Pods 已就绪。"

# ==============================================================================
# 12. 安装 NFS Client Provisioner (用于动态 PV/PVC)
# ==============================================================================
log_info "安装 NFS Client Provisioner..."

# 12.1 添加 Helm 仓库 (通常在线操作，离线场景下需要手动解压 chart)
log_info "加载 NFS Client Provisioner Helm Chart..."
NFS_CHART_TGZ="${OFFLINE_ASSETS_DIR}/charts/nfs-subdir-external-provisioner-${NFS_CHART_VERSION}.tgz"
if [ ! -f "$NFS_CHART_TGZ" ]; then
    log_error "NFS Client Provisioner Helm Chart 文件 ${NFS_CHART_TGZ} 不存在。"
fi

# 解压 chart 到临时目录
log_info "解压 Helm Chart 到临时目录..."
sudo mkdir -p "${TEMP_DIR}/nfs-client-provisioner"
sudo tar -xzf "$NFS_CHART_TGZ" -C "${TEMP_DIR}/nfs-client-provisioner" || log_error "解压 NFS Chart 失败。"
NFS_CHART_PATH="${TEMP_DIR}/nfs-client-provisioner/nfs-subdir-external-provisioner" # 解压后的实际目录

# 12.2 创建 NFS provisioner 的 values.yaml
log_info "创建 NFS Client Provisioner 的 values.yaml..."
cat <<EOF | sudo tee "${TEMP_DIR}/nfs-provisioner-values.yaml" > /dev/null
replicaCount: 1

strategy:
  type: Recreate

image:
  repository: ${LOCAL_REGISTRY_ADDR}/sig-storage/nfs-subdir-external-provisioner
  tag: ${NFS_PROVISIONER_VERSION}
  pullPolicy: IfNotPresent

nfs:
  server: ${NFS_SERVER}
  path: ${NFS_PATH}

storageClass:
  create: true
  name: ${NFS_STORAGE_CLASS_NAME}
  defaultClass: true
  provisionerName: ${NFS_STORAGE_CLASS_NAME}
  reclaimPolicy: Delete
  archiveOnDelete: true

# 允许 Pod 调度到 control-plane 节点
tolerations:
  - key: "node-role.kubernetes.io/control-plane"
    operator: "Exists"
    effect: "NoSchedule"

# 如果你想强制跑在控制节点（通常单节点集群推荐）
# 控制节点通常带有 label：node-role.kubernetes.io/control-plane=""
nodeSelector:
  node-role.kubernetes.io/control-plane: ""

# 也可以留空不写，K8s 会随机选择节点
# nodeSelector: {}

EOF

log_info "NFS Client Provisioner values.yaml 已生成，内容如下:"
cat "${TEMP_DIR}/nfs-provisioner-values.yaml"

# 12.3 部署 NFS Client Provisioner (使用 Helm)
log_info "使用 Helm 部署 NFS Client Provisioner..."

# 检查是否已安装，如果已安装则升级，否则安装
if helm status nfs-client-provisioner -n kube-system &>/dev/null; then
    log_info "NFS Client Provisioner 已存在，进行升级..."
    helm upgrade nfs-client-provisioner "${NFS_CHART_PATH}" \
        --install \
        --namespace kube-system \
        --values "${TEMP_DIR}/nfs-provisioner-values.yaml" \
        --version "${NFS_CHART_VERSION}" || log_error "升级 NFS Client Provisioner 失败。"
else
    log_info "NFS Client Provisioner 未安装，进行安装..."
    helm install nfs-client-provisioner "${NFS_CHART_PATH}" \
        --namespace kube-system \
        --values "${TEMP_DIR}/nfs-provisioner-values.yaml" \
        --version "${NFS_CHART_VERSION}" || log_error "安装 NFS Client Provisioner 失败。"
fi

log_info "NFS Client Provisioner Helm Chart 应用完成。"

log_info "等待 NFS Client Provisioner Pod 启动 (最多 5 分钟)..."
sleep 1
kubectl wait --for=condition=ready pod -l app=nfs-subdir-external-provisioner -n kube-system --timeout=300s || log_error "NFS Client Provisioner Pod 未能在指定时间内启动。"
log_info "NFS Client Provisioner Pods 已就绪。"

log_info "设置默认 StorageClass 为 ${NFS_STORAGE_CLASS_NAME}..."
# 确保旧的默认 StorageClass 被取消默认
kubectl patch storageclass $(kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}') -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}' &>/dev/null || true
# 设置新的默认 StorageClass
kubectl patch storageclass "${NFS_STORAGE_CLASS_NAME}" -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}' || log_error "设置 ${NFS_STORAGE_CLASS_NAME} 为默认 StorageClass 失败。"
log_info "${NFS_STORAGE_CLASS_NAME} 已设置为默认 StorageClass。"

# ==============================================================================
# 13. KubeVirt 额外配置 (如 NetworkAttachmentDefinition 示例)
# ==============================================================================
log_info "应用 KubeVirt 额外配置 (示例 NetworkAttachmentDefinition)..."

# 如果需要，这里可以添加其他 NetworkAttachmentDefinition
# 例如，一个 vlan 接口
cat <<EOF | kubectl apply -f -
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: example-vlan-net
  namespace: default
spec:
  config: '{
      "cniVersion": "0.3.1",
      "type": "bridge",
      "bridge": "br1",
      "vlan": 100,
      "ipam": {
        "type": "whereabouts",
        "range": "192.168.100.0/24"
      }
    }'
EOF
# 注意：whereabouts 需要单独安装，这里只是一个示例。
# 如果没有安装 whereabouts，请替换为 host-local 或其他 IPAM 插件。
log_info "示例 NetworkAttachmentDefinition 'example-vlan-net' 已应用 (如果 whereabouts 未安装，此配置可能不会完全生效)。"

# ==============================================================================
# 14. 验证集群状态和安装结果
# ==============================================================================
log_info "--------------------------------------------------"
log_info "所有安装步骤完成，开始最终验证..."
log_info "--------------------------------------------------"

log_info "验证所有命名空间下的 Pod 状态..."
kubectl get pods --all-namespaces

log_info "等待所有 Pods 达到 Ready 状态 (最多 10 分钟)..."
# 注意：此命令可能会在 Pod 数量多时耗时较长
sleep 1
kubectl wait --for=condition=ready --all pods --all-namespaces --timeout=600s || log_warn "并非所有 Pods 都达到 Ready 状态，请手动检查。"

log_info "验证集群节点状态..."
kubectl get nodes

log_info "验证 StorageClass 状态..."
kubectl get sc

log_info "验证 KubeVirt 状态..."
kubectl get kubevirts -n kubevirt

log_info "KubeVirt 预期输出示例： STATUS 为 'Deployed'"
virtctl version || log_warn "virtctl 命令可能未安装或不在 PATH 中。"

# ==============================================================================
# 15. 输出加入命令
# ==============================================================================
log_info "--------------------------------------------------"
log_info "Kubernetes 控制平面离线安装完成！"
log_info "使用以下命令将工作节点加入集群："
log_info "--------------------------------------------------"
sudo kubeadm token create --print-join-command
echo ""
log_info "请注意保存上述命令，因为令牌有过期时间。"

log_info "清理临时目录: ${TEMP_DIR}"
sudo rm -rf "${TEMP_DIR}"

log_info "脚本执行完毕。"

