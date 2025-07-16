def ssh_execute_command(host, port, username, password, commands, real_time_log=False, 
                        remote_exec=True, scp_map=dict()):
    try:
        import os
        import paramiko
        # 创建 SSH 对象
        ssh = paramiko.SSHClient()
        # 允许连接不在 know_hosts 文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        ssh.connect(hostname=host, port=port, username=username, password=password)
        all_results = []
        if scp_map:
            sftp = ssh.open_sftp()
            for sf, df in scp_map.items():
                # 1. 上传到 /tmp/ 目录
                tmp_path = f"/tmp/{os.path.basename(df)}"
                print(f"上传 {sf} 到临时目录 {tmp_path}")
                sftp.put(sf, tmp_path)

                # 2. 用 sudo 移动到目标目录
                cmd = f"echo {password} | sudo mv {tmp_path} {df}"
                print(f"用 sudo 移动 {tmp_path} 到 {df}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    print(f"移动失败: {stderr.read().decode()}")
                else:
                    print("移动成功")
            sftp.close()
        if remote_exec:
            # 通用流程
            result = ""
            error = ""
            for command in commands:
                stdin, stdout, stderr = ssh.exec_command(f'{command}', get_pty=True)
                stdin.flush()
                if real_time_log:
                    print(f"开始执行命令: {command=}, 请耐心等待...")
                    # 实时读取标准输出
                    for line in iter(stdout.readline, ""):
                        print(f'{line=}')
                        result += line
                    # 实时读取标准错误输出
                    for line in iter(stderr.readline, ""):
                        print(f'{line=}')
                        error += line
                else:
                    result = stdout.read().decode()
                    error = stderr.read().decode()

                all_results.append((result, error))
                if real_time_log:
                    print(f"命令 {command=} 执行结束")
        # 关闭连接
        ssh.close()
        return all_results
    except Exception as e:
        print(f"SSH连接或执行命令时出错: {e=}")
        return [e]
    
if __name__ == "__main__":
    # 测试代码
    host = ""
    port = 22
    username = ""
    password = ""
    commands = ["sudo", "apt-get update"]
    scp_map = {
        "local_file.txt": "/remote/path/remote_file.txt"
    }
    results = ssh_execute_command(host, port, username, password, commands, real_time_log=True, scp_map=scp_map)
    for result, error in results:
        print(f"Result: {result}")
        print(f"Error: {error}")
# This code is a simplified version of the SSH command execution utility.
# It uses the paramiko library to connect to a remote server and execute commands.
# The code includes functionality for uploading files via SFTP and executing commands with real-time logging.
# This code is a simplified version of the SSH command execution utility.