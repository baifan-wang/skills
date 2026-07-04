# Claude Code Skills

计算化学与分子模拟相关的 Claude Code Skills 集合。

## 项目结构

| 目录 | 说明 |
|------|------|
| `autodock/` | 自动化分子对接技能 |
| `amber-md/` | Amber 分子动力学模拟技能 |
| `claude-science/` | Claude Science 扩展集合（MCP 服务器 + 科学技能） |

## 技能列表

### 1. claude-science — Claude Science 科学计算扩展

面向生命科学与计算化学的综合扩展集合，包含 MCP 数据服务和科学计算技能。

**MCP 服务器：**
- **bio-tools**：统一查询接口，覆盖 23 个生物信息学数据域约 247 个工具（PubMed、ChEMBL、ClinVar、GTEx、PDB 等）
- **ketcher-chemistry**：交互式化学结构编辑器（基于 EPAM Ketcher）

**科学技能（30+ 个）：**
- 蛋白质结构预测与设计（AlphaFold2、Boltz-2、Chai-1、OpenFold3、ESMFold2、ProteinMPNN 等）
- 基因组与单细胞分析（Evo2、Borzoi、scGPT、scVI-tools）
- 分子对接（DiffDock-L 全盲对接）
- 远程计算与 HPC（SSH/SLURM、Modal 无服务器 GPU）
- 科研写作与可视化（出版级图表、文献综述、PDF 解析）

详见 [claude-science/README.md](claude-science/README.md)

### 2. autodock — 自动化分子对接

基于 AutoDock Vina 的全自动分子对接工作流。从 PDB 文件到对接结果，全程自动化处理。

**核心功能：**
- 自动处理受体蛋白（去水、去小分子、加氢、可选保留辅因子）
- 支持 10+ 种配体格式（SMILES、SDF、MOL2、PDB、CDX 等）
- 多种对接中心定义方式（配体中心、残基选择、手动坐标）
- 多核 CPU 并行加速
- 自动生成能量排名、可视化脚本和图表
- 支持虚拟筛选

**触发关键词：** 分子对接、docking、AutoDock Vina、虚拟筛选、蛋白-配体对接、PDB 处理

### 3. amber-md — Amber 分子动力学模拟

Amber 分子动力学模拟全流程助手。Claude 直接执行体系构建和轨迹分析，用户自行运行计算密集的模拟步骤。

**核心功能：**
- 体系构建：antechamber / parmchk2 / tleap 自动化
- 自动生成 Amber 输入文件（min.in / heat.in / density.in / product.in）
- 自动生成运行脚本（bash / Slurm / PBS）
- 全面的轨迹分析：RMSD、RMSF、回旋半径、SASA、DSSP 二级结构、氢键分析、距离矩阵、聚类分析、PCA、自由能景观图
- MM-PBSA/GBSA 结合自由能计算
- 支持蛋白-配体、纯蛋白、蛋白-蛋白复合物体系

**触发关键词：** Amber、MD 模拟、分子动力学、蛋白模拟、antechamber、tleap、pmemd、cpptraj、MMPBSA、RMSD 分析

## 安装

```powershell
git clone https://github.com/baifan-wang/skills.git
```

将需要的技能目录复制到 Claude Code 的 skills 目录：

```powershell
# claude-science
cp -r claude-science/mcp-servers/* $env:USERPROFILE\.claude\mcp\
cp -r claude-science/skills/<skill-name> $env:USERPROFILE\.claude\skills\<skill-name>

# autodock
cp -r autodock $env:USERPROFILE\.claude\skills\autodock

# amber-md
cp -r amber-md $env:USERPROFILE\.claude\skills\amber-md
```

各技能的详细安装和配置说明请参见对应目录下的 README。

## 依赖概览

| 技能 | 外部软件 | Python 库 |
|------|---------|-----------|
| claude-science | 按技能各异（详见子目录） | 按技能各异（详见子目录） |
| autodock | AutoDock Vina, OpenBabel, MGLTools | numpy, pandas, matplotlib, rdkit |
| amber-md | AmberTools 26+, Amber 26+ | numpy, pandas, matplotlib |

## 许可证

各技能遵循其各自的许可证。autodock 采用 MIT 许可证。
