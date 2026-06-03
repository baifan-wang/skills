# Amber 分子动力学模拟技能

Amber MD 全流程助手。Claude 直接执行体系构建（antechamber/parmchk2/tleap）和轨迹分析（cpptraj + Python 绘图），用户自行运行计算密集的模拟步骤（pmemd.cuda/pmemd.MPI）。

## 适用体系

- 蛋白-配体复合物
- 纯蛋白
- 蛋白-蛋白复合物

## 环境依赖

- AmberTools 26+ (`antechamber`, `parmchk2`, `tleap`, `cpptraj`)
- Amber 26+ (`pmemd.cuda` 或 `pmemd.MPI` 或 `sander`)
- Python 3.7+ (`pandas`, `numpy`, `matplotlib`)
- Perl (`process_mdout.perl` 脚本需要)

## 工作流

| 阶段 | 内容 | 执行者 |
|------|------|--------|
| 0 | 信息收集 | 交互式问答 |
| 1 | 体系构建（antechamber/tleap） | Claude |
| 2 | MD 模拟（优化/升温/平衡/生产） | 用户 |
| 3 | 轨迹分析 + 绘图 | Claude |
| 4 | 排错 | 引导式 |

### 阶段 0 — 信息收集

询问用户：输入文件、体系类型、计算资源（GPU/CPU）、调度器（bash/Slurm/PBS）、模拟时长（默认 1 ns）、分析需求。

**默认设置**：ff19SB + TIP3P + GAFF2 力场，Langevin 控温 (ntt=3, gamma_ln=2.0)，生产模拟 1 ns。

### 阶段 1 — 体系构建

1. 小分子参数化：`antechamber` + `parmchk2`（先确认净电荷）
2. LEaP 构建：编写 `leap.in`，运行 `tleap -f leap.in`

**关键规则**：`comp_dry.top` **必须**在 `solvateoct` 之前保存。顺序错误会导致分析阶段报错 `Number of atoms in NetCDF file does not match topology`。

MM-PBSA 需要额外保存 `protein.top` 和 `ligand.top`。

### 阶段 2 — MD 模拟

生成控制文件和运行脚本：
- `min1.in` / `min2.in` / `min3.in` — 三步能量优化
- `heat.in` — 升温 0K→300K（50 ps，NVT）
- `density.in` — 密度平衡（50 ps，NPT）
- `product.in` — 生产模拟（1 ns，NPT，NetCDF 轨迹）
- `run.sh` — 批量运行脚本

用户自行运行。GPU (RTX 5090) 约 5 分钟/ns，CPU 约 5 小时/ns。

### 阶段 3 — 轨迹分析

| 分析模块 | 工具 | 输出 |
|----------|------|------|
| 热力学 | `process_mdout.perl` + matplotlib | 温度/密度/能量时间曲线 |
| RMSD / RMSF / Rg | cpptraj + matplotlib | 结构稳定性指标 |
| SASA / DSSP | cpptraj + matplotlib | 溶剂可及表面积、二级结构 |
| 氢键 | cpptraj | 氢键数量/占据率 |
| 距离矩阵 | cpptraj + matplotlib | Cα 距离热力图 |
| 聚类 | cpptraj k-means/hieragglo | 代表性构象 |
| PCA | cpptraj（两步法） | 主成分投影 |
| 自由能景观 | matplotlib | ΔG = −RT ln(P/Pmax) |
| MM-PBSA/GBSA | MMPBSA.py | 结合自由能（**仅复合物体系**） |

## 目录结构

```
workdir/
├── prep/                  # 体系构建输出
│   ├── leap.in
│   ├── ligand.prepin / ligand.frcmod
│   ├── comp_oct.top / comp_oct.crd  （溶剂化 — 用于模拟）
│   ├── comp_dry.top / comp_dry.crd  （真空 — 用于分析）
│   ├── protein.top / protein.crd    （MM-PBSA 用）
│   └── ligand.top / ligand.crd      （MM-PBSA 用）
├── md/                    # 模拟输入文件
│   ├── min1.in / min2.in / min3.in
│   ├── heat.in / density.in / product.in
│   └── run.sh
└── analysis/              # 分析脚本与输出
    ├── strip/
    ├── physical/
    ├── rmsd/
    ├── sasa/
    ├── hbond/
    ├── distmat/
    ├── cluster/
    ├── pca/
    ├── fel/
    └── mmpbsa/
```

## 重要规则

### LEaP：先保存真空拓扑，再溶剂化

```tleap
comp = combine { protein ligand }
saveamberparm comp comp_dry.top comp_dry.crd   # ← 在 solvateoct 之前
saveamberparm protein protein.top protein.crd  # ← MM-PBSA 用
saveamberparm ligand ligand.top ligand.crd     # ← MM-PBSA 用
solvateoct comp TIP3PBOX 10.0                  # ← 在 dry 保存之后
```

错误顺序会导致 `comp_dry.top` 包含水和离子原子（~6800 个），与去水轨迹（~300 个）不匹配，cpptraj 报错退出。

