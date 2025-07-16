import socket

def get_local_ipv4():
    """获取本机IPv4地址"""
    try:
        # 获取本机所有网络接口信息
        local_ip = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        # 如果上述方式失败（例如,主机名无法解析）,则尝试以下备用方法
        local_ip = ([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
            if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) 
            for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])
    return local_ip

if __name__ == "__main__":
    print(get_local_ipv4())