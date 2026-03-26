#!/usr/bin/env python3
"""
PDB文件处理脚本
功能：
1. 删除水分子（残基名 HOH, WAT, H2O 等）
2. 删除小分子，但可以指定保留的残基名
3. 删除金属原子（基于元素符号）
4. 添加氢原子（使用 pdb2pqr 或 openbabel）

使用示例：
1. 基本用法：删除水、小分子、金属，自动加氢
   python process_pdb.py input.pdb output.pdb

2. 保留特定小分子（如 FAD、NAD），删除其他小分子
   python process_pdb.py input.pdb output.pdb --keep FAD NAD

3. 不加氢
   python process_pdb.py input.pdb output.pdb --no-hydrogens

4. 指定加氢工具（pdb2pqr 或 openbabel）
   python process_pdb.py input.pdb output.pdb --hydrogen-tool pdb2pqr

5. 保留金属原子
   python process_pdb.py input.pdb output.pdb --keep-metals

6. 详细输出
   python process_pdb.py input.pdb output.pdb --verbose

注意：
- 需要安装 pdb2pqr 和/或 openbabel（obabel）并添加到 PATH 环境变量。
- 自动选择加氢工具：如果保留了小分子（非水、非金属），则使用 openbabel；否则使用 pdb2pqr。
- 金属检测基于 PDB 文件中的元素符号列（77-78列）。常见金属元素包括 Zn、Cu、Fe、Mg、Ca 等。
- 水残基名包括 HOH、WAT、H2O 等。
"""

import argparse
import sys
import os
import tempfile
import shutil
from typing import Set, List, Optional
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
WATER_RESIDUES = pdb_utils.WATER_RESIDUES
TOOL_AUTO = pdb_utils.TOOL_AUTO
TOOL_PDB2PQR = pdb_utils.TOOL_PDB2PQR
TOOL_OPENBABEL = pdb_utils.TOOL_OPENBABEL

# 设置日志
logger = pdb_utils.setup_logging()

def is_water(res_name: str) -> bool:
    """检查是否为水分子"""
    return res_name in WATER_RESIDUES

def filter_pdb(input_file: str, output_file: str, keep_residues: Optional[Set[str]] = None,
               remove_metals: bool = True) -> Set[str]:
    """
    过滤 PDB 文件，删除水、小分子和金属

    参数:
        input_file: 输入文件路径
        output_file: 输出文件路径
        keep_residues: 要保留的小分子残基名集合
        remove_metals: 是否删除金属原子

    返回:
        保留的 HETATM 残基名集合（非水、非金属）
    """
    if keep_residues is None:
        keep_residues = set()

    kept_hetatms: Set[str] = set()  # 保留的 HETATM 残基名（非水、非金属）

    try:
        with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
            for line in f_in:
                if line.startswith((pdb_utils.PDB_RECORD_ATOM, pdb_utils.PDB_RECORD_HETATM)):
                    # 检查是否为水（最常见，先检查）
                    res_name = line[17:20].strip()
                    if is_water(res_name):
                        continue

                    # 检查是否为金属（如果需要）
                    if remove_metals and pdb_utils.is_metal_from_line(line):
                        continue

                    # 如果是 HETATM，检查是否在保留列表中
                    if line.startswith(pdb_utils.PDB_RECORD_HETATM):
                        if res_name not in keep_residues:
                            continue
                        else:
                            # 记录保留的小分子
                            kept_hetatms.add(res_name)

                    # 保留该行
                    f_out.write(line)
                else:
                    # 保留其他所有行（HEADER、TITLE、TER 等）
                    f_out.write(line)
    except IOError as e:
        logger.error(f"文件读写错误: {e}")
        raise

    logger.info(f"过滤完成。保留的小分子残基: {kept_hetatms}")
    return kept_hetatms

def add_hydrogens_with_pdb2pqr(input_pdb: str, output_pdb: str, ff: str = 'AMBER', ph: float = 7.0) -> None:
    """使用 pdb2pqr 添加氢原子"""
    # pdb2pqr 命令：pdb2pqr --ff=AMBER --with-ph=7.0 input.pdb output.pdb
    cmd = ['pdb2pqr', f'--ff={ff}', f'--with-ph={ph}', '--keep-chain', input_pdb, output_pdb]
    pdb_utils.run_external_tool(cmd, TOOL_PDB2PQR, logger)

