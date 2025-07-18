# 暂时不用
# from appPublic import sshx
# 后面有空了再改成g.debug
import time
import os
import re
from appPublic.log import debug
import paramiko
import socket
import traceback

async def ssh_execute_command(host, port, username, password, commands, real_time_log=False, 
                        remote_exec=True, scp_map=dict()):
    try:
        # 创建 SSH 对象
        ssh = paramiko.SSHClient()
        # 允许连接不在 know_hosts 文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        ssh.connect(hostname=host, port=port, username=username, password=password)
        all_results = []
        if scp_map:
            # 创建 SFTP 客户端对象
            sftp = ssh.open_sftp()
            # 构建脚本内部调用脚本json
            for sf,df in scp_map.items():
                # 上传文件
                debug(f"远程拷贝 {sf=} => {df=}")
                sftp.put(sf, df)
            # 关闭 SFTP 连接
            sftp.close()
        if remote_exec:
            # 通用流程
            result = ""
            error = ""
            for command in commands:
                stdin, stdout, stderr = ssh.exec_command(f'{command}', get_pty=True)
                stdin.flush()
                if real_time_log:
                    debug(f"开始执行命令: {command=}, 请耐心等待...")
                    # 实时读取标准输出
                    for line in iter(stdout.readline, ""):
                        debug(f'{line=}')
                        result += line
                    # 实时读取标准错误输出
                    for line in iter(stderr.readline, ""):
                        debug(f'{line=}')
                        error += line
                else:
                    result = stdout.read().decode(errors="replace")
                    error = stderr.read().decode(errors="replace")

                all_results.append((result, error))
                if real_time_log:
                    debug(f"命令 {command=} 执行结束")
        # 关闭连接
        ssh.close()
        return all_results
    except Exception as e:
        debug(f"SSH连接或执行命令时出错: {e=}")
        return [e]
    
# ----------------------------------------以下是非Root用户进行Root操作基座-------------------------------------------

async def ssh_execute_command_noroot(host, port, username, password, commands, real_time_log=False,
                        remote_exec=True, scp_map=dict(), temp_dir="/tmp/ssh_temp", sudo_timeout=500):
    """
    增强版SSH执行命令函数，支持普通用户向root目录传输文件和执行sudo命令
    sudo_timeout参数控制sudo命令的超时时间（秒）
    """
    try:
        # 创建SSH连接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, port=port, username=username, password=password)
        all_results = []

        # 创建临时目录（如果需要文件传输）
        if scp_map:
            # 创建临时目录
            create_temp_cmd = f"mkdir -p {temp_dir} && chmod 700 {temp_dir}"
            stdin, stdout, stderr = ssh.exec_command(create_temp_cmd)
            create_error = stderr.read().decode(errors="replace")
            if create_error:
                raise Exception(f"创建临时目录失败: {create_error}")

            # 创建SFTP客户端
            sftp = ssh.open_sftp()

            # 上传文件到临时目录
            temp_scp_map = {}
            for local_path, remote_path in scp_map.items():
                # 确定临时目标路径
                temp_remote_path = f"{temp_dir}/{os.path.basename(remote_path)}"
                debug(f"上传文件 {local_path} => {temp_remote_path}")
                sftp.put(local_path, temp_remote_path)
                temp_scp_map[temp_remote_path] = remote_path

            # 关闭SFTP连接
            sftp.close()

            # 将文件从临时目录移动到目标位置（需要sudo权限）
            for temp_path, final_path in temp_scp_map.items():
                # 确保目标目录存在
                mkdir_cmd = f"sudo mkdir -p $(dirname {final_path})"
                await execute_sudo_command(ssh, mkdir_cmd, password, real_time_log, sudo_timeout, username)

                # 移动文件
                move_cmd = f"sudo mv {temp_path} {final_path}"
                await execute_sudo_command(ssh, move_cmd, password, real_time_log, sudo_timeout, username)

                # 设置文件权限
                chmod_cmd = f"sudo chmod 644 {final_path}"
                if final_path.endswith('.sh'):  # 脚本文件设置可执行权限
                    chmod_cmd = f"sudo chmod 755 {final_path}"
                await execute_sudo_command(ssh, chmod_cmd, password, real_time_log, sudo_timeout, username)

        # 执行远程命令（如果需要）
        if remote_exec:
            for command in commands:
                # 执行需要sudo权限的命令
                result, error = await execute_sudo_command(ssh, command, password, real_time_log, sudo_timeout, username)
                all_results.append((result, error))

        # 清理临时目录
        if scp_map:
            cleanup_cmd = f"rm -rf {temp_dir}"
            stdin, stdout, stderr = ssh.exec_command(cleanup_cmd)

        # 关闭SSH连接
        ssh.close()
        return all_results

    except Exception as e:
        debug(f"SSH操作错误: {traceback.format_exc()}")
        raise e
        return [(None, str(e))]


