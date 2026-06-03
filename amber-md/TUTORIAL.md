# 利用 amber-md 技能进行分子动力学模拟教程

本教程基于蛋白 1L2Y（Trp-cage，20 残基）与吲哚类配体的复合物体系，完整演示从 PDB 文件到结合自由能的全流程。

---

## 目录

1. [准备工作](#1-准备工作)
2. [阶段 0：信息收集](#2-阶段-0信息收集)
3. [阶段 1：体系构建](#3-阶段-1体系构建)
4. [阶段 2：模拟运行](#4-阶段-2模拟运行)
5. [阶段 3：结果分析](#5-阶段-3结果分析)
6. [结果判读](#6-结果判读)
7. [常见问题排查](#7-常见问题排查)

---

## 1. 准备工作

### 1.1 输入文件

```
workdir/
├── 1L2Y-1.pdb      # 蛋白结构（已加氢，20 残基）
└── ligand.pdb       # 配体结构（吲哚环类分子，已加氢）
```

### 1.2 环境检查

```bash
which tleap antechamber parmchk2 cpptraj    # AmberTools
which pmemd.cuda                              # GPU 版本
python -c "import pandas, numpy, matplotlib"  # Python 环境
```

### 1.3 启动技能

在 Claude Code 中输入：

```
/amber-md 利用当前目录下的蛋白质pdb文件：1L2Y-1.pdb和小分子配体文件：ligand.pdb进行分子动力学模拟
```

---

## 2. 阶段 0：信息收集

Claude 会依次询问以下问题，按实际情况回答：

| 问题 | 本教程的选择 | 说明 |
|------|-------------|------|
| 配体净电荷 | 0 | 吲哚类分子在生理 pH 下为中性 |
| 计算资源 | GPU (pmemd.cuda) | 已检测到 RTX 5090 |
| 作业调度器 | bash（本地运行） | 无 Slurm/PBS |
| 模拟时长 | 1 ns（默认） | 500,000 步，dt=0.002 ps |
| 分析需求 | 全部 | RMSD/RMSF/Rg/SASA/DSSP/氢键/聚类/PCA/FEL/MM-PBSA |
| 力场 | ff19SB + TIP3P + GAFF2（默认） | 当前 Amber 推荐组合 |

**关键提示**：若不确定，全部用默认值即可。1 ns 模拟适合流程验证，发表级研究建议 100 ns+。

---

## 3. 阶段 1：体系构建

Claude 自动执行以下步骤（用户无需操作）：

### 3.1 小分子参数化

```bash
cd prep
antechamber -i ../ligand.pdb -fi pdb -o ligand.prepin -fo prepi -c bcc -nc 0 -s 2
parmchk2 -i ligand.prepin -f prepi -o ligand.frcmod
```

检查：确认 `ligand.prepin` 中残基名与 PDB 一致（都是 `MOL`）。

### 3.2 配体残基号处理

蛋白残基号为 1-20，配体残基号 6 与蛋白 ALA 6 冲突。Claude 将配体残基号改为 21：

```bash
sed 's/MOL A   6/MOL A  21/' ligand.pdb > ligand_renum.pdb
```

### 3.3 LEaP 构建体系

Claude 编写 `leap.in`，**关键：comp_dry.top 必须在 solvateoct 之前保存**：

```tleap
source leaprc.protein.ff19SB
source leaprc.water.tip3p
source leaprc.gaff2
loadamberprep ligand.prepin
loadamberparams ligand.frcmod
protein = loadpdb ../1L2Y-1.pdb
ligand = loadpdb ligand_renum.pdb

saveamberparm protein protein.top protein.crd   # MM-PBSA 用
saveamberparm ligand ligand.top ligand.crd      # MM-PBSA 用

comp = combine { protein ligand }
saveamberparm comp comp_dry.top comp_dry.crd    # ← 必须在溶剂化前

solvateoct comp TIP3PBOX 10.0
addions2 comp Na+ 0
addions2 comp Cl- 0

saveamberparm comp comp_oct.top comp_oct.crd    # 溶剂化体系（模拟用）
savepdb comp comp_oct.pdb
quit
```

运行：

```bash
tleap -f leap.in
```

### 3.4 检查输出

| 检查项 | 本体系结果 |
|--------|-----------|
| tleap ERROR 数 | 0 |
| 蛋白净电荷 | +1（N 端 + LYS + ARG − ASP − C 端） |
| 中和离子 | 1 Cl⁻ |
| 水分子数 | 2180 |
| 盒子尺寸 | ~53.5 Å（缓冲 >13 Å） |
| 输出文件 | comp_oct.top/crd, comp_dry.top/crd, protein.top/crd, ligand.top/crd |

**阶段 1 完成，Claude 暂停等待确认。**

---

## 4. 阶段 2：模拟运行

Claude 生成全部输入文件到 `md/` 目录：

```
md/
├── min1.in          # 优化溶剂（约束蛋白+配体，restraint_wt=500）
├── min2.in          # 优化溶剂+氢原子（约束重原子）
├── min3.in          # 全原子自由优化（无约束）
├── heat.in          # 0K→300K 升温 50 ps（NVT, Langevin）
├── density.in       # NPT 密度平衡 50 ps
├── product.in       # 生产模拟 1 ns（NPT, NetCDF 轨迹）
└── run.sh           # 一键运行脚本
```

### 4.1 运行模拟

```bash
cd md
bash run.sh          # GPU 版本
bash run.sh cpu      # CPU 版本（如无 GPU）
```

### 4.2 预估耗时

| 硬件 | 1 ns 耗时 |
|------|----------|
| RTX 5090 | ~5 分钟 |
| CPU 单核 | ~5 小时 |

本教程在 RTX 5090 上实际耗时 268 秒（324 ns/day）。

### 4.3 验证模拟完成

```bash
tail -20 product.out | grep "Total wall time"
# 输出：Total wall time: 268 seconds
```

**阶段 2 完成，用户告知 Claude 模拟已结束。**

---

## 5. 阶段 3：结果分析

Claude 自动执行全部分析模块。

### 5.1 轨迹预处理

```bash
cd analysis/strip
cpptraj -i strip.in
```

strip.in 内容：
```
parm ../../prep/comp_dry.top
trajin ../../md/product.nc
strip :WAT,:Na+,:Cl-
center :1-20 mass
image center familiar
rms reference first
trajout strip.nc netcdf
```

输出 `strip.nc`（3.6 MB，仅含蛋白+配体的 306 个原子，1000 帧）。

### 5.2 热力学分析

```bash
cd analysis/physical
perl process_mdout.perl ../../md/heat.out ../../md/density.out ../../md/product.out
python plot_thermo.py
```

输出 `thermodynamics.png`：温度稳定在 300 K，密度 ~1.0 g/mL，势能/总能量平稳无漂移 → 体系已充分平衡。

### 5.3 RMSD / RMSF / Rg

```bash
cd analysis/rmsd
cpptraj -i rmsd.in
python plot_rmsd.py
```

rmsd.in 内容：
```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
rms first mass out rmsd_bb.dat @CA,C,N time 1.0
rms first mass out rmsd_all.dat time 1.0
atomicfluct out rmsf_byres.dat :1-20 byres
atomicfluct out rmsf_bb.dat :1-20@CA,C,N byres
radgyr out rg.dat :1-20
```

输出 `rmsd_rmsf_rg.png`：
- 上图：骨架/全原子 RMSD 时间曲线（反映结构偏离初始构象的程度）
- 中图：RMSF 按残基分布（带圆点线图，反映每个残基的柔性）
- 下图：回旋半径 Rg 时间曲线（反映蛋白整体紧凑度）

### 5.4 SASA / DSSP

```bash
cd analysis/sasa
cpptraj -i sasa.in
python plot_sasa_dssp.py
```

sasa.in 内容：
```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
molsurf out sasa.dat :1-20
secstruct out dssp.dat :1-20
```

输出 `sasa_dssp.png`：
- 上图：溶剂可及表面积 SASA 时间曲线
- 下图：二级结构堆叠面积图（Alpha/Beta/3-10/Turn/Bend-Coil）

### 5.5 氢键分析

```bash
cd analysis/hbond
cpptraj -i hbond.in
```

hbond.in 内容：
```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
hbond HBOND out hbond.dat :1-20 :21 avgout hbond_avg.dat
```

本体系结果：**未检测到稳定的蛋白-配体氢键**（cpptraj 输出 `Warning: Set 'HBOND[UU]' contains no data`）。这不一定是错误——吲哚类配体主要通过疏水和 π-π 堆积结合，而非氢键。

### 5.6 距离矩阵

```bash
cd analysis/distmat
cpptraj -i distmat.in
python plot_distmat.py
```

输出 `distmat.png`：Cα-Cα 距离热力图，展示残基间空间邻近关系。

### 5.7 聚类分析

```bash
cd analysis/cluster
cpptraj -i cluster.in
python plot_cluster.py
```

cluster.in 内容（注意 repout 须并入主命令）：
```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
rms first @CA
cluster C0 kmeans clusters 5 randompoint maxit 500 rms @CA sieve 10 \
  repout rep repframe \
  out cnumvtime.dat summary summary.dat info info.dat
```

输出 `cluster_analysis.png`：
- 左图：聚类编号随时间变化
- 右图：5 个聚类群体的占比饼图
- 代表性构象 PDB 文件：`rep.c0.pdb`, `rep.c1.pdb` ...

### 5.8 PCA 主成分分析

PCA 须分两步执行：

**第一步** — 计算协方差矩阵并对角化：

```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
rms first @CA
matrix covar @CA name covar
diagmatrix covar out evecs.dat vecs 50 name evecs
run
```

**第二步** — 投影到 PC1-PC2：

```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
rms first @CA
projection evecs evecs.dat out proj.dat @CA beg 1 end 2
run
```

```bash
cd analysis/pca
cpptraj -i pca_step1.in   # 第一步
cpptraj -i pca_step2.in   # 第二步
python plot_pca.py
```

输出 `pca_analysis.png`：
- 左图：PC1-PC2 散点图（按帧着色）
- 右图：各主成分方差解释率

### 5.9 自由能景观

```bash
cd analysis/fel
python plot_fel.py
```

基于 PC1-PC2 二维直方图计算 ΔG = −RT ln(P/Pmax)，输出 `free_energy_landscape.png`：等值线图展示构象空间中的能量极小值区域。

### 5.10 MM-PBSA/GBSA 结合自由能

```bash
cd analysis/mmpbsa
MMPBSA.py -O -i mmgbsa.in -o mmgbsa.dat \
  -sp ../../prep/comp_oct.top \
  -cp ../../prep/comp_dry.top \
  -rp ../../prep/protein.top \
  -lp ../../prep/ligand.top \
  -y ../../md/product.nc

python plot_mmgbsa.py
```

mmgbsa.in 内容：
```
Input file for running PB and GB
&general
  interval=5, verbose=1, startframe=21, endframe=1000
/
&gb
  igb=5, saltcon=0.100
/
```

输出 `mmgbsa_results.png`：
- 左图：能量分解（范德华/静电/极性溶剂化/非极性溶剂化）
- 右图：结合自由能总结（ΔG_gas / ΔG_solv / ΔG_total）

---

## 6. 结果判读

### 6.1 模拟质量检查

| 指标 | 正常范围 | 异常处理 |
|------|---------|----------|
| 温度 | 300 ± 5 K | 检查 ntt/gamma_ln 参数 |
| 密度 | ~1.0 g/mL | 延长密度平衡时间 |
| 总能量漂移 | < 1% / ns | 检查盒子尺寸、截断值 |
| RMSD 稳定 | 波动 < 2 Å | 延长模拟时间 |

### 6.2 本体系关键结果

| 分析项 | 结果 | 解读 |
|--------|------|------|
| RMSD 骨架 | 见 rmsd 图 | 小蛋白（20 残基）结构稳定 |
| Rg | 见 rmsd 图 | 蛋白紧凑折叠 |
| 二级结构 | 见 DSSP 图 | α-螺旋含量稳定 |
| 蛋白-配体氢键 | 无稳定氢键 | 结合由疏水/π-π 堆积主导 |
| ΔG_binding (MM-GBSA) | **−16.09 ± 4.01 kcal/mol** | 有利结合 |
| 主要贡献 | 范德华 + 静电 | 典型的小分子-蛋白结合模式 |

### 6.3 MM-GBSA 能量分解解读

- **VDWAALS（负值）**：范德华相互作用，反映形状互补性
- **EEL（负值）**：静电相互作用，反映电荷互补性
- **EGB（正值）**：极性溶剂化自由能惩罚（去溶剂化代价）
- **ESURF（负值）**：非极性溶剂化自由能（疏水效应）

负的总 ΔG 表示结合在热力学上有利。正值则表示不利于结合。

---

## 7. 常见问题排查

### 7.1 "Number of atoms in NetCDF file does not match topology"

**原因**：`comp_dry.top` 在 `solvateoct` 之后保存，包含了水和离子。

**解决**：重新运行 tleap，确保 `saveamberparm comp comp_dry.top comp_dry.crd` 在溶剂化之前。

### 7.2 PCA 报 "Set 'evecs' contains no data"

**原因**：`diagmatrix` 和 `projection` 放在了同一次 cpptraj 调用中。

**解决**：分两步执行（见 5.8 节）。

### 7.3 聚类报 "No clustering algorithm specified"

**原因**：`repout rep repframe` 被写成独立的第二条 `cluster C0` 命令。

**解决**：将 `repout` 并入主 cluster 命令（见 5.7 节）。

### 7.4 Python 读数据报 IndexError / KeyError

**原因**：cpptraj 输出文件首行为 `#` 注释头，pandas 未跳过。

**解决**：所有 `pd.read_csv()` 加 `comment="#"` 参数。

### 7.5 DSSP 图不显示或报 AttributeError

**原因**：DSSP 输出是宽格式矩阵（每残基一列整数码），不是长格式。

**解决**：用 `iloc[:, 1:]` 提取 SS 码列，按整数码分组统计（见 5.4 节）。

### 7.6 MMPBSA.py 报找不到 protein.top / ligand.top

**原因**：阶段 1 的 leap.in 中未保存独立组分拓扑。

**解决**：重新运行 tleap，在 `combine` 之后、`solvateoct` 之前添加 `saveamberparm protein protein.top protein.crd` 和 `saveamberparm ligand ligand.top ligand.crd`。

---

## 进阶建议

1. **延长模拟**：发表级研究建议至少 100 ns，推荐 500 ns-1 µs
2. **重复模拟**：至少 3 次独立重复，评估结果可重复性
3. **MM-PBSA 替代 MM-GBSA**：PB 模型更精确但更耗时
4. **结合自由能分解**：使用 `energy_decomposition=1` 获得 per-residue 贡献
5. **熵贡献**：使用 NMODE 或 Quasi-harmonic 方法计算 −TΔS 项
6. **增强采样**：对慢自由度使用 umbrella sampling 或 metadynamics

---

## 文件清单（本教程生成的全部文件）

```
workdir/
├── prep/
│   ├── leap.in, leap_split.in, leap_fix.in
│   ├── ligand.prepin, ligand.frcmod
│   ├── comp_oct.top, comp_oct.crd, comp_oct.pdb
│   ├── comp_dry.top, comp_dry.crd
│   ├── protein.top, protein.crd
│   └── ligand.top, ligand.crd
├── md/
│   ├── min1.in, min2.in, min3.in
│   ├── heat.in, density.in, product.in
│   ├── run.sh
│   └── *.out, *.rst, *.mdcrd, product.nc
└── analysis/
    ├── strip/strip.nc
    ├── physical/thermodynamics.png
    ├── rmsd/rmsd_rmsf_rg.png
    ├── sasa/sasa_dssp.png
    ├── hbond/
    ├── distmat/distmat.png
    ├── cluster/cluster_analysis.png, rep.c*.pdb
    ├── pca/pca_analysis.png
    ├── fel/free_energy_landscape.png
    └── mmpbsa/mmgbsa_results.png
```
