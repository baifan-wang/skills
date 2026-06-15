---
name: amber-md
description: >
  Amber 分子动力学模拟全流程助手。Claude 直接执行体系构建（antechamber/
  parmchk2/tleap）和轨迹分析（cpptraj + Python 绘图），用户自行运行计算
  密集的模拟步骤（pmemd.cuda/pmemd.MPI/sander）。支持蛋白-配体、纯蛋白、
  蛋白-蛋白复合物体系。自动生成 Amber 输入文件（min.in / heat.in /
  density.in / product.in）和运行脚本（bash / Slurm / PBS）。分析能力
  包括 RMSD、RMSF、回旋半径、SASA、DSSP 二级结构、氢键分析、距离矩阵、
  聚类分析、主成分分析 (PCA)、自由能景观图、MM-PBSA/GBSA 结合自由能计算。
  用户提及 Amber、MD 模拟、分子动力学、蛋白模拟、配体结合、antechamber、
  tleap/LEaP、pmemd、sander、cpptraj、MMPBSA、RMSD 分析、轨迹分析时触发。
---

# Amber 分子动力学模拟技能

## 快速启动

当用户提及 Amber 分子动力学相关需求时，先快速诊断用户当前所处阶段，然后路由到对应工作流：

| 用户状态 | 路由 |
|----------|------|
| 从零开始，只有 PDB 结构文件 | 阶段 0 → 阶段 1 → 阶段 2 → 阶段 3 |
| 已有拓扑 (.top) + 坐标 (.crd) 文件 | 跳过阶段 1，从阶段 2 开始 |
| 已完成模拟，有轨迹文件 (.nc/.mdcrd) | 直接进入阶段 3 |
| 模拟报错或结果异常 | 跳到阶段 4 排错 |
| 只需要输入文件模板或参考命令 | 直接引用 `references/` 中对应的参考文件 |

**核心原则**：每个阶段结束后暂停，向用户确认输出无误再进入下一阶段。不要一次性生成全部内容。关键决策点需解释 WHY（如：为什么分三步优化、为什么用 Langevin 控温）。

**谁执行什么**：阶段 1（antechamber / parmchk2 / tleap）由 Claude 直接执行，这些命令秒级完成。阶段 2（能量优化→生产模拟）由用户自行运行，因为计算耗时长（GPU ~5分钟、CPU ~5小时）。阶段 3（cpptraj 分析 + Python 绘图）由 Claude 执行。

---

## 阶段 0：信息收集

在生成任何文件之前，一次性向用户询问以下信息：

1. **输入文件**：有哪些文件可用？原始 PDB 结构？小分子配体文件（PDB/MOL2/SDF）？已有 top/crd？
2. **体系类型**：蛋白-配体复合物 / 纯蛋白 / 蛋白-蛋白复合物？
3. **计算资源**：GPU（`pmemd.cuda`）还是 CPU（`pmemd.MPI` / `sander.MPI`）？可用核心数？
4. **作业调度器**：Slurm / PBS / 无（本地 bash 运行）？
5. **模拟时长**：默认 1 ns（500,000 步，dt=0.002 ps）。教程级 1-10 ns 即可，发表级通常需 100 ns 以上。
6. **分析需求**：需要哪些分析？（RMSD / RMSF / Rg / SASA / 氢键 / 聚类 / PCA / 自由能景观 / MM-PBSA）
   - **注意：MM-PBSA/GBSA 仅适用于蛋白-配体或蛋白-蛋白复合物体系，纯蛋白体系不适用。**

**新手默认设置**：如果不确定，默认使用 ff19SB 力场 + TIP3P 水模型 + Langevin 控温 (ntt=3, gamma_ln=2.0)。1 ns 模拟适合教程验证流程，发表级研究建议至少 100 ns。

---

## 阶段 1：体系构建

### 1.1 处理蛋白结构

