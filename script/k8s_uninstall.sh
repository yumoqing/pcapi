#!/bin/bash
set -euo pipefail

# 颜色输出函数
red_echo() { echo -e "\033[31m$1\033[0m"; }
green_echo() { echo -e "\033[32m$1\033[0m"; }
yellow_echo() { echo -e "\033[33m$1\033[0m"; }

# 强制清理函数
force_clean() {
    local cmd=$*
    if eval "$cmd"; then
        green_echo "  执行成功: $cmd"
    else
        yellow_echo "  执行失败，但继续: $cmd"
    fi
}

# ========================
# 核心函数：彻底清理tunl0接口
# ========================
clean_tunl0() {
    green_echo "  专项清理tunl0接口..."
    # 尝试1：常规停用+删除
    force_clean "ip link set tunl0 down || true"
    force_clean "ip link delete tunl0 || true"
    
    # 尝试2：卸载ipip模块后删除（tunl0依赖的内核模块）
    force_clean "rmmod ipip || true"
    force_clean "ip link delete tunl0 || true"
    
    # 尝试3：检查是否有残留的tunl0配置并删除
    if ip link show tunl0 &> /dev/null; then
        force_clean "ip link set tunl0 nomaster || true"  # 移除主接口关联
        force_clean "ip link delete tunl0 || true"
    fi
}

# ========================
# 第一阶段：强制清理核心组件
# ========================
cleanup_core() {
    green_echo "===== 第一阶段：清理核心K8s组件 ====="

    # 1. 强制终止所有相关进程
    green_echo "1. 强制终止K8s/容器相关进程..."
    force_clean "ps -aux | grep -E 'kube|etcd|containerd|docker|cni|flannel|tunl0' | grep -v grep | awk '{print \$2}' | xargs -r kill -9"
    force_clean "pkill -f 'kube|etcd|containerd|docker|cni|flannel' || true"

    # 2. 强制清理网络资源（优先处理tunl0）
    green_echo "2. 强制清理网络资源..."
    clean_tunl0  # 调用专项清理函数
    
    # 清理其他网络接口
    force_clean "ip link set flannel.1 down || true"
    force_clean "ip link delete flannel.1 || true"
    force_clean "ip link set cni0 down || true"
    force_clean "ip link delete cni0 || true"
    force_clean "ip link set docker0 down || true"
    force_clean "ip link delete docker0 || true"
    
    # 清理路由和规则
    force_clean "ip route flush proto bird || true"
    force_clean "rm -rf /var/lib/cni/* /etc/cni/net.d/* || true"
    force_clean "iptables -F && iptables -t nat -F && iptables -t mangle -F && iptables -X || true"
    force_clean "ip6tables -F && ip6tables -t nat -F && ip6tables -t mangle -F && ip6tables -X || true"
    force_clean "ipvsadm --clear || true"

    # 3. 强制重置K8s配置
    green_echo "3. 强制重置K8s配置..."
    force_clean "kubeadm reset -f --cri-socket unix:///var/run/containerd/containerd.sock || true"
    force_clean "kubeadm reset -f --cri-socket unix:///var/run/docker.sock || true"
    force_clean "rm -f /etc/kubernetes/flannel/* || true"
}

# ========================
# 第二阶段：彻底卸载软件包
# ========================
cleanup_packages() {
    green_echo "\n===== 第二阶段：彻底卸载软件包 ====="
    force_clean "apt-get purge -y kubelet kubectl kubeadm kubernetes-cni cri-tools --allow-change-held-packages || true"
    force_clean "dpkg -P kubelet kubectl kubeadm kubernetes-cni cri-tools || true"
    force_clean "apt-get purge -y containerd containerd.io docker-ce docker-ce-cli docker-buildx-plugin docker-compose-plugin --allow-change-held-packages || true"
    force_clean "dpkg -P containerd containerd.io docker-ce docker-ce-cli || true"
    force_clean "apt-get autoremove -y --purge || true"
    force_clean "apt-get autoclean || true"
}

# ========================
# 第三阶段：删除所有相关目录
# ========================
cleanup_directories() {
    green_echo "\n===== 第三阶段：删除所有相关目录 ====="
    
    # 卸载containerd挂载点
    green_echo "  卸载containerd挂载点..."
    local containerd_mounts=$(mount | grep "containerd" | awk '{print $3}')
    if [ -n "$containerd_mounts" ]; then
        force_clean "echo '$containerd_mounts' | xargs -I {} umount -l {} || true"
    else
        green_echo "  无containerd挂载点需要卸载"
    fi
    
    # 卸载SHM挂载点
    green_echo "  卸载共享内存(SHM)挂载点..."
    local shm_mounts=$(mount | grep "tmpfs.*type tmpfs (rw,nosuid,nodev,noexec,relatime,size=65536k,mode=700)" | awk '{print $3}')
    if [ -n "$shm_mounts" ]; then
        force_clean "echo '$shm_mounts' | xargs -I {} umount -l {} || true"
    else
        green_echo "  无SHM挂载点需要卸载"
    fi
    
    # 处理活跃的SHM文件（临时关闭set -e避免退出）
    green_echo "  删除所有活跃的SHM文件..."
    set +e
    for pid in $(ls -1 /proc/ 2>/dev/null | grep -E '^[0-9]+$' || true); do
        if [ -f "/proc/$pid/mounts" ] && [ -r "/proc/$pid/mounts" ]; then
            grep "shm" "/proc/$pid/mounts" 2>/dev/null | grep "containerd" 2>/dev/null | while read -r line; do
                shm_path=$(echo "$line" | awk '{print $2}')
                if [ -n "$shm_path" ] && [ -d "$shm_path" ]; then
                    umount -l "$shm_path" 2>/dev/null || true
                    echo "  已尝试卸载SHM: $shm_path"
                fi
            done
        fi
    done
    set -e
    
    # 清理/k8sdata目录内容
    green_echo "  清理/k8sdata目录内容..."
    force_clean "rm -rf /k8sdata/* /k8sdata/.* || true"
    
    # 清理containerd残留目录
    green_echo "  清理containerd容器残留..."
    force_clean "rm -rf /run/containerd/io.containerd.grpc.v1.cri/sandboxes/* || true"
    force_clean "rm -rf /run/containerd/io.containerd.runtime.v2.task/k8s.io/* || true"
    
    # 清理其他目录
    local dirs=(
        /etc/kubernetes /var/lib/kubelet /var/lib/kubernetes /var/lib/etcd
        /var/lib/kube-proxy /var/lib/kubeadm /var/lib/cni
        /var/lib/containerd /var/lib/docker /run/containerd /run/docker
        /etc/containerd /etc/docker /usr/local/bin/kube* /usr/local/bin/etcd*
        $HOME/.kube /root/.kube /var/lib/flannel /etc/flannel
    )
    for dir in "${dirs[@]}"; do
        force_clean "rm -rf $dir || true"
        if [ -d "$dir" ]; then
            force_clean "rm -rf --one-file-system $dir || true"
        fi
    done
}

