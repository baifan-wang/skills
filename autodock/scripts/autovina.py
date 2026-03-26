import os
import subprocess
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import re
from typing import List, Tuple, Optional, Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
import numpy as np
import warnings
import logging

from pdb_utils import (
    parse_pdb_line,
    PDB_RECORD_ATOM,
    PDB_RECORD_HETATM,
    setup_logging,
    run_external_tool
)

# ============================ 用户配置 ============================
# 请根据您的实际安装路径修改以下变量
VINA_EXE_PATH = "C:\\apps\\vina.exe"  # 请修改为实际的vina路径
OPENBABEL_PATH = "C:\\OpenBabel-3.1.1\\obabel.exe"  # 请修改为实际的openbabel路径
MGL_PATH = "C:\\Program Files (x86)\\MGLTools-1.5.7\\"
PREPARE_LIGAND_SCRIPT = MGL_PATH + "Lib\\site-packages\\AutoDockTools\\Utilities24\\prepare_ligand4.py"
PREPARE_RECEPTOR_SCRIPT = MGL_PATH + "Lib\\site-packages\\AutoDockTools\\Utilities24\\prepare_receptor4.py"
ADT4_PYTHON = MGL_PATH + "python.exe"
# ============================

warnings.filterwarnings("ignore", category=DeprecationWarning)

logger = logging.getLogger(__name__)

def extract_center_from_pdb(pdb_file: Path) -> Tuple[float, float, float]:
    """从PDB文件中提取原子坐标并计算中心点"""
    coords = []
    try:
        with open(pdb_file, 'r') as f:
            for line in f:
                if line.startswith((PDB_RECORD_ATOM, PDB_RECORD_HETATM)):
                    parsed = parse_pdb_line(line)
                    if parsed.get('x') and parsed.get('y') and parsed.get('z'):
                        try:
                            x = float(parsed['x'])
                            y = float(parsed['y'])
                            z = float(parsed['z'])
                            coords.append([x, y, z])
                        except ValueError:
                            continue

        if coords:
            center = np.mean(coords, axis=0)
            return center[0], center[1], center[2]
        else:
            return None
    except Exception as e:
        logger.error(f"读取PDB文件时出错: {e}")
        return None


def update_config_center(conf_file: Path, center_x: float, center_y: float, center_z: float) -> None:
    """更新配置文件中的中心坐标"""
    try:
        with open(conf_file, 'r') as f:
            lines = f.readlines()
        
        with open(conf_file, 'w') as f:
            for line in lines:
                if line.strip().startswith('center_x'):
                    f.write(f'center_x = {center_x:.3f}\n')
                elif line.strip().startswith('center_y'):
                    f.write(f'center_y = {center_y:.3f}\n')
                elif line.strip().startswith('center_z'):
                    f.write(f'center_z = {center_z:.3f}\n')
                else:
                    f.write(line)
        print(f"已更新对接中心坐标: ({center_x:.3f}, {center_y:.3f}, {center_z:.3f})")
    except Exception as e:
        print(f"更新配置文件时出错: {e}")