如果用户提供的 PDB 是刚从 RCSB 下载的原始文件，提醒预处理事项：
- 使用 `pdb4amber` 清理 PDB（去除水分子、非标准残基、替代构象）
- 检查残基命名：组氨酸 HIS 须改为 HIE（ε-质子化）/ HID（δ-质子化）/ HIP（双质子化）；半胱氨酸 CYS 如形成二硫键须改为 CYX
- 检查缺失残基/原子，必要时用 Modeller 等工具补全

### 1.2 小分子力场参数（如有配体）

**Claude 直接执行 antechamber + parmchk2**（这些命令几秒内完成，无需用户操作）。

执行前必须询问用户小分子的净电荷（默认 0）。净电荷由小分子在生理 pH 下的质子化状态决定。`-nc` 必须是整数（如 -2, -1, 0, 1, 2）。

```bash
antechamber -i ligand.pdb -fi pdb -o ligand.prepin -fo prepi -c bcc -nc 0 -s 2
parmchk2 -i ligand.prepin -f prepi -o ligand.frcmod
```

执行后检查：
1. 确认 `ligand.prepin` 和 `ligand.frcmod` 已生成
2. 打开 `ligand.prepin`，确认残基名称与 `ligand.pdb` 中一致。如不一致，用 Edit 工具修正 prepin 中的残基名

### 1.3 运行 LEaP 构建体系

**Claude 直接编写 `leap.in` 并执行 `tleap -f leap.in`**（通常 1-2 秒完成）。

参考 `references/force-fields.md` 选择力场组合。生成 `leap.in` 并使用 Bash 工具执行：

```bash
tleap -f leap.in
```

`leap.in` 典型内容（**注意顺序：先保存 dry 拓扑和独立组分拓扑，再溶剂化**）：
- `source leaprc.protein.ff19SB`（或 ff14SB）
- `source leaprc.water.opc`（或 TIP4P）
- `source leaprc.gaff2`（如有小分子）
- `loadamberparams frcmod.ionslm_126_opc`  （加载离子参数，OPC 兼容此离子参数文件）
- `loadamberprep ligand.prepin` + `loadamberparams ligand.frcmod`（如有）
- `protein/ligand = loadpdb <file>` 加载结构
- `check protein/ligand` 检查参数完整性
- `saveamberparm protein protein.top protein.crd`（**MM-PBSA 需要**）
- `saveamberparm ligand ligand.top ligand.crd`（**MM-PBSA 需要**）
- `comp = combine { protein ligand }` 构建复合物
- `saveamberparm comp comp_dry.top comp_dry.crd` **← 必须在溶剂化前保存真空拓扑**
- `solvateoct comp TIP3PBOX 10.0` 添加水盒子（缓冲≥8 Å）
- `addions2 comp Na+ 0` 或 `addions2 comp Cl- 0` 中和电荷
- `saveamberparm comp comp_oct.top comp_oct.crd` 保存溶剂化体系（模拟用）
- `savepdb comp comp_oct.pdb` 保存可视结构
- `quit`

**为什么这个顺序重要？** `comp_dry.top` 必须在 `solvateoct` 之前保存，否则会包含水和离子的原子，导致 cpptraj 分析时拓扑与去水轨迹原子数不匹配（典型错误：`Number of atoms in NetCDF file (306) does not match number in associated topology (6847)`）。`protein.top` 和 `ligand.top` 为 MM-PBSA 计算提供独立组分的拓扑。

**执行后检查 tleap 输出**：搜索 `ERROR` 关键字。如有 ERROR，根据 `references/troubleshooting.md` 修正后重新运行。Warning 可接受。

### 1.4 构建完成检查清单

- [ ] `check` 输出无 ERROR（Warning 可接受）
- [ ] 体系净电荷为 0（`addions2` 已中和）
- [ ] 水盒子缓冲距离 ≥ 8 Å
- [ ] 残基名称一致（prepin vs PDB）
- [ ] 输出文件存在：`comp_oct.top`, `comp_oct.crd`, `comp_oct.pdb`, `comp_dry.top`, `comp_dry.crd`

---

## 阶段 2：模拟运行

参考 `references/input-templates.md` 获取完整参数注释。模拟分四个步骤顺序执行，每步生成控制文件 + 运行命令 + (可选) Slurm/PBS 脚本。

