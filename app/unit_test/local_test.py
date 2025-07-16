import re

def parse_resource_value(value_str, resource_type, unit):
    """
    解析资源值并转换为可读格式，假设 value_str 仅为数字（已去除单位）。

    :param value_str: 仅包含数字的字符串（已去除单位）
    :param resource_type: 'cpu' 或 'memory'
    :param unit: 原始单位，用于决定如何处理该数值（如 'm', 'n', 'Ki', 'Mi', 'Gi' 等）
    :return: 转换后的可读值和目标单位
    """
    print(111)
    # 直接转换输入字符串为浮点数（不再提取单位）
    try:
        value = float(value_str.strip())
    except ValueError:
        raise ValueError("无法解析输入字符串为数字")

    print(222)
    if resource_type == 'cpu':
        # CPU利用率的转换，根据unit参数判断原始单位
        if unit == 'n':  # 纳秒
            return value / 1e9, '%'
        elif unit == 'm':  # 毫核
            return value / 1000, 'cores'
        else:
            # 默认认为是核心数（单位是 core 或直接以整数表示）
            return value, 'cores'

    elif resource_type == 'memory':
        # 内存相关的单位转换
        units_dict = {'Ki': 1, 'Mi': 1024, 'Gi': 1024 * 1024}
        if unit in units_dict:
            bytes_val = value * 1024 * units_dict[unit]  # Ki/Mi/Gi -> 字节
        elif unit == 'B' or unit == '':  # 字节或无单位
            bytes_val = value
        else:
            raise ValueError(f"不支持的内存单位: {unit}")

        print(444)
        # 将字节转换为MB或GB
        if bytes_val < 1024 * 1024 * 1024:
            return bytes_val / (1024 * 1024), 'MB'
        else:
            return bytes_val / (1024 * 1024 * 1024), 'GB'

    else:
        raise ValueError("未知的资源类型，应为 'cpu' 或 'memory'")
    
if __name__ == "__main__":
    numeric_part = re.sub(r'\D', '', '80739445n')
    numeric_part2 = re.sub(r'\D', '', '4792336Ki')
    print(f'CPU:{parse_resource_value(numeric_part, "cpu", unit="n")}')  # CPU利用率
    print(f'内存:{parse_resource_value(numeric_part2, "memory", unit="Ki")}')  # 内存利用率