class MolFormatConverter:
    """分子格式转换类"""
    
    def __init__(self, ligands_dir: str = "ligands"):
        """
        初始化分子格式转换器
        
        Args:
            ligands_dir: 配体文件目录
        """
        self.ligands_dir = Path(ligands_dir)
        self.ligands_dir.mkdir(exist_ok=True)
        
    def rename_mol2(self, mol2_file: Path) -> None:
        """
        重命名mol2文件中的原子（示例函数，需要根据实际情况修改）
        
        Args:
            mol2_file: mol2文件路径
        """
        try:
            with open(mol2_file, 'r') as f:
                lines = f.readlines()
            
            # 这里是一个简单的重命名示例，实际需要根据mol2格式进行调整
            # 例如：将原子名从数字改为元素符号
            i = 0
            n = 1
            f = open(mol2_file,'w')
            rename = False
            for line in lines:
                if line.startswith('@<TRIPOS>ATOM'):
                    rename = True
                    f.write(line)
                elif line.startswith('@<TRIPOS>UNITY_ATOM_ATTR') or line.startswith('@<TRIPOS>BOND'):
                    rename = False
                    f.write(line)
                elif rename == False:
                    f.write(line)
                elif rename == True:
                    i+=1
                    if line.split()[5] == 'Cl':
                        s=line[:9]+'l'+str(n)+line[13:]
                        n+=1
                    elif line.split()[5] == 'Br':
                        s=line[:9]+'r'+str(n)+line[13:]
                        n+=1
                    else:
                        s=line[:9]+str(i)+line[10:]
                        i+=1
                    f.write(s)
            f.close()

                
        except Exception as e:
            print(f"重命名mol2文件时出错: {e}")
    
    def process_smi_file(self, smi_file: Path) -> List[Path]:
        """
        处理.smi文件
        
        Args:
            smi_file: .smi文件路径
            
        Returns:
            生成的sdf文件路径列表
        """
        generated_files = []
        
        try:
            with open(smi_file, 'r') as f:
                lines = f.readlines()
            
            base_name = smi_file.stem
            
            for i, line in enumerate(lines):
                parts = line.strip().split()
                if len(parts) >= 2:
                    smiles, name = parts[0], parts[1]
                    
                    # 创建分子对象
                    mol = Chem.MolFromSmiles(smiles)
                    if mol is not None:
                        # 加氢并生成3D结构
                        mol = Chem.AddHs(mol)
                        AllChem.EmbedMolecule(mol, randomSeed=42)
                        AllChem.MMFFOptimizeMolecule(mol)
                        
                        # 保存为sdf文件
                        sdf_path = self.ligands_dir / f"{name}_{i}.sdf"
                        writer = Chem.SDWriter(str(sdf_path))
                        writer.write(mol)
                        writer.close()
                        
                        # 绘制2D结构
                        img_path = self.ligands_dir / f"{name}_{i}.png"
                        img = Draw.MolToImage(mol, size=(300, 300))
                        img.save(str(img_path))
                        
                        generated_files.append(sdf_path)
                        print(f"已处理SMILES: {smiles}, 保存为: {sdf_path}")
        
        except Exception as e:
            print(f"处理smi文件时出错 {smi_file}: {e}")
        
        return generated_files
    
    def process_sdf_file(self, sdf_file: Path) -> List[Path]:
        """
        处理.sdf文件
        
        Args:
            sdf_file: .sdf文件路径
            
        Returns:
            生成的sdf文件路径列表
        """
        generated_files = []
        
        try:
            # 首先检查文件是否存在且不为空
            if not sdf_file.exists():
                print(f"错误: SDF文件不存在: {sdf_file}")
                return generated_files
            
            file_size = sdf_file.stat().st_size
            if file_size == 0:
                print(f"错误: SDF文件为空: {sdf_file}")
                return generated_files
            
            print(f"处理SDF文件: {sdf_file} (大小: {file_size} 字节)")
            
            # 尝试读取文件
            supplier = Chem.SDMolSupplier(str(sdf_file))
            
            # 检查supplier是否有效
            if supplier is None:
                print(f"错误: 无法创建SDMolSupplier for {sdf_file}")
                return generated_files
            
            base_name = sdf_file.stem
            mol_count = 0
            
            # 创建一个集合来跟踪已使用的分子名，避免重复
            used_names = set()
            
            for i, mol in enumerate(supplier):
                if mol is not None:
                    mol_count += 1
                    
                    # 尝试获取分子名
                    mol_name = None
                    if mol.HasProp("_Name"):
                        mol_name = mol.GetProp("_Name").strip()
                    
                    # 如果分子名无效或为空，使用基于文件名的命名
                    if not mol_name or mol_name == "" or mol_name.isspace():
                        # 使用文件名 + 序号
                        mol_name = f"{base_name}_{i+1}"
                        print(f"警告: 分子 {i} 没有名称，使用: {mol_name}")
                    else:
                        print(f"分子 {i} 名称: {mol_name}")
                    
                    # 清理分子名中的非法字符
                    mol_name = re.sub(r'[<>:"/\\|?*\s]', '_', mol_name)
                    mol_name = mol_name.strip('_')
                    
                    # 确保名称唯一
                    original_name = mol_name
                    counter = 1
                    while mol_name in used_names:
                        mol_name = f"{original_name}_{counter}"
                        counter += 1
                    used_names.add(mol_name)
                    
                    # 加氢并生成3D结构（如果需要）
                    try:
                        mol = Chem.AddHs(mol)
                        # 检查是否已有3D坐标
                        has_3d = False
                        if mol.GetNumConformers() > 0:
                            conf = mol.GetConformer()
                            if conf.Is3D():
                                has_3d = True
                        
                        if not has_3d:
                            print(f"为分子 {mol_name} 生成3D结构...")
                            AllChem.EmbedMolecule(mol, randomSeed=42)
                            AllChem.MMFFOptimizeMolecule(mol)
                        else:
                            print(f"分子 {mol_name} 已有3D结构")
                    except Exception as e:
                        print(f"警告: 无法为分子 {mol_name} 生成3D结构: {e}")
                    
                    # 保存为单独的sdf文件
                    sdf_path = self.ligands_dir / f"{mol_name}.sdf"
                    writer = Chem.SDWriter(str(sdf_path))
                    writer.write(mol)
                    writer.close()
                    
                    # 绘制2D结构
                    try:
                        img_path = self.ligands_dir / f"{mol_name}.png"
                        img = Draw.MolToImage(mol, size=(300, 300))
                        img.save(str(img_path))
                        print(f"已生成2D结构图: {img_path}")
                    except Exception as e:
                        print(f"警告: 无法为分子 {mol_name} 绘制2D结构: {e}")
                    
                    generated_files.append(sdf_path)
                    print(f"已处理分子: {mol_name}, 保存为: {sdf_path}")
                else:
                    print(f"警告: SDF文件中第 {i+1} 个分子无法读取")
            
            if mol_count == 0:
                print(f"警告: SDF文件 {sdf_file} 中没有可读取的分子")
            else:
                print(f"成功处理 {mol_count} 个分子")
            
        except Exception as e:
            print(f"处理sdf文件时出错 {sdf_file}: {e}")
            import traceback
            traceback.print_exc()
        
        return generated_files

    
    def process_mol_file(self, mol_file: Path) -> List[Path]:
        """
        处理.mol文件
        
        Args:
            mol_file: .mol文件路径
            
        Returns:
            生成的sdf文件路径列表
        """
        generated_files = []
        
        try:
            mol = Chem.MolFromMolFile(str(mol_file),strictParsing=False)
            if mol is not None:
                # 加氢并生成3D结构（如果需要）
                mol = Chem.AddHs(mol)
                AllChem.EmbedMolecule(mol, randomSeed=42)
                AllChem.MMFFOptimizeMolecule(mol)
                
                # 保存为sdf文件
                sdf_path = self.ligands_dir / f"{mol_file.stem}.sdf"
                writer = Chem.SDWriter(str(sdf_path))
                writer.write(mol)
                writer.close()
                
                # 绘制2D结构
                img_path = self.ligands_dir / f"{mol_file.stem}.png"
                img = Draw.MolToImage(mol, size=(300, 300))
                img.save(str(img_path))
                
                generated_files.append(sdf_path)
                print(f"已处理mol文件: {mol_file}, 保存为: {sdf_path}")
        
        except Exception as e:
            print(f"处理mol文件时出错 {mol_file}: {e}")
        
        return generated_files
    
    def process_cdx_file(self, cdx_file: Path) -> List[Path]:
        """
        处理.cdx文件
        
        Args:
            cdx_file: .cdx文件路径
            
        Returns:
            生成的sdf文件路径列表
        """
        generated_files = []
        
        try:
            # 使用openbabel转换cdx到sdf
            sdf_path = self.ligands_dir / f"{cdx_file.stem}.sdf"
            
            # 构建openbabel命令（使用绝对路径）
            cmd = [
                OPENBABEL_PATH,
                "-icdx",  # 明确指定输入格式
                str(cdx_file.absolute()),
                "-osdf",  # 明确指定输出格式
                "-O", str(sdf_path.absolute())
            ]
            
            print(f"运行OpenBabel命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True)
            
            print(f"OpenBabel输出: {result.stdout}")
            if result.stderr:
                print(f"OpenBabel警告: {result.stderr}")
            
            # 检查文件是否成功生成
            if not sdf_path.exists() or sdf_path.stat().st_size == 0:
                print(f"警告: OpenBabel未成功生成SDF文件: {sdf_path}")
                return generated_files
            
            print(f"已转换cdx文件: {cdx_file} -> {sdf_path}")
            
            # 然后传递给process_sdf_file处理
            generated_files = self.process_sdf_file(sdf_path)
            
        except subprocess.CalledProcessError as e:
            print(f"处理cdx文件时出错 {cdx_file}:")
            print(f"命令: {e.cmd}")
            print(f"返回码: {e.returncode}")
            print(f"标准输出: {e.stdout}")
            print(f"错误输出: {e.stderr}")
            
            # 尝试其他方法：如果OpenBabel失败，尝试使用ChemDraw或直接处理
            print("尝试备用方法处理CDX文件...")
            logger.warning("备用CDX处理方法未实现，跳过该文件")
            generated_files = []
            
        except Exception as e:
            print(f"处理cdx文件时出错 {cdx_file}: {e}")
            import traceback
            traceback.print_exc()
        
        return generated_files
    
    def convert_sdf_to_mol2(self, sdf_file: Path) -> Optional[Path]:
        """
        将sdf文件转换为mol2格式
        
        Args:
            sdf_file: sdf文件路径
            
        Returns:
            生成的mol2文件路径
        """
        try:
            mol2_path = self.ligands_dir / f"{sdf_file.stem}.mol2"
            cmd = [OPENBABEL_PATH, str(sdf_file), "-O", str(mol2_path)]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 重命名mol2文件中的原子
            self.rename_mol2(mol2_path)
            
            print(f"已转换sdf文件: {sdf_file} -> {mol2_path}")
            return mol2_path
            
        except Exception as e:
            print(f"转换sdf到mol2时出错 {sdf_file}: {e}")
            return None
    
    def prepare_ligand(self, ligand_file: Path) -> Optional[Path]:
        """
        使用prepare_ligand4.py准备配体
        """
        try:
            pdbqt_path = self.ligands_dir / f"{ligand_file.stem}.pdbqt"
            
            # 获取绝对路径
            ligand_abs = ligand_file.absolute()
            pdbqt_abs = pdbqt_path.absolute()
            
            # 获取文件所在目录作为工作目录
            working_dir = ligand_abs.parent
            
            cmd = [
                ADT4_PYTHON,
                PREPARE_LIGAND_SCRIPT,
                '-l', ligand_abs.name,  # 只传递文件名，不包含路径
                '-o', pdbqt_abs.name,   # 只传递文件名
                '-A', 'hydrogens',
                '-U', 'nphs_lps']

            print(f"运行命令 (工作目录: {working_dir}): {' '.join(cmd)}")
            
            # 在文件所在目录中运行命令
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True, 
                shell=True,
                cwd=str(working_dir)  # 关键：设置工作目录
            )
            
            print(f"标准输出: {result.stdout}")
            if result.stderr:
                print(f"错误输出: {result.stderr}")
            
            # 检查文件是否生成
            if pdbqt_path.exists():
                print(f"已准备配体: {ligand_file} -> {pdbqt_path}")
                return pdbqt_path
            else:
                print(f"警告: PDBQT文件未生成: {pdbqt_path}")
                return None
            
        except subprocess.CalledProcessError as e:
            print(f"准备配体时出错 {ligand_file}:")
            print(f"命令: {e.cmd}")
            print(f"返回码: {e.returncode}")
            print(f"标准输出: {e.stdout}")
            print(f"错误输出: {e.stderr}")
            return None
        except Exception as e:
            print(f"准备配体时发生异常 {ligand_file}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def convert_all_ligands(self) -> List[Path]:
        """
        转换所有配体文件为pdbqt格式
        
        Returns:
            所有生成的pdbqt文件路径列表
        """
        pdbqt_files = []
        
        # 支持的扩展名
        supported_extensions = ['.smi', '.mol', '.sdf', '.mol2', '.pdbqt', '.cdx', '.pdb']
        
        # 收集所有配体文件
        all_ligand_files = []
        for ext in supported_extensions:
            all_ligand_files.extend(list(self.ligands_dir.glob(f"*{ext}")))
        
        # 处理每种格式的文件
        for ligand_file in all_ligand_files:
            print(f"\n处理文件: {ligand_file.name}")
            
            if ligand_file.suffix == '.pdbqt':
                # pdbqt文件不需要处理
                pdbqt_files.append(ligand_file)
                print(f"跳过pdbqt文件: {ligand_file}")
                
            elif ligand_file.suffix == '.smi':
                # 处理smi文件
                sdf_files = self.process_smi_file(ligand_file)
                for sdf_file in sdf_files:
                    mol2_file = self.convert_sdf_to_mol2(sdf_file)
                    if mol2_file:
                        pdbqt_file = self.prepare_ligand(mol2_file)
                        if pdbqt_file:
                            pdbqt_files.append(pdbqt_file)
                
            elif ligand_file.suffix == '.mol':
                # 处理mol文件
                sdf_files = self.process_mol_file(ligand_file)
                for sdf_file in sdf_files:
                    mol2_file = self.convert_sdf_to_mol2(sdf_file)
                    if mol2_file:
                        pdbqt_file = self.prepare_ligand(mol2_file)
                        if pdbqt_file:
                            pdbqt_files.append(pdbqt_file)
                
            elif ligand_file.suffix == '.sdf':
                # 处理sdf文件
                sdf_files = self.process_sdf_file(ligand_file)
                for sdf_file in sdf_files:
                    mol2_file = self.convert_sdf_to_mol2(sdf_file)
                    if mol2_file:
                        pdbqt_file = self.prepare_ligand(mol2_file)
                        if pdbqt_file:
                            pdbqt_files.append(pdbqt_file)
                
            elif ligand_file.suffix == '.cdx':
                # 处理cdx文件
                sdf_files = self.process_cdx_file(ligand_file)
                for sdf_file in sdf_files:
                    mol2_file = self.convert_sdf_to_mol2(sdf_file)
                    if mol2_file:
                        pdbqt_file = self.prepare_ligand(mol2_file)
                        if pdbqt_file:
                            pdbqt_files.append(pdbqt_file)
                
            elif ligand_file.suffix in ['.mol2', '.pdb']:
                # 直接使用prepare_ligand处理
                pdbqt_file = self.prepare_ligand(ligand_file)
                if pdbqt_file:
                    pdbqt_files.append(pdbqt_file)
        
        return pdbqt_files
    
    def prepare_receptor(self, receptor_pdb: Path) -> Optional[Path]:
        """
        准备受体蛋白
        
        Args:
            receptor_pdb: 受体pdb文件路径
            
        Returns:
            生成的受体pdbqt文件路径
        """
        try:
            pdbqt_path = receptor_pdb.with_suffix('.pdbqt')
            cmd = [ADT4_PYTHON, PREPARE_RECEPTOR_SCRIPT, "-r", str(receptor_pdb), "-o", str(pdbqt_path)]
            subprocess.run(cmd, check=True, capture_output=True)
            
            print(f"已准备受体: {receptor_pdb} -> {pdbqt_path}")
            return pdbqt_path
            
        except Exception as e:
            print(f"准备受体时出错 {receptor_pdb}: {e}")
            return None


def run_single_docking_task(ligand_pdbqt: Path, receptor_pdbqt: Path, 
                           vina_conf: str, vina_exe: str) -> Optional[Tuple[Path, float]]:
    """
    单个对接任务的包装函数（需要在类外部定义以便在Windows上序列化）
    """
    try:
        # 创建临时处理器实例（或直接运行命令）
        output_name = f"{ligand_pdbqt.stem}_docked.pdbqt"
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        output_path = results_dir / output_name
        
        # 构建vina命令（使用绝对路径）
        cmd = [
            vina_exe,
            '--cpu', '1',
            '--receptor', str(receptor_pdbqt.absolute()),
            '--config', str(Path(vina_conf).absolute()),
            '--ligand', str(ligand_pdbqt.absolute()),
            '--out', str(output_path.absolute())
        ]
        
        # 运行对接
        print(f"开始对接: {ligand_pdbqt.name}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True)
        
        print(f"对接完成: {ligand_pdbqt.name} -> {output_path}")
        
        # 提取能量
        energy = extract_energy_from_pdbqt(output_path)
        
        return output_path, energy
        
    except subprocess.CalledProcessError as e:
        print(f"对接失败 {ligand_pdbqt.name}: {e}")
        print(f"错误输出: {e.stderr}")
        return None
    except Exception as e:
        print(f"对接过程中出错 {ligand_pdbqt.name}: {e}")
        return None

def extract_energy_from_pdbqt(pdbqt_file: Path) -> Optional[float]:
    """
    从pdbqt文件中提取对接能量（辅助函数）
    """
    try:
        with open(pdbqt_file, 'r') as f:
            for line in f:
                if line.startswith("REMARK VINA RESULT:"):
                    # 提取能量值
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        return float(parts[3])  # 第一个值是能量
        return None
    except Exception as e:
        print(f"从pdbqt文件提取能量时出错 {pdbqt_file}: {e}")
        return None

class DockingProcessor:
    """对接处理类"""
    
    def __init__(self, vina_exe: str = VINA_EXE_PATH, auto_clean: bool = True):
        """
        初始化对接处理器
        
        Args:
            vina_exe: vina可执行文件路径
        """
        self.vina_exe = vina_exe
        self.results_dir = Path("results")
        self.auto_clean = auto_clean
        self.results_dir.mkdir(exist_ok=True)

    def extract_energy_from_pdbqt(self, pdbqt_file: Path) -> Optional[float]:
        """现在直接调用外部函数"""
        return extract_energy_from_pdbqt(pdbqt_file)
    
    def run_parallel_docking(self, ligand_pdbqts: List[Path], receptor_pdbqt: Path, 
                            vina_conf: str, max_workers: int = None) -> List[Tuple[Path, float]]:
        """
        并行运行多个分子对接
        
        Args:
            ligand_pdbqts: 配体pdbqt文件路径列表
            receptor_pdbqt: 受体pdbqt文件路径
            vina_conf: vina配置文件路径
            max_workers: 最大工作进程数
            
        Returns:
            (对接结果文件路径, 对接能量) 列表
        """
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        
        docking_results = []
        
        # 创建任务参数列表
        task_args = []
        for ligand in ligand_pdbqts:
            task_args.append((ligand, receptor_pdbqt, vina_conf, self.vina_exe))
        
        print(f"开始并行对接，使用 {max_workers} 个CPU核心")
        
        # 使用进程池并行执行
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for args in task_args:
                future = executor.submit(run_single_docking_task, *args)
                futures.append(future)
            
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=300)  # 5分钟超时
                    if result:
                        docking_results.append(result)
                        ligand_name = ligand_pdbqts[i].stem
                        energy = result[1] if result[1] is not None else "未知"
                        print(f"进度: {i+1}/{len(ligand_pdbqts)} - {ligand_name}: 能量 = {energy}")
                except Exception as e:
                    print(f"对接任务失败: {e}")
        
        # 如果启用自动清理
        if self.auto_clean and docking_results:
            print("\n自动清理对接结果文件...")
            cleaned_count = 0
            for result_file, energy in docking_results:
                if result_file and result_file.exists():
                    if self.fix_windows_vina_output(result_file):
                        cleaned_count += 1
            
            print(f"已清理 {cleaned_count}/{len(docking_results)} 个文件")
        
        return docking_results
        
   
    def plot_energy_bar_chart(self, docking_results: List[Tuple[Path, float]], 
                             top_n: int = 50) -> None:
        """
        绘制对接能量柱状图
        
        Args:
            docking_results: (对接结果文件路径, 对接能量) 列表
            top_n: 显示前N个分子
        """
        # 过滤掉能量为None的结果并按能量排序
        valid_results = [(path, energy) for path, energy in docking_results if energy is not None]
        sorted_results = sorted(valid_results, key=lambda x: x[1])
        
        # 只取前top_n个
        if len(sorted_results) > top_n:
            sorted_results = sorted_results[:top_n]
        
        if not sorted_results:
            print("没有有效的对接结果可用于绘图")
            return
        
        # 提取数据和标签
        ligands = [Path(path).stem.replace('_docked', '') for path, _ in sorted_results]
        energies = [energy for _, energy in sorted_results]

        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'KaiTi', 'FangSong']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建柱状图
        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(ligands)), energies, color='skyblue')
        
        # 在柱子上方添加能量值（使用英文字体避免中文问题）
        for i, (bar, energy) in enumerate(zip(bars, energies)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f'{energy:.2f}', ha='center', va='bottom', fontsize=8, 
                    fontfamily='DejaVu Sans')  # 使用英文字体显示数字
        
        # 设置图表属性
        plt.xlabel('配体分子', fontsize=12)
        plt.ylabel('对接能量 (kcal/mol)', fontsize=12)
        plt.title('分子对接能量排名', fontsize=14)
        
        # 如果x轴标签有中文，减小字体大小
        plt.xticks(range(len(ligands)), ligands, rotation=90, fontsize=6)  # 减小字体
        
        plt.tight_layout()
        
        # 保存图表
        plot_path = "docking_energies.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"已保存能量柱状图: {plot_path}")
    
    def create_pymol_pml(self, receptor_pdbqt: Path, docking_results: List[Tuple[Path, float]], 
                        top_n: int = 50) -> None:
        """
        创建PyMOL的pml脚本文件
        
        Args:
            receptor_pdbqt: 受体pdbqt文件路径
            docking_results: (对接结果文件路径, 对接能量) 列表
            top_n: 显示前N个分子
        """
        # 过滤掉能量为None的结果并按能量排序
        valid_results = [(path, energy) for path, energy in docking_results if energy is not None]
        sorted_results = sorted(valid_results, key=lambda x: x[1])
        
        # 只取前top_n个
        if len(sorted_results) > top_n:
            sorted_results = sorted_results[:top_n]
        
        if not sorted_results:
            print("没有有效的对接结果可用于创建PML文件")
            return
        
        # 创建PML文件内容
        pml_content = "# PyMOL脚本 - 对接结果可视化\n\n"
        
        # 加载受体
        pml_content += f"# 加载受体\n"
        pml_content += f"load {receptor_pdbqt}, receptor\n"
        pml_content += f"hide everything, receptor\n"
        pml_content += f"show cartoon, receptor\n"
        pml_content += f"color gray, receptor\n\n"
        
        # 定义颜色列表
        colors = [
            "red", "blue", "green", "yellow", "orange", 
            "purple", "pink", "cyan", "magenta", "salmon"
        ]
        
        # 加载配体并按能量排序
        pml_content += f"# 加载配体（按能量从低到高排序）\n"
        for i, (ligand_path, energy) in enumerate(sorted_results):
            ligand_name = Path(ligand_path).stem.replace('_docked', '')
            color_idx = i % len(colors)
            
            pml_content += f"load {ligand_path}, ligand_{ligand_name}\n"
            pml_content += f"show sticks, ligand_{ligand_name}\n"
            pml_content += f"color {colors[color_idx]}, ligand_{ligand_name} & elem C \n"
            pml_content += f"set stick_radius, 0.2, ligand_{ligand_name}\n"
            pml_content += f"# 能量: {energy:.2f} kcal/mol\n\n"
        
        # 添加显示设置
        pml_content += "# 显示设置\n"
        pml_content += "set cartoon_transparency, 0.5\n"
        pml_content += "bg_color white\n"
        pml_content += "set_view (\n"
        pml_content += "     0.8,    0.2,    0.5,\n"
        pml_content += "     0.5,    0.1,   -0.8,\n"
        pml_content += "    -0.2,    0.9,   -0.1,\n"
        pml_content += "     0.0,    0.0, -100.0,\n"
        pml_content += "    50.0,   50.0,   50.0,\n"
        pml_content += "    80.0,  120.0,    0.0 )\n"
        
        # 保存PML文件
        pml_path = "docking_results.pml"
        with open(pml_path, 'w') as f:
            f.write(pml_content)
        
        print(f"已创建PyMOL脚本: {pml_path}")
        
        # 同时创建文本格式的结果摘要
        self.create_results_summary(sorted_results)
    
    def create_results_summary(self, sorted_results: List[Tuple[Path, float]]) -> None:
        """
        创建对接结果摘要
        
        Args:
            sorted_results: 排序后的对接结果列表
        """
        summary_path = "docking_summary.txt"
        
        with open(summary_path, 'w') as f:
            f.write("分子对接结果摘要\n")
            f.write("=" * 50 + "\n")
            f.write(f"{'排名':<5} {'分子名称':<30} {'对接能量(kcal/mol)':<20}\n")
            f.write("-" * 50 + "\n")
            
            for i, (ligand_path, energy) in enumerate(sorted_results, 1):
                ligand_name = Path(ligand_path).stem.replace('_docked', '')
                f.write(f"{i:<5} {ligand_name:<30} {energy:<20.2f}\n")
        
        print(f"已创建结果摘要: {summary_path}")

    def fix_windows_vina_output(self, pdbqt_file: Path) -> bool:
        """
        专门修复Windows下Vina输出的PDBQT文件问题
        
        Args:
            pdbqt_file: 要修复的PDBQT文件路径
            
        Returns:
            修复是否成功
        """
        try:
            # 读取文件
            with open(pdbqt_file, 'rb') as f:
                content = f.read()
            
            # 转换为文本，处理可能的编码问题
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                # Windows下常见的是cp1252或latin-1编码
                try:
                    text = content.decode('cp1252')
                except:
                    text = content.decode('latin-1', errors='ignore')
            
            # 特殊处理：移除ENDMDL之前的任何非标准行
            lines = text.splitlines(keepends=True)
            
            # 寻找ENDMDL的位置
            endmdl_indices = []
            for i, line in enumerate(lines):
                if 'ENDMDL' in line.upper():
                    endmdl_indices.append(i)
            
            if not endmdl_indices:
                print(f"警告: {pdbqt_file.name} 中没有找到ENDMDL标记")
                return False
            
            # 使用最后一个ENDMDL的位置
            last_endmdl = endmdl_indices[-1]
            
            # 清理ENDMDL之前的行
            cleaned_lines = []
            for i, line in enumerate(lines):
                if i <= last_endmdl:
                    # ENDMDL及之前的行，进行清理
                    line_clean = line.rstrip('\n\r')

                    # 移除二进制字符
                    line_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', line_clean)

                    # 检查是否是有效行
                    if (line_clean.startswith((f'{PDB_RECORD_ATOM} ', f'{PDB_RECORD_HETATM} ', 'ROOT ', 'ENDROOT',
                                             'BRANCH ', 'ENDBRANCH', 'TORSDOF',
                                             'REMARK ', 'MODEL ', 'ENDMDL', 'COMPND')) or
                        line_clean == ''):
                        cleaned_lines.append(line_clean + '\n')
                else:
                    # ENDMDL之后的行（通常是空的或不需要的）
                    pass
            
            # 确保以ENDMDL结束
            if cleaned_lines and not cleaned_lines[-1].strip() == 'ENDMDL':
                cleaned_lines.append('ENDMDL\n')
            
            # 写入修复后的文件
            with open(pdbqt_file, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
            
            print(f"已修复Windows Vina输出文件: {pdbqt_file.name}")
            return True
            
        except Exception as e:
            print(f"修复Windows Vina输出时出错 {pdbqt_file}: {e}")
            return False

def create_default_config(conf_file: Path) -> None:
    """创建默认的Vina配置文件"""
    default_config = """center_x = 0.0
center_y = 0.0
center_z = 0.0
size_x = 16.5
size_y = 16.5
size_z = 16.5
exhaustiveness = 8
num_modes = 10
energy_range = 4
"""
    with open(conf_file, 'w') as f:
        f.write(default_config)
    print(f"已创建默认配置文件: {conf_file}")

def main():
    """主函数"""
    print("注意: 请确保已正确配置路径")
    print("=" * 60)

    # 步骤0：检查并创建配置文件
    conf_file = Path("conf.txt")
    if not conf_file.exists():
        print("未找到conf.txt文件，正在创建默认配置...")
        create_default_config(conf_file)

    # 根据center.pdb更新对接中心坐标
    center_pdb = Path("center.pdb")
    if center_pdb.exists():
        print("找到center.pdb文件，正在提取对接中心坐标...")
        center = extract_center_from_pdb(center_pdb)
        if center:
            update_config_center(conf_file, center[0], center[1], center[2])
        else:
            print("无法从center.pdb提取坐标，将使用原有配置")
    else:
        print("未找到center.pdb文件，将使用conf.txt中的当前坐标")

    # 1. 分子格式转换
    print("=" * 60)
    print("步骤1: 转换分子格式")
    print("=" * 60)



    converter = MolFormatConverter("ligands")
    pdbqt_files = converter.convert_all_ligands()
    
    if not pdbqt_files:
        print("错误: 没有找到或成功转换任何配体文件")
        return
    
    print(f"\n成功转换 {len(pdbqt_files)} 个配体文件为pdbqt格式")
    
    # 2. 准备受体
    print("\n" + "=" * 60)
    print("步骤2: 准备受体蛋白")
    print("=" * 60)
    
    # 假设受体文件名为receptor.pdb，放在当前目录
    receptor_pdb = Path("receptor.pdb")
    if not receptor_pdb.exists():
        print(f"错误: 受体文件 {receptor_pdb} 不存在")
        print("请将受体PDB文件命名为'receptor.pdb'并放在当前目录")
        return
    
    receptor_pdbqt = converter.prepare_receptor(receptor_pdb)
    if not receptor_pdbqt:
        print("错误: 受体准备失败")
        return
    
    # 3. 运行分子对接
    print("\n" + "=" * 60)
    print("步骤3: 运行分子对接")
    print("=" * 60)

    vina_config = "conf.txt"

    # 创建对接处理器
    dock_processor = DockingProcessor(VINA_EXE_PATH)
    
    # 运行并行对接
    docking_results = dock_processor.run_parallel_docking(
        pdbqt_files, receptor_pdbqt, vina_config
    )
    
    if not docking_results:
        print("错误: 没有成功的对接结果")
        return
    
    print(f"\n成功完成 {len(docking_results)} 个分子的对接")
    
    # 4. 分析和可视化结果
    print("\n" + "=" * 60)
    print("步骤4: 分析对接结果")
    print("=" * 60)
    
    # 绘制能量柱状图
    dock_processor.plot_energy_bar_chart(docking_results, top_n=50)
    
    # 创建PyMOL脚本
    dock_processor.create_pymol_pml(receptor_pdbqt, docking_results, top_n=50)
    
    print("\n" + "=" * 60)
    print("所有步骤完成！")
    print("=" * 60)
    print(f"对接结果保存在: {dock_processor.results_dir}")
    print("1. docking_energies.png - 对接能量柱状图")
    print("2. docking_results.pml - PyMOL可视化脚本")
    print("3. docking_summary.txt - 结果摘要")
    print("4. 各个分子的对接结果文件")


if __name__ == "__main__":
    # 在运行前，请确保修改以下路径为您的实际安装路径
    print("注意: 请确保已正确配置以下路径:")
    print(f"VINA_EXE_PATH: {VINA_EXE_PATH}")
    print(f"OPENBABEL_PATH: {OPENBABEL_PATH}")
    print(f"PREPARE_LIGAND_SCRIPT: {PREPARE_LIGAND_SCRIPT}")
    print(f"PREPARE_RECEPTOR_SCRIPT: {PREPARE_RECEPTOR_SCRIPT}")
    print("\n如果路径不正确，请在代码开头修改这些变量")
    print("=" * 60)
    
    main()