async def execute_sudo_command(ssh, command, password, real_time_log, sudo_timeout, username):
    """
    执行需要sudo权限的命令，处理密码交互和超时
    """
    sudo_cmd = f"sudo -S -p '[sudo] password: ' {command}"  # -k参数确保每次都需要密码
    # sudo_cmd = f"sudo -k -S -p '[sudo] password: ' {command}"  # 正确方式
    stdin, stdout, stderr = ssh.exec_command(sudo_cmd, get_pty=True)
    # 真实的sudo命令执行
    # sudo -p '[sudo] password: ' echo hello
    # 设置命令超时
    channel = stdout.channel
    channel.settimeout(timeout=sudo_timeout)

    # 处理密码提示
    password_prompt = False
    initial_output = ""

    try:
        debug("等待sudo密码提示...")
        start_time = time.time()
        while True:
            ready = False
            # 检查stdout
            if channel.recv_ready():
                # 此处发现chunk长度可能为一个标准kubeconfig长度，导致无法正确读取所有输出
                chunk = channel.recv(5800).decode(errors="replace")
                initial_output += chunk
                debug(f"stdout: {chunk.strip()}")
                if re.search(r"\[sudo\] password:", chunk):
                    password_prompt = True
                    stdin.write(f"{password}\n")
                    stdin.flush()
                    break
                ready = True
            # 检查stderr
            if channel.recv_stderr_ready():
                chunk = channel.recv_stderr(5800).decode(errors="replace")
                initial_output += chunk
                debug(f"stderr: {chunk.strip()}")
                if re.search(r"\[sudo\] password:", chunk):
                    password_prompt = True
                    stdin.write(f"{password}\n")
                    stdin.flush()
                    break
                ready = True
            # 超时检测
            if time.time() - start_time > sudo_timeout:
                raise Exception(f"等待sudo密码提示超时（{sudo_timeout}秒）: {sudo_cmd}")
            if not ready:
                time.sleep(0.5)  # 避免CPU占用过高

        # 如果没有收到密码提示但命令执行超时，可能是权限问题
        if not password_prompt:
            # 等待一段时间，确保没有密码提示
            time.sleep(3)
            # debug(f"ssh初步连接初始输出: {initial_output}")
            if not re.search(r"\[sudo\] password:", initial_output):
                raise Exception(f"未收到密码提示，可能sudo配置不允许该用户执行此命令: {sudo_cmd}")

    except socket.timeout:
        raise Exception(f"命令执行超时（{sudo_timeout}秒）: {sudo_cmd}")

    # 收集命令输出
    result = initial_output if not password_prompt else ""
    error = ""

    try:
        if real_time_log:
            debug(f"执行命令: {sudo_cmd}")
            # 实时读取标准输出
            while True:
                if channel.recv_ready():
                    line = channel.recv(5800).decode(errors="replace")
                    debug(f"输出: {line.strip()}")
                    result += line
                if channel.recv_stderr_ready():
                    line = channel.recv_stderr(5800).decode(errors="replace")
                    debug(f"错误: {line.strip()}")
                    error += line
                if channel.exit_status_ready():
                    break
                time.sleep(0.1)  # 避免CPU占用过高
        else:
            # 非实时模式读取输出
            result += channel.recv(-1).decode(errors="replace") if channel.recv_ready() else ""
            error += channel.recv_stderr(-1).decode(errors="replace") if channel.recv_stderr_ready() else ""

    except socket.timeout:
        raise Exception(f"命令执行超时（{sudo_timeout}秒）: {sudo_cmd}")

    # 获取命令退出状态
    exit_status = channel.recv_exit_status()

    # 检查sudo执行是否失败
    if exit_status != 0:
        if "incorrect password attempt" in error.lower():
            error = f"密码错误，无法执行sudo命令: {sudo_cmd}"
        elif "not allowed to run sudo" in error.lower():
            error = f"用户 {username} 没有sudo权限执行此命令: {sudo_cmd}"

    return result, error
