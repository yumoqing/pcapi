def ssh_execute_commands(host, port, username, password, commands, real_time_log=False):
    try:
        import paramiko
        # 创建 SSH 对象
        ssh = paramiko.SSHClient()
        # 允许连接不在 know_hosts 文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        ssh.connect(hostname=host, port=port, username=username, password=password)
        all_results = []
        result = ""
        error = ""
        for command in commands:
        #     stdin, stdout, stderr = ssh.exec_command(f'sudo -S {command}', get_pty=True)
        #     stdin.write(password + '\n')
            stdin, stdout, stderr = ssh.exec_command(f'{command}', get_pty=True)
            stdin.flush()
            if real_time_log:
                print(f"开始执行命令: {command}")
                # 实时读取标准输出
                for line in iter(stdout.readline, ""):
                    print(line, end="")
                    result += line
                # 实时读取标准错误输出
                for line in iter(stderr.readline, ""):
                    print(line, end="")
                    error += line
            else:
                result = stdout.read().decode()
                error = stderr.read().decode()

            all_results.append((result, error))
            if real_time_log:
                print(f"命令 {command} 执行结束")

        # 关闭连接
        ssh.close()
        return all_results
    except Exception as e:
        print(f"SSH 连接或执行命令时出错: {e}")
        return None

def new_cluster(params):
    # 随后填充远程操控k8s主逻辑
    """
        用于接收cpcc端传递过来的k8s安装指令参数，进行远程sshx调用操作内网机器进行集群节点的安装
        参数示例：
        {'cluster_type': '0', 'host': '192.168.0.3', 'port': '22', 'user': 'ysh', 'password': 'Kyy@123456'}
    """
    host = params.get("host")
    port = int(params.get("port"))
    username = params.get("user")
    password = params.get("password")
    commands = ['cd /install/ && ./k8s_install_1804.sh master','cd /install/ && cat join_command.txt']
    results = ssh_execute_commands(host, port, username, password, commands, real_time_log=True)
    if results:
        print("所有命令执行的整体结果：")
        for result, error in results:
            if result:
                print("执行结果：")
                print(result)
            if error:
                print("错误信息：")
                print(error)
    return results

if __name__ == "__main__":
    params = {'cluster_type': '0', 'host': '192.168.0.2', 'port': '22', 'user': 'root', 'password': 'Yuanshenhong.1'}
    new_cluster(params)
    
