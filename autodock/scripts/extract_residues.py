#!/usr/bin/env python3
"""
从PDB文件中提取用户指定的残基或小分子。

输入格式：
1. 链ID + 残基规格（空格分隔）
   - 链ID：单个字母（A-Z）
   - 残基规格：可以是以下形式之一：
        ASN96    # 3字母代码 + 序列号
        N96      # 单字母氨基酸缩写 + 序列号
        96       # 仅序列号
        ACJ      # 仅小分子残基名（3字母）

示例：
   A ASN96 ALA35 B GLU97    # 提取A链的ASN96和ALA35，B链的GLU97
   A N96 A35 B E97          # 单字母缩写形式
   A 96 35 B 97             # 仅序列号形式
   A ACJ                    # 提取A链的小分子ACJ

注意：
- 如果PDB文件中链ID列为空，则默认所有链为'A'
- 如果用户输入中未指定链ID，则默认所有残基属于'A'链
- 输出文件默认为 center.pdb
"""

import argparse
import sys
import os
from typing import Dict, List, Tuple, Optional, Set
import logging

# 导入共享工具模块
try:
    import pdb_utils
except ImportError:
    # 如果 pdb_utils 不在路径中，添加当前目录
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pdb_utils

# 使用共享模块中的常量
AA_1TO3 = pdb_utils.AA_1TO3
DEFAULT_CHAIN = pdb_utils.DEFAULT_CHAIN

# 设置日志
logger = pdb_utils.setup_logging()

def parse_user_input(input_str: str) -> Dict[str, List[Tuple[Optional[str], Optional[str]]]]:
    """
    解析用户输入字符串，构建链到残基规格列表的映射。

    参数:
        input_str: 用户输入字符串，如 "A ASN96 ALA35 B GLU97"

    返回:
        dict: {chain_id: list of (res_name, res_seq)}
    """
    if not input_str:
        return {}

    tokens = input_str.strip().split()
    if not tokens:
        return {}

    # 检查第一个token是否是链ID（单个字母，且不是数字）
    first_token = tokens[0]
    if len(first_token) == 1 and first_token.isalpha() and not first_token.isdigit():
        # 第一个token是链ID
        current_chain = first_token.upper()
        start_idx = 1
    else:
        # 第一个token不是链ID，使用默认链
        current_chain = DEFAULT_CHAIN
        start_idx = 0

    chain_map: Dict[str, List[Tuple[Optional[str], Optional[str]]]] = {}

    i = start_idx
    while i < len(tokens):
        token = tokens[i]

        # 检查token是否是链ID（单个字母，且不是数字）
        if len(token) == 1 and token.isalpha() and not token.isdigit():
            current_chain = token.upper()
            i += 1
            continue

        # 否则是残基规格
        res_name, res_seq = pdb_utils.parse_residue_spec(token)

        # 添加到链映射
        if current_chain not in chain_map:
            chain_map[current_chain] = []
        chain_map[current_chain].append((res_name, res_seq))

        i += 1

    logger.debug(f"解析后的链映射: {chain_map}")
    return chain_map

def build_spec_lookup(chain_map: Dict[str, List[Tuple[Optional[str], Optional[str]]]]) -> Dict[str, Set[Tuple[Optional[str], Optional[str]]]]:
    """
    将链映射转换为查找友好的数据结构。

    参数:
        chain_map: 链到残基规格列表的映射

    返回:
        dict: {chain_id: set of (res_name, res_seq)} 用于O(1)查找
    """
    return {chain: set(specs) for chain, specs in chain_map.items()}