### 2.1 能量优化（三步）

**为什么分三步？** 逐步释放约束可以避免结构剧烈变化导致优化失败。先让溶剂适应蛋白环境，再调整氢原子（最轻的原子），最后全原子自由优化。

| 步骤 | 文件 | 约束范围 | 说明 |
|------|------|----------|------|
| min1 | `min1.in` | `'!:WAT,Na+,Cl-'` (restraint_wt=500) | 只优化溶剂和离子 |
| min2 | `min2.in` | `'(!:WAT,Na+,Cl-) & (!@H=)'` (restraint_wt=500) | 额外释放氢原子 |
| min3 | `min3.in` | ntr=0（无约束） | 全原子自由优化 |

公共参数：`imin=1, ncyc=500, maxcyc=1000, drms=0.001, ntb=1, ntpr=100, ntwr=500`

运行命令格式（以 GPU 为例）：
```bash
pmemd.cuda -O -i min1.in -o min1.out -p comp_oct.top -c comp_oct.crd -r min1.rst -x min1.mdcrd -ref comp_oct.crd
pmemd.cuda -O -i min2.in -o min2.out -p comp_oct.top -c min1.rst -r min2.rst -x min2.mdcrd -ref min1.rst
pmemd.cuda -O -i min3.in -o min3.out -p comp_oct.top -c min2.rst -r min3.rst -x min3.mdcrd -ref min2.rst
```

### 2.2 升温 (Heating, 0K → 300K, 50 ps)

**为什么用 Langevin 控温？** Langevin 动力学 (ntt=3) 通过随机碰撞模拟热浴效应，升温过程更平缓稳定，比 Berendsen 控温更符合统计力学。

关键参数：`imin=0, irest=0, ntx=1, nstlim=25000, dt=0.002, ntc=2, ntf=2, ntb=1`
控温：`ntt=3, gamma_ln=2.0, tempi=0.0, temp0=300.0`
约束：`ntr=1, restraintmask='!:WAT,Na+,Cl-', restraint_wt=2.0`
升温控制：`nmropt=1` + `&wt TYPE='TEMP0', istep1=0, istep2=25000, value1=0.1, value2=300.0`

命令：
```bash
pmemd.cuda -O -i heat.in -o heat.out -p comp_oct.top -c min3.rst -r heat.rst -x heat.mdcrd -ref min3.rst
```

### 2.3 恒压平衡 (Density, NPT, 50 ps)

让体系密度达到实验值（~1.0 g/cm³），水分子充分填充蛋白表面空腔。

关键参数：`irest=1, ntx=5, ntb=2, ntp=1, taup=1.0, pres0=1.0`
其余同升温阶段，`restraint_wt=2.0`（轻约束蛋白和配体）

命令：
```bash
pmemd.cuda -O -i density.in -o density.out -p comp_oct.top -c heat.rst -r density.rst -x density.mdcrd -ref heat.rst
```

### 2.4 生产模拟 (Production MD, NPT, 1 ns)

关键参数：`nstlim=500000, dt=0.002, ntb=2, ntp=1, taup=2.0`
**轨迹输出改用 NetCDF 格式**：`ntwx=500, ioutfm=1`（.nc 文件更紧凑，cpptraj 处理更快）
无约束（ntr=0），无 nmropt。

命令：
```bash
pmemd.cuda -O -i product.in -o product.out -p comp_oct.top -c density.rst -r product.rst -x product.nc
```

### 2.5 生成运行脚本

根据用户调度器生成批量运行脚本。bash 脚本将四条命令串联；Slurm/PBS 脚本包含 `#SBATCH`/`#PBS` 头（分区、节点、核心数、walltime）。

### 2.6 重要提醒

- **用户自行运行**，Claude 不执行模拟
- GPU（RTX 5090）：1 ns ≈ 5 分钟；CPU 单核：1 ns ≈ 5 小时
- 提醒用户运行前检查磁盘空间（1 ns NetCDF 轨迹约 200 MB）
- `irest=1, ntx=5` 的搭配表示热重启（读取速度和盒子信息），`irest=0, ntx=1` 表示冷启动