# ========================
# 第四阶段：清理系统服务
# ========================
cleanup_services() {
    green_echo "\n===== 第四阶段：清理系统服务 ====="
    local services=(kubelet kube-apiserver kube-controller-manager kube-scheduler kube-proxy etcd containerd docker)
    for service in "${services[@]}"; do
        force_clean "systemctl stop $service || true"
        force_clean "systemctl disable $service || true"
        force_clean "rm -f /lib/systemd/system/$service.service || true"
        force_clean "rm -f /etc/systemd/system/$service.service || true"
        force_clean "rm -f /etc/systemd/system/multi-user.target.wants/$service.service || true"
    done
    force_clean "systemctl daemon-reload || true"
    force_clean "systemctl reset-failed || true"
}

# ========================
# 最终验证：确保无残留（含tunl0专项检查）
# ========================
verify_perfect_cleanup() {
    green_echo "\n===== 最终验证：确保无残留 ====="
    local is_perfect=true

    # 1. 验证进程无残留
    green_echo "1. 验证进程无残留..."
    local processes=$(ps -aux | grep -E 'kube|etcd|containerd|docker|cni|flannel' | grep -v grep)
    if [ -n "$processes" ]; then
        red_echo "  ❌ 发现残留进程:"
        echo "$processes"
        is_perfect=false
    else
        green_echo "  ✔️ 无残留进程"
    fi

    # 2. 验证命令无残留
    green_echo "2. 验证命令无残留..."
    local cmds=(kubectl kubeadm kubelet containerd docker etcd)
    for cmd in "${cmds[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            red_echo "  ❌ 命令 $cmd 仍存在"
            is_perfect=false
        fi
    done
    if [ "$is_perfect" = true ]; then
        green_echo "  ✔️ 无残留命令"
    fi

    # 3. 验证目录无残留
    green_echo "3. 验证目录无残留..."
    # 验证/k8sdata是否为空
    if [ "$(ls -A /k8sdata 2>/dev/null)" ]; then
        red_echo "  ❌ 目录/k8sdata不为空"
        is_perfect=false
    else
        green_echo "  ✔️ 目录/k8sdata为空"
    fi
    # 验证containerd目录是否为空
    if [ "$(ls -A /run/containerd/io.containerd.grpc.v1.cri/sandboxes 2>/dev/null)" ]; then
        red_echo "  ❌ containerd沙箱目录不为空"
        is_perfect=false
    else
        green_echo "  ✔️ containerd沙箱目录为空"
    fi
    if [ "$(ls -A /run/containerd/io.containerd.runtime.v2.task/k8s.io 2>/dev/null)" ]; then
        red_echo "  ❌ containerd运行时目录不为空"
        is_perfect=false
    else
        green_echo "  ✔️ containerd运行时目录为空"
    fi
    # 验证其他目录
    local other_dirs=(
        /etc/kubernetes /var/lib/kubelet /var/lib/etcd /var/lib/cni
        /var/lib/containerd /var/lib/docker $HOME/.kube /var/lib/flannel
    )
    for dir in "${other_dirs[@]}"; do
        if [ -d "$dir" ] || [ -f "$dir" ]; then
            red_echo "  ❌ 目录/文件 $dir 仍存在"
            is_perfect=false
        fi
    done

    # 4. 验证网络无残留（核心：tunl0专项检查+最后清理）
    green_echo "4. 验证网络无残留..."
    # 最后一次尝试清理tunl0（防止验证前重新出现）
    clean_tunl0
    # 检查残留接口
    local interfaces=$(ip link show | grep -E 'cni0|flannel.1|docker0|tunl0' | awk '{print $2}' | sed 's/://')
    if [ -n "$interfaces" ]; then
        red_echo "  ❌ 发现残留网络接口: $interfaces (如果是tunl0请忽略)"
        is_perfect=false
    else
        green_echo "  ✔️ 无残留网络接口"
    fi

    # 最终结果
    if [ "$is_perfect" = true ]; then
        green_echo "\n🎉 完美清理！系统中已无任何K8s相关残留，可安全重新安装。"
    else
        red_echo "\n❌ 清理不彻底！以上残留项需手动处理。"
        exit 1
    fi
}

# ========================
# 执行完整流程
# ========================
green_echo "===== 开始K8s彻底清理流程 ====="
cleanup_core
cleanup_packages
cleanup_directories
cleanup_services
sleep 20  # 延长等待，确保内核释放所有资源
verify_perfect_cleanup