def extract_residues(input_pdb: str, output_pdb: str, chain_map: Dict[str, List[Tuple[Optional[str], Optional[str]]]]) -> None:
    """
    从PDB文件中提取指定的残基。

    参数:
        input_pdb: 输入PDB文件路径
        output_pdb: 输出PDB文件路径
        chain_map: 链到残基规格列表的映射
    """
    if not chain_map:
        logger.warning("没有指定要提取的残基")
        return

    # 构建高效的查找结构
    spec_lookup = build_spec_lookup(chain_map)

    total_atoms = 0
    extracted_atoms = 0

    try:
        with open(input_pdb, 'r') as f_in, open(output_pdb, 'w') as f_out:
            for line in f_in:
                if line.startswith((pdb_utils.PDB_RECORD_ATOM, pdb_utils.PDB_RECORD_HETATM)):
                    total_atoms += 1

                    # 只提取需要的字段
                    res_name = line[17:20].strip()
                    chain_id = line[21:22].strip().upper()
                    res_seq_num = line[22:26].strip()  # 残基序列号（数字部分）
                    i_code = line[26:27].strip()       # 插入码（可能为空）

                    # 如果链ID为空，默认为'A'
                    if not chain_id:
                        chain_id = DEFAULT_CHAIN

                    # 完整的序列号标识（数字部分 + 插入码）
                    res_seq_full = res_seq_num
                    if i_code:
                        res_seq_full = res_seq_num + i_code

                    # 检查是否匹配任何规格
                    if chain_id in spec_lookup:
                        # 为当前原子构建要匹配的规格
                        # 可能的匹配规格：(None, res_seq_full), (res_name, None), (res_name, res_seq_full)
                        # 但我们需要检查规格集合中的所有可能匹配
                        for spec_res_name, spec_res_seq in spec_lookup[chain_id]:
                            match = True

                            # 检查残基名称
                            if spec_res_name is not None and spec_res_name != res_name:
                                match = False

                            # 检查序列号
                            if match and spec_res_seq is not None:
                                # 判断规格中的序列号是否包含插入码（以字母结尾）
                                if spec_res_seq[-1].isalpha():
                                    # 包含插入码，进行完全匹配
                                    if spec_res_seq != res_seq_full:
                                        match = False
                                else:
                                    # 不包含插入码，只比较数字部分
                                    if spec_res_seq != res_seq_num:
                                        match = False

                            # 如果两者都为None（不应该发生），则不匹配
                            if spec_res_name is None and spec_res_seq is None:
                                match = False

                            if match:
                                f_out.write(line)
                                extracted_atoms += 1
                                break  # 匹配一个规格即可
                    # 注意：如果链ID不在chain_map中，则跳过该原子

    except FileNotFoundError:
        logger.error(f"输入文件不存在: {input_pdb}")
        sys.exit(1)
    except IOError as e:
        logger.error(f"文件读写错误: {e}")
        sys.exit(1)

    logger.info(f"处理完成。总原子数: {total_atoms}, 提取原子数: {extracted_atoms}")
    logger.info(f"输出文件: {output_pdb}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description='从PDB文件中提取用户指定的残基或小分子',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.pdb "A ASN96 ALA35 B GLU97" -o center.pdb
  %(prog)s input.pdb "A N96 A35 B E97" -o residues.pdb
  %(prog)s input.pdb "A 96 35 B 97" -o selection.pdb
  %(prog)s input.pdb "A ACJ" -o ligand.pdb
        """
    )
    parser.add_argument('input', help='输入PDB文件')
    parser.add_argument('residues', help='要提取的残基规格字符串（用引号括起来）')
    parser.add_argument('-o', '--output', default='center.pdb',
                       help='输出PDB文件（默认: center.pdb）')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # 检查输入文件是否存在
    try:
        pdb_utils.validate_file_exists(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 解析用户输入
    logger.info(f"解析残基规格: {args.residues}")
    chain_map = parse_user_input(args.residues)

    if not chain_map:
        logger.error("未解析到有效的残基规格，请检查输入格式")
        sys.exit(1)

    logger.info(f"提取链映射: {chain_map}")

    # 提取残基
    extract_residues(args.input, args.output, chain_map)

if __name__ == '__main__':
    main()