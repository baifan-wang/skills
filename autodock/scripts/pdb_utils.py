#!/usr/bin/env python3
"""
PDB处理共享工具模块

包含 extract_residues.py 和 process_pdb.py 共享的功能：
- PDB文件格式常量
- 氨基酸映射
- 水残基名和金属元素定义
- PDB行解析函数
- 日志配置
- 文件验证
"""

import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import re
import logging
import os
import subprocess
from typing import Dict, List, Tuple, Optional, Set, Any

# 预编译的正则表达式
RESIDUE_SPEC_PATTERN = re.compile(r'^([A-Z]+)(\d+)([A-Z]?)$')
INSERTION_CODE_PATTERN = re.compile(r'^(\d+)([A-Z])$')
RESIDUE_NUMBER_PATTERN = re.compile(r'^(\d+)')

# PDB记录类型
PDB_RECORD_ATOM = "ATOM"
PDB_RECORD_HETATM = "HETATM"
PDB_RECORD_TER = "TER"

# 默认链ID
DEFAULT_CHAIN = "A"

# 氨基酸三字母代码到单字母代码的映射
AA_3TO1: Dict[str, str] = {
    'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D',
    'CYS': 'C', 'GLN': 'Q', 'GLU': 'E', 'GLY': 'G',
    'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K',
    'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S',
    'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V',
    # 非标准氨基酸
    'ASH': 'D', 'GLH': 'E', 'HID': 'H', 'HIE': 'H', 'HIP': 'H',
    'LYN': 'K', 'CYM': 'C', 'CYX': 'C'
}

# 单字母代码到三字母代码的映射（取第一个常见的）
AA_1TO3: Dict[str, str] = {}
for three, one in AA_3TO1.items():
    if one not in AA_1TO3:
        AA_1TO3[one] = three

# 水残基名
WATER_RESIDUES: Set[str] = {'HOH', 'WAT', 'H2O', 'WAT1', 'HOH1'}

# 常见金属元素符号（来自 PDB 元素符号列）
# 注意：已移除重复项
METAL_ELEMENTS: Set[str] = {
    'ZN', 'CU', 'FE', 'MG', 'CA', 'MN', 'CO', 'NI', 'PT', 'AU',
    'AG', 'HG', 'PB', 'LI', 'NA', 'K', 'RB', 'CS', 'FR', 'BE',
    'SR', 'BA', 'RA', 'AL', 'GA', 'IN', 'TL', 'SN', 'BI', 'PO',
    'CR', 'MO', 'W', 'V', 'CD', 'YB', 'LU', 'EU', 'GD',
    'TB', 'DY', 'HO', 'ER', 'TM', 'HF', 'TA', 'RE',
    'OS', 'IR', 'RH', 'PD', 'RU', 'TC'
}

# 加氢工具常量
TOOL_AUTO = "auto"
TOOL_PDB2PQR = "pdb2pqr"
TOOL_OPENBABEL = "openbabel"