def add_hydrogens_with_openbabel(input_pdb: str, output_pdb: str) -> None:
    """使用 openbabel 添加氢原子"""
    # obabel input.pdb -O output.pdb -h
    cmd = ['obabel', input_pdb, '-O', output_pdb, '-h']
    pdb_utils.run_external_tool(cmd, TOOL_OPENBABEL, logger)

def select_hydrogen_tool(tool: str, kept_hetatms: Set[str], force_tool: bool = False) -> str:
    """
    选择加氢工具

    参数:
        tool: 用户指定的工具（'auto', 'pdb2pqr', 'openbabel'）
        kept_hetatms: 保留的小分子残基集合
        force_tool: 是否强制使用用户指定的工具

    返回:
        选择的工具名称
    """
    if tool != TOOL_AUTO and force_tool:
        logger.info(f"强制使用工具: {tool}")
        return tool

    if tool == TOOL_AUTO:
        # 如果保留了非水、非金属的小分子，则使用 openbabel
        if kept_hetatms:
            tool = TOOL_OPENBABEL
            logger.info("检测到保留的小分子，自动选择 openbabel 加氢")
        else:
            tool = TOOL_PDB2PQR
            logger.info("未检测到小分子，自动选择 pdb2pqr 加氢")

    return tool

def main() -> None:
    parser = argparse.ArgumentParser(description='处理 PDB 文件：删除水、小分子、金属，添加氢原子')
    parser.add_argument('input', help='输入 PDB 文件')
    parser.add_argument('output', help='输出 PDB 文件')
    parser.add_argument('--keep', nargs='+', default=[], help='要保留的小分子残基名（例如 FAD, NAD）')
    parser.add_argument('--no-hydrogens', action='store_true', help='不添加氢原子')
    parser.add_argument('--hydrogen-tool', choices=[TOOL_AUTO, TOOL_PDB2PQR, TOOL_OPENBABEL],
                       default=TOOL_AUTO, help='加氢工具（auto：自动选择，pdb2pqr：仅蛋白质，openbabel：有小分子时）')
    parser.add_argument('--force-tool', action='store_true',
                       help='强制使用指定的工具，即使 auto 检测建议其他工具')
    parser.add_argument('--keep-metals', action='store_true', help='保留金属原子')
    parser.add_argument('--ff', default='AMBER', help='pdb2pqr 力场（默认 AMBER）')
    parser.add_argument('--ph', type=float, default=7.0, help='pdb2pqr pH 值（默认 7.0）')
    parser.add_argument('--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # 检查输入文件是否存在
    try:
        pdb_utils.validate_file_exists(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 保留的残基名集合
    keep_residues = set(args.keep)

    # 临时文件
    with tempfile.TemporaryDirectory() as tmpdir:
        filtered_pdb = os.path.join(tmpdir, 'filtered.pdb')

        # 步骤1：过滤 PDB
        logger.info(f"过滤 PDB 文件: {args.input}")
        try:
            kept_hetatms = filter_pdb(
                args.input, filtered_pdb,
                keep_residues=keep_residues,
                remove_metals=not args.keep_metals
            )
        except Exception as e:
            logger.error(f"过滤失败: {e}")
            sys.exit(1)

        # 检查过滤后的文件是否为空
        if os.path.getsize(filtered_pdb) == 0:
            logger.error("过滤后文件为空，请检查过滤条件")
            sys.exit(1)

        # 步骤2：添加氢原子（如果需要）
        if not args.no_hydrogens:
            # 选择加氢工具
            tool = select_hydrogen_tool(
                args.hydrogen_tool,
                kept_hetatms,
                args.force_tool
            )

            intermediate_pdb = os.path.join(tmpdir, 'with_h.pdb')

            try:
                if tool == TOOL_PDB2PQR:
                    add_hydrogens_with_pdb2pqr(filtered_pdb, intermediate_pdb, ff=args.ff, ph=args.ph)
                elif tool == TOOL_OPENBABEL:
                    add_hydrogens_with_openbabel(filtered_pdb, intermediate_pdb)
                else:
                    logger.error(f"未知工具: {tool}")
                    sys.exit(1)
            except Exception as e:
                logger.error(f"加氢失败: {e}")
                logger.info("将不加氢的输出文件作为最终结果")
                intermediate_pdb = filtered_pdb

            final_temp = intermediate_pdb
        else:
            final_temp = filtered_pdb

        # 复制到最终输出位置
        try:
            shutil.copy2(final_temp, args.output)
        except IOError as e:
            logger.error(f"复制输出文件失败: {e}")
            sys.exit(1)

        logger.info(f"处理完成，输出文件: {args.output}")

if __name__ == '__main__':
    main()