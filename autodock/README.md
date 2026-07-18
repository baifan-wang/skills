[README.md](https://github.com/user-attachments/files/26244905/README.md)
[README.md](https://github.com/user-attachments/files/26244905/README.md)
# AutoDock Skill

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AutoDock Vina](https://img.shields.io/badge/AutoDock-Vina-green.svg)](https://vina.scripps.edu/)
[![OpenBabel](https://img.shields.io/badge/OpenBabel-3.1.1-orange.svg)](https://openbabel.org/)

**全自动化分子对接工作流，让药物发现更简单、更快速、更可靠**

AutoDock Skill是一个基于AutoDock Vina的自动化分子对接的skill，它将复杂的对接流程简化为**自然语言操作**，能快速完成从蛋白质准备到结果分析的全过程，大大提升效率提升，方便对于脚本和命令行不熟悉的人。

## ✨ 核心特性

- 🚀 **完全自动化** - 从PDB文件到对接结果，全程自动化处理
- ⚡ **并行加速** - 利用多核CPU并行处理
- 🧬 **智能处理** - 自动去除水分子和小分子、可选保留辅因子、添加氢原子
- 🎯 **精准定位** - 多种方式提取对接中心
- 📊 **全面分析** - 自动生成能量排名、可视化脚本和图表
- 🔧 **格式兼容** - 支持SMILES、SDF、MOL2、CDX等10+种格式

## 📦 快速开始

### 系统要求
- **操作系统**: Windows
- **Python**: 3.8+
- **依赖软件**: AutoDock Vina, OpenBabel, MGLTools

### 安装步骤

1. **克隆仓库**
```powershell
git clone https://github.com/baifan-wang/skills.git
cp autodock C:\Users\xxx\.claude\skills
```

2. **安装Python依赖**
```powershell
pip install -r requirements.txt
```

3. **配置外部工具路径**
编辑 `scripts/autovina.py` 中的路径配置：
```python
VINA_EXE_PATH = "C:\\apps\\vina.exe"  # 修改为实际的vina路径
OPENBABEL_PATH = "C:\\OpenBabel-3.1.1\\obabel.exe"  # 修改为实际的openbabel路径
MGL_PATH = "C:\\Program Files (x86)\\MGLTools-1.5.7\\"  # 修改为实际的MGLTools路径
```

## 🚀 使用指南

### 基本工作流

1. **准备输入文件**
```
working_directory/
├── receptor.pdb          # 受体蛋白文件
├── center.pdb            # 可选：对接中心参考
├── conf.txt              # 可选：对接参数（自动创建）
└── ligands/              # 配体文件目录
    ├── compound1.sdf
    ├── compound2.smiles
    └── ...
```

2. **运行自动化对接**
在working_directory启动claude code，输入：
```
/autodock 清理3NKS.pdb，保留其中的FAD，以3NKS.pdb中的ACJ为中心，进行分子对接
```
以上指令以3NKS.pdb这个蛋白质结构进行分子对接，以其中的共晶小分子ACJ作为对接的中心进行对接。由于辅因子FAD是结合口袋的一部分，给予保留。


3. **查看结果**

# 查看能量排名
cat docking_summary.txt

# 可视化对接结果
用pymol打开docking_results.pml

# 查看能量分布图
docking_energies.png


### 完整示例：3NKS蛋白对接


## 📚 详细文档

### 1. 提取对接中心

可以以共晶小分子为对接中心。如果没有共晶小分子，可以以活性口袋中的氨基酸残基来定义对接中心。比如对Claude code说：
```
以A链的第35，87，95号残基来定义对接中心。
```
如果你没有指定对接中心，那么Claude code将以该目录下的conf.txt中定义的对接中心来进行对接。如果没有conf.txt，将以坐标原点(0,0,0)来进行对接。这时候对接结果完全不可靠。

### 2. 对接参数配置
如果你提供了conf.txt，那么Claude code将按照里面的配置来进行对接。如果conf.txt里面提供了对接的中心，那么就不必让claude code来生成对接中心。
**默认conf.txt**：
```ini
center_x = 0.0
center_y = 0.0
center_z = 0.0
size_x = 16.5
size_y = 16.5
size_z = 16.5
exhaustiveness = 8
num_modes = 10
energy_range = 4
```

**参数说明**：
| 参数 | 说明 | 推荐范围 |
|------|------|----------|
| `center_x/y/z` | 对接口袋中心坐标 | 从center.pdb自动计算 |
| `size_x/y/z` | 搜索框大小（Å） | 10-30 |
| `exhaustiveness` | 搜索详尽度 | 1-32（越高越精确） |
| `num_modes` | 输出构象数 | 1-20 |
| `energy_range` | 能量范围（kcal/mol） | 3-7 |

### 3. 支持的配体格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| SMILES | `.smi`, `.smiles` | 制表符分隔：`SMILES name` |
| SDF | `.sdf`, `.sd` | 可包含多个分子 |
| MOL | `.mol` | 单个分子 |
| MOL2 | `.mol2` | 3D结构 |
| ChemDraw | `.cdx` | 需要OpenBabel支持 |
| PDB | `.pdb` | 3D坐标 |
| PDBQT | `.pdbqt` | AutoDock格式（无需转换） |

**SMILES文件格式**：
```
CC(=O)Oc1ccccc1C(=O)O aspirin
CN1C=NC2=C1C(=O)N(C(=O)N2C)C caffeine
```

## 📊 结果解读

### 输出文件结构
```
working_directory/
├── results/                    # 对接结果
│   ├── ligand1_docked.pdbqt
│   ├── ligand2_docked.pdbqt
│   └── ...
├── docking_energies.png        # 能量条形图
├── docking_results.pml         # PyMOL可视化脚本
├── docking_summary.txt         # 结果摘要
└── receptor.pdbqt              # 准备的受体
```

### 能量排名示例
```
排名    分子名称        对接能量(kcal/mol)
----------------------------------------
1      mol2l          -9.12  ⭐ 最佳结合
2      2_1            -8.44
3      6_5            -8.42
4      5_4            -8.05
5      7_6            -7.67
```


## 🔧 故障排除

### 常见问题

**Q: "No ligand files found"**
```
检查ligands/目录是否存在且包含支持的文件格式
确保文件扩展名正确（.sdf, .smi, .mol2等）
```

**Q: "Receptor preparation failed"**
```
检查MGLTools路径配置是否正确
确保receptor.pdb包含有效的ATOM记录
尝试重新处理PDB文件：python scripts/process_pdb.py input.pdb receptor.pdb
```

**Q: "Low docking scores"**
```
验证对接中心坐标是否正确
增加exhaustiveness参数（如从8增加到16）
检查配体的3D结构质量
```

**Q: "OpenBabel conversion failed"**
```
确认OpenBabel已正确安装
对于CDX文件，确保OpenBabel编译时启用了CDX支持
尝试将文件转换为中间格式（如SDF）再处理
```



## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 报告问题
请在GitHub Issues中报告bug或提出功能建议。

### 提交代码
1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/yourusername/autodock-skill.git
cd autodock-skill

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -r requirements-dev.txt

```

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- **AutoDock Vina团队** - 提供核心对接引擎
- **OpenBabel团队** - 化学格式转换工具
- **MGLTools团队** - 受体和配体准备工具
- **RDKit团队** - 化学信息学库
- **所有贡献者和用户** - 感谢你们的反馈和支持

## 📞 联系方式

- **项目主页**: [https://github.com/yourusername/autodock-skill](https://github.com/yourusername/autodock-skill)
- **问题反馈**: [GitHub Issues](https://github.com/yourusername/autodock-skill/issues)
- **电子邮件**: your.email@example.com

## ⭐ 支持项目

如果这个项目对您有帮助，请给我们一个Star！⭐

---

**让计算赋能发现，让技术加速创新** 🚀