---

## 阶段 3：结果分析

参考 `references/analysis.md` 获取完整的 cpptraj 命令和 Python 绘图代码。

### 3.1 轨迹预处理

分析前先去除溶剂和离子、居中、成像。所有 cpptraj 输入文件中的路径均相对于 `analysis/<模块>/` 子目录：

```bash
# analysis/strip/strip.in
parm ../../prep/comp_dry.top
trajin ../../md/product.nc
strip :WAT,:Na+,:Cl-
center :1-20 mass
image center familiar
rms reference first
trajout strip.nc netcdf
```

运行：`cd analysis/strip && cpptraj -i strip.in`

**重要**：`parm` 必须用 `comp_dry.top`（真空拓扑），不能用 `comp_oct.top`。后续所有分析模块（rmsd/sasa/pca/cluster 等）的 `parm` 也用 `../../prep/comp_dry.top`，`trajin` 用 `../strip/strip.nc`。

### 3.2 分析模块路由

根据用户需求，引导到对应分析模块：

| 分析类型 | 核心工具 | 输出 |
|----------|----------|------|
| 热力学稳定性 | `scripts/process_mdout.perl`（技能自带）+ matplotlib | TEMP/DENSITY/ETOT 时间曲线 |
| RMSD | cpptraj `rms` 命令 | 骨架/全原子 RMSD 时间曲线 |
| RMSF / 回旋半径 | cpptraj `atomicfluct` / `radgyr` | 残基波动幅度 / Rg 时间曲线 |
| SASA / DSSP | cpptraj `surf` / `secstruct` | 溶剂可及表面积 / 二级结构占比 |
| 氢键分析 | cpptraj `hbond` 命令 | 氢键数目/占据率时间曲线 |
| 距离/角度 | cpptraj `distance` / `angle` | 特定原子对的距离/角度 |
| 聚类分析 | cpptraj `cluster` (kmeans/hieragglo/dbscan) | 代表构象 PDB + 聚类分布 |
| PCA | cpptraj `crdaction` + `diagmatrix` + `projection` | PC 方差 + 投影轨迹 |
| 自由能景观 | Python matplotlib (PC1-PC2 2D 直方图) | ΔG = -RT ln(P/Pmax) 图 |
| MM-PBSA/GBSA | `MMPBSA.py` + 输入文件 | 结合自由能 (ΔG_binding) — **仅蛋白-配体/蛋白-蛋白体系** |

### 3.3 执行分析

**Claude 直接执行 cpptraj 和 Python 绘图**（这些命令秒至分钟级完成）。

对每项分析：
1. 编写 **cpptraj 输入文件**（如 `rmsd.in`, `hbond.in`, `pca.in`），用 Bash 执行 `cpptraj -i xxx.in`
2. 编写 **Python 绘图脚本**（matplotlib/seaborn），用 Bash 执行 `python plot_xxx.py`
3. 向用户展示生成的图表，并简要解读结果

**关键注意事项（常见踩坑）**：

- **PCA 必须分两步执行**：`diagmatrix` 是分析命令（在 `run` 后才执行），但 `projection` 命令在解析阶段就检查 eigenvector 数据集是否存在。因此不能在同一次 cpptraj 调用中同时使用 `diagmatrix` 和 `projection`。正确做法：
  - 第一步：`matrix covar ...` + `diagmatrix ...` + `run` → 生成 `evecs.dat`
  - 第二步：`projection evecs evecs.dat out proj.dat @CA beg 1 end 2` + `run`（直接从文件读取 eigenvectors，无需 `readdata`）

- **聚类 `repout` 必须并入主命令**：`cluster C0 kmeans ... repout rep repframe out cnumvtime.dat ...` 放在同一条命令中，不能分开写成两条 `cluster C0 ...` 命令。

- **氢键可能为空**：当蛋白-配体间无稳定氢键时，cpptraj 输出 `Warning: Set 'HBOND[UU]' contains no data`。这不一定是错误，需如实报告"未检测到稳定氢键"。