def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    设置日志配置

    Args:
        verbose: 是否启用详细日志

    Returns:
        配置好的日志记录器
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def validate_file_exists(file_path: str) -> None:
    """
    验证文件是否存在，如果不存在则引发 FileNotFoundError

    Args:
        file_path: 文件路径

    Raises:
        FileNotFoundError: 文件不存在时
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

def parse_pdb_line(line: str) -> Dict[str, Any]:
    """
    解析 PDB 行的字段

    Args:
        line: PDB行字符串

    Returns:
        包含解析字段的字典
    """
    return {
        'record': line[0:6].strip(),
        'atom_serial': line[6:11].strip(),
        'atom_name': line[12:16].strip(),
        'alt_loc': line[16:17].strip(),
        'res_name': line[17:20].strip(),
        'chain_id': line[21:22].strip(),
        'res_seq': line[22:26].strip(),  # 残基序列号（数字部分）
        'i_code': line[26:27].strip(),   # 插入码（可能为空）
        'x': line[30:38].strip(),
        'y': line[38:46].strip(),
        'z': line[46:54].strip(),
        'occupancy': line[54:60].strip(),
        'temp_factor': line[60:66].strip(),
        'segment': line[72:76].strip(),
        'element': line[76:78].strip(),
        'charge': line[78:80].strip(),
        'full_line': line.rstrip('\n')
    }

def is_metal_from_element(element: str) -> bool:
    """
    根据元素符号检查是否为金属

    Args:
        element: 元素符号（如 'ZN', 'CU'）

    Returns:
        是否为金属
    """
    return element in METAL_ELEMENTS

def is_metal_from_line(line: str) -> bool:
    """
    检查PDB行是否为金属原子（基于元素符号列）

    Args:
        line: PDB行字符串

    Returns:
        是否为金属
    """
    if len(line) >= 78:
        element = line[76:78].strip()
        return element != '' and element in METAL_ELEMENTS
    return False

def extract_residue_number(res_seq_str: str) -> str:
    """
    从残基序列号字符串中提取数字部分（去除插入码）

    Args:
        res_seq_str: PDB中的残基序列号字符串（可能包含插入码，如 '96A'）

    Returns:
        数字部分（字符串）
    """
    match = RESIDUE_NUMBER_PATTERN.match(res_seq_str.strip())
    return match.group(1) if match else res_seq_str.strip()

def parse_residue_spec(spec: str) -> Tuple[Optional[str], Optional[str]]:
    """
    解析残基规格字符串

    Args:
        spec: 残基规格字符串，如 'ASN96', 'N96', '96', '96A', 'ASN96A', 'ACJ'

    Returns:
        (res_name, res_seq) 元组，其中可能为None
        res_name: 残基名称（三字母代码）或None
        res_seq: 残基序列号（字符串，包含插入码）或None
    """
    spec = spec.strip().upper()

    # 1. 纯数字：仅序列号（无插入码）
    if spec.isdigit():
        return (None, spec)

    # 2. 纯字母（长度1-4）：可能是单字母氨基酸缩写或小分子残基名
    if spec.isalpha():
        if len(spec) == 1 and spec in AA_1TO3:
            # 单字母氨基酸缩写
            return (AA_1TO3[spec], None)
        else:
            # 小分子残基名（如 ACJ）或三字母氨基酸代码
            return (spec, None)

    # 3. 字母+数字+可选插入码：如 ASN96, N96, ASN96A
    match = RESIDUE_SPEC_PATTERN.match(spec)
    if match:
        letters = match.group(1)
        numbers = match.group(2)
        insert_code = match.group(3) if match.group(3) else ''

        # 如果字母部分长度为1，可能是单字母氨基酸缩写
        if len(letters) == 1 and letters in AA_1TO3:
            res_name = AA_1TO3[letters]
        else:
            # 否则视为三字母代码
            res_name = letters

        res_seq = numbers + insert_code
        return (res_name, res_seq)

    # 4. 数字+字母（插入码）：如 96A
    match = INSERTION_CODE_PATTERN.match(spec)
    if match:
        numbers = match.group(1)
        insert_code = match.group(2)
        res_seq = numbers + insert_code
        return (None, res_seq)

    # 5. 无法解析
    return (spec, None)

def run_external_tool(cmd: List[str], tool_name: str, logger: logging.Logger) -> None:
    """
    运行外部工具的通用函数

    Args:
        cmd: 命令列表
        tool_name: 工具名称（用于日志）
        logger: 日志记录器

    Raises:
        RuntimeError: 工具执行失败时
        FileNotFoundError: 工具未找到时
    """
    logger.info(f"运行 {tool_name}: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            logger.debug(f"{tool_name} 输出: {result.stdout}")
        if result.stderr:
            logger.warning(f"{tool_name} 错误: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"{tool_name} 失败: {e.stderr}")
        raise RuntimeError(f"{tool_name} 执行失败: {e.returncode}")
    except FileNotFoundError:
        logger.error(f"{tool_name} 未找到，请确保已安装 {tool_name} 并在 PATH 中")
        raise

# subprocess 已在模块顶部导入
