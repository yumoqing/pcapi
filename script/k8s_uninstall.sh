#!/bin/bash
set -euo pipefail

# 定义颜色输出函数
red_echo() {
    echo -e "\033[31m$1\033[0m"
}
green_echo() {
    echo -e "\033[32m$1\033[0m"
}
yellow_echo() {
    echo -e "\033[33m$1\033[0m"
}

# ========================
# 清理流程
# ========================
cleanup_steps() {
    # 1. 停止服务
    green_echo "1. 停止K8s及容器运行时服务..."
    systemctl stop kubelet kube-apiserver kube-controller-manager kube-scheduler kube-proxy etcd nfs-kernel-server containerd docker &> /dev/null || true
    systemctl disable kubelet kube-apiserver kube-controller-manager kube-scheduler kube-proxy etcd nfs-kernel-server containerd docker &> /dev/null || true

    # 2. 清理进程
    green_echo "2. 清理K8s相关进程..."
    ps -aux | grep -E 'kube|etcd|containerd|docker' | grep -v grep | awk '{print $2}' | xargs -r kill -9 &> /dev/null || true

    # 3. 清理网络资源
    green_echo "3. 清理CNI网络资源..."
    ip link delete cni0 &> /dev/null || true
    ip link delete flannel.1 &> /dev/null || true
    rm -rf /var/lib/cni/networks/* /var/lib/cni/loader/* /etc/cni/net.d/* &> /dev/null || true

    # 4. kubeadm reset
    green_echo "4. 执行kubeadm reset..."
    kubeadm reset -f &> /dev/null || true

    # 5. 卸载软件包
    green_echo "5. 卸载K8s及容器运行时软件包..."
    apt-get purge -y kubelet kubectl kubeadm kubernetes-cni cri-tools containerd.io docker-ce docker-ce-cli &> /dev/null || true
    apt-get autoremove -y &> /dev/null || true

    # 6. 清理配置和数据目录
    green_echo "6. 清理配置和数据目录..."
    rm -rf /etc/kubernetes /var/lib/kubelet /var/lib/kubernetes /var/lib/etcd /var/lib/kubeadm /var/lib/kube-proxy /var/lib/containerd /var/lib/docker &> /dev/null || true

    # 7. 清理systemd服务残留
    green_echo "7. 清理systemd服务残留..."
    rm -f /lib/systemd/system/{containerd,docker,kubelet}.service &> /dev/null || true
    rm -f /etc/systemd/system/multi-user.target.wants/{containerd,docker,kubelet}.service &> /dev/null || true
    systemctl daemon-reload &> /dev/null || true

    # 8. 清理网络规则
    green_echo "8. 清理iptables和ipvs规则..."
    iptables -F && iptables -t nat -F && iptables -t mangle -F && iptables -X &> /dev/null || true
    ipvsadm --clear &> /dev/null || true

    # 9. 清理源和kubeconfig
    green_echo "9. 清理软件源和kubeconfig..."
    rm -rf /etc/apt/sources.list.d/{docker,kubernetes,kuboard}* &> /dev/null || true
    rm -rf $HOME/.kube/config &> /dev/null || true

    # 10. 更新软件包缓存
    green_echo "10. 更新软件包缓存..."
    apt-get update &> /dev/null || true
}

# ========================
# 验证清理结果
# ========================
verify_cleanup() {
    green_echo "\n开始验证清理结果..."
    local is_clean=true

    # 检查关键服务状态
    for service in kubelet docker containerd; do
        if systemctl is-active "$service" &> /dev/null; then
            red_echo "  ❌ 服务 $service 仍在运行"
            is_clean=false
        else
            green_echo "  ✔️ 服务 $service 已停止"
        fi
    done

    # 检查关键命令是否残留
    for cmd in kubectl kubeadm docker containerd; do
        if command -v "$cmd" &> /dev/null; then
            red_echo "  ❌ 命令 $cmd 仍存在"
            is_clean=false
        else
            green_echo "  ✔️ 命令 $cmd 已移除"
        fi
    done

    # 检查关键目录是否残留
    for dir in /etc/kubernetes /var/lib/kubelet /var/lib/containerd /var/lib/docker; do
        if [ -d "$dir" ]; then
            red_echo "  ❌ 目录 $dir 未完全清理"
            is_clean=false
        else
            green_echo "  ✔️ 目录 $dir 已删除"
        fi
    done

    # 最终结果
    if $is_clean; then
        green_echo "\n🎉 清理成功！环境已准备好重新安装K8s。"
    else
        red_echo "\n❌ 清理不彻底，请手动检查残留项！"
    fi
}

# ========================
# 执行清理和验证
# ========================
cleanup_steps
verify_cleanup