- **cnumvtime.dat 可能为空**：如聚类失败（算法选择或参数问题），检查 cpptraj 输出中的 Warning。

- **热力学 DENSITY 文件可能只有 1 列**：`process_mdout.perl` 对不同输出文件生成不同列数。Python 脚本需检查 `data.shape[1]`。

- **evecs.dat 格式特殊**：第一行是文件头（`Eigenvector file: ...`），第二行是矩阵维度，之后每个 eigenvector 先有一行 `序号 特征值`，再是多行分量，以 `****` 分隔。不能用 `pd.read_csv` 直接读取。Python 脚本需手动解析。

- **MM-PBSA/GBSA 仅适用于复合物体系**：纯蛋白体系无结合自由能可算，运行前须确认体系类型为蛋白-配体或蛋白-蛋白复合物。计算方法为 ΔG_binding = G_complex − G_protein − G_ligand，必须有受体和配体两个独立组分。

- **MM-PBSA 需要独立组分拓扑**：运行 `MMPBSA.py` 需要 `-sp comp_oct.top -cp comp_dry.top -rp protein.top -lp ligand.top`。`protein.top` 和 `ligand.top` 必须在阶段 1 的 `leap.in` 中提前保存。

---

## 阶段 4：排错

参考 `references/troubleshooting.md` 获取完整排错指南。基本策略：

1. **定位阶段**：根据错误发生时机定位（体系构建 / 能量优化 / 动力学 / 分析）
2. **匹配症状**：在 troubleshooting.md 中按关键字搜索错误信息
3. **排查原因**：常见原因包括残基名不匹配、参数缺失、SHAKE 失败、盒子体积崩溃、拓扑/轨迹不匹配
4. **应用解决方案**：按文档建议逐步修复，修复后从失败步骤重新开始

常见快速修复：
- `antechamber` 原子类型缺失 → 检查输入分子结构完整性，或尝试 `-at gaff2`
- LEaP `check` ERROR → 确认 prepin 残基名与 PDB 一致
- SHAKE 失败 (vlimit exceeded) → 降低 dt 至 1 fs，或增加优化步数
- 能量漂移 → 检查盒子尺寸是否足够（≥8 Å），或降低截断值

---

## 输出规范

生成的文件按以下目录结构组织：

```
workdir/
├── prep/                  # 体系构建输出
│   ├── leap.in            # LEaP 自动化脚本
│   ├── ligand.prepin      # 小分子 prep 参数
│   ├── ligand.frcmod      # 小分子力场修正
│   ├── comp_oct.top       # 溶剂化体系拓扑
│   └── comp_oct.crd       # 溶剂化体系坐标
├── md/                    # 模拟输入文件和运行脚本
│   ├── min1.in / min2.in / min3.in
│   ├── heat.in
│   ├── density.in
│   ├── product.in
│   └── run.sh / run.slurm / run.pbs
└── analysis/              # 分析脚本
    ├── strip.in           # 轨迹预处理
    ├── rmsd/
    │   ├── rmsd.in
    │   └── plot_rmsd.py
    ├── mmpbsa/
    │   ├── mmgbsa.in
    │   └── run_mmpbsa.sh
    ├── pca/
    │   ├── pca.in
    │   └── plot_fel.py
    └── ...
```

**文件命名约定**：遵循 Amber 社区惯例——输入文件用 `.in`，输出文件与输入同名不同扩展名（`min1.in` → `min1.out`, `min1.rst`, `min1.mdcrd`），拓扑 `.top`，坐标 `.crd`，NetCDF 轨迹 `.nc`。

---

## 引用

- 教程（权威参考）：`手把手教你做Amber分子动力学模拟.md`
- 力场选型：`references/force-fields.md`
- 输入模板与运行脚本：`references/input-templates.md`
- 分析命令与绘图：`references/analysis.md`
- 排错指南：`references/troubleshooting.md`
- 官方文档：Amber26 手册 (`Amber26.pdf`)