### cpptraj：读取输出数据须加 `comment="#"`

所有 cpptraj 输出文件首行为 `#` 注释头。用 `pd.read_csv(..., comment="#", header=None)` 或手动跳过 `#` 行。

### cpptraj：路径相对于 analysis 子目录

```
# analysis/strip/strip.in
parm ../../prep/comp_dry.top
trajin ../../md/product.nc

# analysis/rmsd/rmsd.in
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
```

### PCA：必须分两步执行

第一步：`matrix covar` + `diagmatrix` + `run` → 生成 `evecs.dat`
第二步：`projection evecs evecs.dat out proj.dat @CA beg 1 end 2` + `run`

原因：`diagmatrix` 是分析命令（`run` 之后才执行），而 `projection` 在输入解析阶段就检查 eigenvector 数据集是否存在。同一次调用中 `projection` 看不到 `diagmatrix` 的输出。

### 聚类：repout 须并入主命令

```cpptraj
cluster C0 kmeans clusters 5 randompoint maxit 500 rms @CA sieve 10 \
  repout rep repframe \
  out cnumvtime.dat summary summary.dat info info.dat
```

禁止写成单独的 `cluster C0 repout rep repframe` —— 这会覆盖前面的 `C0` 定义，导致"未指定聚类算法"警告。

### DSSP：宽格式矩阵

cpptraj `secstruct` 输出宽格式矩阵（列 0 = 帧号，列 1-N = 每个残基的整数 SS 码）。SS 码对照：0=None, 1=Parallel β, 2=Antiparallel β, 3=3-10 helix, 4=Alpha helix, 5=Pi helix, 6=Turn, 7=Bend。

```python
dssp_raw = pd.read_csv("dssp.dat", delim_whitespace=True, comment="#", header=None)
ss_data = dssp_raw.iloc[:, 1:].values  # 去掉帧号列
```

### MM-PBSA/GBSA：仅适用于复合物

ΔG_binding = G_complex − G_receptor − G_ligand，必须有受体和配体两个独立组分。纯蛋白体系不适用。

### RMSF：用带圆点线图，不用柱状图

```python
axes.plot(rmsf[0], rmsf[1], marker='o', linewidth=1.0, markersize=4, color='steelblue')
```

### evecs.dat：须手动解析

格式：文件头行 → 矩阵维度行 → 每个模式："序号 特征值" → 多行分量 → "****"分隔。不能用 `pd.read_csv` 直接读。需逐行解析，通过 `len(parts) == 2 and parts[0].isdigit()` 识别特征值行。

### DENSITY 文件可能只有 1 列

`process_mdout.perl` 对不同输出文件生成不同列数。`summary.DENSITY` 有时只有值列（无时间列）。Python 脚本须检查 `data.shape[1]`，单列时用 `np.arange()` 生成 x 轴。

### 氢键为空不一定是错误

蛋白-配体间无稳定氢键时，cpptraj 输出 `Warning: Set 'HBOND[UU]' contains no data`。如实报告"未检测到稳定氢键，结合可能由疏水/π-π 堆积主导"。

## 数据格式速查表

| 文件 | 格式 | 读取方法 |
|------|------|----------|
| `*.dat`（cpptraj 输出） | `#` 头 + 空格分隔 | `pd.read_csv(..., comment="#", header=None)` |
| `evecs.dat` | 自定义（header + `****` 分隔） | 逐行手动解析 |
| `dssp.dat` | 宽矩阵（帧 × 残基） | `pd.read_csv` → `iloc[:, 1:]` |
| `summary.*`（perl 输出） | 空格分隔，列数可变 | 先检查 `shape[1]` |
| `mmgbsa.dat`（MMPBSA.py） | 空格分隔总结统计 | `re.match()` 提取各项 |
| `proj.dat`（cpptraj） | `#Frame Mode1 Mode2` | `pd.read_csv(..., comment="#")` |
| `cnumvtime.dat` | `#Frame C0` | `pd.read_csv(..., comment="#")` |
| `summary.dat`（聚类） | `#Cluster Frames Frac ...` | `pd.read_csv(..., comment="#", header=None, names=[...])` |

## 排错指南

详见 `references/troubleshooting.md`，覆盖：

- antechamber 原子类型/成键参数缺失
- LEaP 电荷/残基/成键警告
- 能量优化不收敛/NaN
- SHAKE 失败/vlimit 超限/能量漂移
- cpptraj 拓扑-轨迹原子数不匹配
- PCA eigenvector 数据集为空
- 聚类算法未识别
- 氢键分析无数据
- Python DataFrame 列/索引错误（来自 cpptraj 输出格式问题）

## 参考文件

- `references/force-fields.md` — 力场选型指南
- `references/input-templates.md` — 所有 `.in` 文件模板及参数说明
- `references/analysis.md` — 完整 cpptraj 命令和 Python 绘图代码
- `references/troubleshooting.md` — 错误诊断与解决方案
- `scripts/process_mdout.perl` — 热力学数据提取脚本
