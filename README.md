# Claude Code Skills

计算化学与分子模拟相关的 Claude Code Skills 集合。

## 技能列表

### 1. autodock — 自动化分子对接

基于 AutoDock Vina 的全自动分子对接工作流。从 PDB 文件到对接结果，全程自动化处理。

**核心功能：**
- 自动处理受体蛋白（去水、去小分子、加氢、可选保留辅因子）
- 支持 10+ 种配体格式（SMILES、SDF、MOL2、PDB、CDX 等）
- 多种对接中心定义方式（配体中心、残基选择、手动坐标）
- 多核 CPU 并行加速
- 自动生成能量排名、可视化脚本和图表
- 支持虚拟筛选

**触发关键词：** 分子对接、docking、AutoDock Vina、虚拟筛选、蛋白-配体对接、PDB 处理

### 2. amber-md —  Amber 分子动力学模拟

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
# autodock
cp -r autodock $env:USERPROFILE\.claude\skills\autodock

# amber-md
cp -r amber-md $env:USERPROFILE\.claude\skills\amber-md
```

各技能的详细安装和配置说明请参见对应目录下的 README。

## 依赖概览

| 技能 | 外部软件 | Python 库 |
|------|---------|-----------|
| autodock | AutoDock Vina, OpenBabel, MGLTools | numpy, pandas, matplotlib, rdkit |
| amber-md | AmberTools 26+, Amber 26+ | numpy, pandas, matplotlib |

## 许可证

各技能遵循其各自的许可证。autodock 采用 MIT 许可证。
