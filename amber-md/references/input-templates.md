# Amber 分子动力学模拟输入文件模板

> 来源：[手把手教你做Amber分子动力学模拟](E:\writting\amber-skill\手把手教你做Amber分子动力学模拟.md)
> 所有模板均使用 `&cntrl ... /` 的 namelist 格式。

---

## 1. 能量优化模板

### min1.in -- 优化溶剂分子

```
Hold solute and minimize water only
 &cntrl
  imin = 1, ncyc = 500, maxcyc = 1000, drms = 0.001,
  ntb = 1, ntr = 1, ntpr = 100, ntwr = 500, ntwx = 500,
  restraint_wt = 500, restraintmask='!:WAT,Na+,Cl-'
 /
```

**参数说明：**

| 参数 | 值 | 含义 |
|------|-----|------|
| `imin=1` | 1 | 执行能量优化（非动力学） |
| `ncyc=500` | 500 | 最陡下降法步数，快速收敛 |
| `maxcyc=1000` | 1000 | 最大总优化步数（最陡下降 + 共轭梯度） |
| `drms=0.001` | 0.001 | 能量梯度均方根收敛判据（kcal/mol·Å） |
| `ntb=1` | 1 | 恒容周期性边界条件 |
| `ntr=1` | 1 | 开启位置约束（需配合 restraintmask） |
| `ntpr=100` | 100 | 每 100 步输出一次信息到 .out 文件 |
| `ntwr=500` | 500 | 每 500 步写入一次重启文件 |
| `ntwx=500` | 500 | 每 500 步写入一次轨迹坐标 |
| `restraint_wt=500` | 500 | 约束力常数（kcal/mol·Å²），数值越大约束越强 |
| `restraintmask` | `'!:WAT,Na+,Cl-'` | 约束**除**水分子和离子外的所有原子（即只优化溶剂） |

### min2.in -- 优化氢原子

```
Minimize water and hydrogen
 &cntrl
  imin = 1, ncyc = 500, maxcyc = 1000, drms = 0.001,
  ntb = 1, ntr = 1, ntpr = 100, ntwr = 500, ntwx = 500,
  restraint_wt = 500, restraintmask='(!:WAT,Na+,Cl-) & (!@H=)'
 /
```

**与 min1.in 的区别：** restraintmask 变为 `'(!:WAT,Na+,Cl-) & (!@H=)'`，即约束除水分子、离子**和氢原子**之外的所有原子，只允许氢原子自由优化。

### min3.in -- 全原子优化

```
Minimize all
 &cntrl
  imin = 1, ncyc = 500, maxcyc = 1000, drms = 0.001,
  ntb = 1, ntr = 0, ntpr = 100, ntwr = 500, ntwx = 500,
 /
```

**与 min2.in 的区别：** `ntr=0`，不再约束任何原子，对整个体系进行全原子优化。无需 restraint_wt 和 restraintmask。

---

## 2. 升温模板

### heat.in -- 0K → 300K 升温

```
heat lsez apo
 &cntrl
  imin=0, irest=0, ntx=1, nstlim=25000, dt=0.002,
  ntc=2, ntf=2, cut=8.0, ntb=1,
  ntpr=500, ntwx=500, ntt=3, gamma_ln=2.0,
  tempi=0.0, temp0=300.0, ntr=1, restraintmask='!:WAT,Na+,Cl-',
  restraint_wt=2.0, nmropt=1
 /
 &wt TYPE='TEMP0', istep1=0, istep2=25000,
  value1=0.1, value2=300.0, /
 &wt TYPE='END' /
```

**新增参数说明：**

| 参数 | 值 | 含义 |
|------|-----|------|
| `imin=0` | 0 | 执行动力学模拟（非能量优化） |
| `irest=0` | 0 | 开始新的模拟，不读取速度 |
| `ntx=1` | 1 | 仅读取原子坐标，不读取速度（新模拟） |
| `nstlim=25000` | 25000 | 总模拟步数（25,000 × 0.002 ps = 50 ps） |
| `dt=0.002` | 0.002 | 积分步长 2 fs（SHAKE 约束含 H 键后可用） |
| `ntc=2` | 2 | 使用 SHAKE 算法约束含氢原子的键 |
| `ntf=2` | 2 | 忽略含氢原子键的相互作用计算 |
| `cut=8.0` | 8.0 | 非键相互作用截断值（Å） |
| `ntt=3` | 3 | 使用 Langevin 动力学控制温度 |
| `gamma_ln=2.0` | 2.0 | Langevin 碰撞频率（ps⁻¹） |
| `tempi=0.0` | 0.0 | 初始温度（K） |
| `temp0=300.0` | 300.0 | 目标温度（K） |
| `nmropt=1` | 1 | 启用 NMR 选项，允许自定义温度变化 |
| `restraint_wt=2.0` | 2.0 | 升温过程使用较轻的约束 |

**`&wt` 温度控制块说明：**
- `TYPE='TEMP0'`：指定控制目标为温度
- `istep1=0, istep2=25000`：从第 0 步到第 25000 步线性变化
- `value1=0.1, value2=300.0`：温度从 0.1 K 均匀升至 300.0 K
- `&wt TYPE='END' /`：结束升温控制定义

---

## 3. NPT 平衡模板

### density.in -- 密度平衡

```
equ solvent
 &cntrl
  imin = 0, irest = 1, ntx = 5, nstlim = 25000, dt = 0.002,
  ntc = 2, ntf = 2, cut = 8.0, ntb = 2, ntp = 1, taup = 1.0,
  pres0 = 1.0, ntt = 3, gamma_ln = 2.0, temp0 = 300.0,
  ntpr = 500, ntwx = 500, ntwr = 500,
  ntr=1, restraintmask='!:WAT,Na+,Cl-', restraint_wt=2.0,
 /
```

**新增与变化参数：**

| 参数 | 值 | 含义 |
|------|-----|------|
| `irest=1` | 1 | 延续上一步模拟（读取坐标和速度） |
| `ntx=5` | 5 | 读取原子速度、坐标和周期边界盒子信息 |
| `ntb=2` | 2 | 恒压周期性边界条件 |
| `ntp=1` | 1 | 使用等方性位置缩放维持压强（Berendsen 恒压器） |
| `taup=1.0` | 1.0 | 压强耦合常数（ps） |
| `pres0=1.0` | 1.0 | 目标压强（bar） |

---

## 4. 生产模拟模板

### product.in -- NPT 生产 1 ns

```
NPT equilibration and production
 &cntrl
  imin = 0, irest = 1, ntx = 5,
  ntb = 2, pres0 = 1.0, ntp = 1, taup = 2.0,
  cut = 8, ntc = 2, ntf = 2,
  tempi = 300.0, temp0 = 300.0, ntt = 3, gamma_ln = 2.0,
  nstlim = 500000, dt = 0.002,
  ntpr = 500, ntwx = 500, ntwr = 500
 /
```

**关键设定：**
- `nstlim=500000` + `dt=0.002`：500,000 × 0.002 ps = 1000 ps = **1 ns**
- `ntpr/ntwx/ntwr=500`：每 500 步（500 × 0.002 = 1 ps）输出一次
- `taup=2.0`：生产模拟中压强耦合常数放宽到 2.0 ps
- **不约束任何原子**（无 ntr/restraintmask），体系完全自由运动

---

## 5. LEaP 自动化模板

### leap.in

```
source leaprc.protein.ff19SB
source leaprc.water.tip3p
source leaprc.gaff2
loadamberprep ligand.prepin
loadamberparams ligand.frcmod
protein = loadpdb 1L2Y-1.pdb
check protein
saveamberparm protein protein.top protein.crd
ligand = loadpdb ligand.pdb
check ligand
saveamberparm ligand ligand.top ligand.crd
comp = combine { protein ligand }
savepdb comp comp_dry.pdb
saveamberparm comp comp_dry.top comp_dry.crd
solvateoct comp TIP3PBOX 10.0
addions2 comp Cl- 0
savepdb comp comp_oct.pdb
saveamberparm comp comp_oct.top comp_oct.crd
quit
```

**运行方式：** `tleap -f leap.in`

**逐行说明：**

| 命令 | 说明 |
|------|------|
| `source leaprc.protein.ff19SB` | 加载 FF19SB 蛋白力场 |
| `source leaprc.water.tip3p` | 加载 TIP3P 水模型 |
| `source leaprc.gaff2` | 加载 GAFF2 小分子力场 |
| `loadamberprep ligand.prepin` | 加载小分子 prepin 文件（原子类型/电荷） |
| `loadamberparams ligand.frcmod` | 加载小分子力场修正参数 |
| `protein = loadpdb 1L2Y-1.pdb` | 读入蛋白 PDB 结构 |
| `check protein` | 检查蛋白结构完整性 |
| `saveamberparm protein ...` | 保存蛋白的拓扑和坐标文件 |
| `ligand = loadpdb ligand.pdb` | 读入配体 PDB 结构 |
| `check ligand` | 检查配体结构完整性 |
| `saveamberparm ligand ...` | 保存配体的拓扑和坐标文件 |
| `comp = combine { protein ligand }` | 合并蛋白和配体为复合物 |
| `savepdb comp comp_dry.pdb` | 保存真空复合物 PDB（用于 PyMOL 查看） |
| `saveamberparm comp comp_dry.top comp_dry.crd` | 保存真空复合物拓扑和坐标（后续分析用） |
| `solvateoct comp TIP3PBOX 10.0` | 添加 TIP3P 水盒子，八面体形状，溶剂层厚度 10 Å |
| `addions2 comp Cl- 0` | 添加 Cl⁻ 离子中和体系电荷（0 表示自动中和） |
| `savepdb comp comp_oct.pdb` | 保存溶剂化体系 PDB |
| `saveamberparm comp comp_oct.top comp_oct.crd` | 保存溶剂化体系拓扑和坐标（**模拟用**） |
| `quit` | 退出 LEaP |

---

## 6. 运行命令模板

### GPU 版

```bash
pmemd.cuda -O \
  -i {input}.in \
  -o {output}.out \
  -p comp_oct.top \
  -c {coord}.rst \
  -r {restart}.rst \
  -x {traj}.mdcrd \
  [-ref {ref}.rst]
```

### CPU 并行版

```bash
mpirun -np {N} pmemd.MPI -O \
  -i {input}.in \
  -o {output}.out \
  -p comp_oct.top \
  -c {coord}.rst \
  -r {restart}.rst \
  -x {traj}.mdcrd \
  [-ref {ref}.rst]
```

**命令参数说明：**

| 参数 | 含义 |
|------|------|
| `-O` | 覆盖所有同名输出文件 |
| `-i` | 指定控制文件 (.in) |
| `-o` | 输出模拟过程信息 (.out) |
| `-p` | 指定拓扑文件 (.top) |
| `-c` | 指定初始坐标文件 (.rst 或 .crd) |
| `-r` | 输出新的 restart 文件（坐标+速度）(.rst) |
| `-x` | 输出轨迹文件 (.mdcrd 或 .nc) |
| `-ref` | 参考坐标（仅在 ntr=1 时需要） |
| `[-ref]` | 方括号表示可选参数 |

### 完整运行命令序列

```bash
# 能量优化第一步：优化溶剂
pmemd.cuda -O -i min1.in -o min1.out -p comp_oct.top \
  -c comp_oct.crd -r min1.rst -x min1.mdcrd -ref comp_oct.crd

# 能量优化第二步：优化氢原子
pmemd.cuda -O -i min2.in -o min2.out -p comp_oct.top \
  -c min1.rst -r min2.rst -x min2.mdcrd -ref min1.rst

# 能量优化第三步：全原子优化
pmemd.cuda -O -i min3.in -o min3.out -p comp_oct.top \
  -c min2.rst -r min3.rst -x min3.mdcrd -ref min2.rst

# 升温：0 K → 300 K
pmemd.cuda -O -i heat.in -o heat.out -p comp_oct.top \
  -c min3.rst -r heat.rst -x heat.mdcrd -ref min3.rst

# NPT 密度平衡
pmemd.cuda -O -i density.in -o density.out -p comp_oct.top \
  -c heat.rst -r density.rst -x density.mdcrd -ref heat.rst

# 生产模拟：NPT 1 ns
pmemd.cuda -O -i product.in -o product.out -p comp_oct.top \
  -c density.rst -r product.rst -x product.nc
```

### Slurm 脚本模板

```bash
#!/bin/bash
#SBATCH --job-name=amber_md
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --partition=gpu
#SBATCH --output=amber_md_%j.out
#SBATCH --error=amber_md_%j.err

module load amber/26
module load cuda/12.0

# 能量优化
pmemd.cuda -O -i min1.in -o min1.out -p comp_oct.top -c comp_oct.crd -r min1.rst -x min1.mdcrd -ref comp_oct.crd
pmemd.cuda -O -i min2.in -o min2.out -p comp_oct.top -c min1.rst -r min2.rst -x min2.mdcrd -ref min1.rst
pmemd.cuda -O -i min3.in -o min3.out -p comp_oct.top -c min2.rst -r min3.rst -x min3.mdcrd -ref min2.rst

# 升温
pmemd.cuda -O -i heat.in -o heat.out -p comp_oct.top -c min3.rst -r heat.rst -x heat.mdcrd -ref min3.rst

# NPT 平衡
pmemd.cuda -O -i density.in -o density.out -p comp_oct.top -c heat.rst -r density.rst -x density.mdcrd -ref heat.rst

# 生产模拟
pmemd.cuda -O -i product.in -o product.out -p comp_oct.top -c density.rst -r product.rst -x product.nc
```

### PBS 脚本模板

```bash
#!/bin/bash
#PBS -N amber_md
#PBS -l nodes=1:ppn=8:gpus=1
#PBS -l walltime=24:00:00
#PBS -q gpu
#PBS -o amber_md.out
#PBS -e amber_md.err

cd $PBS_O_WORKDIR
module load amber/26
module load cuda/12.0

# 能量优化
pmemd.cuda -O -i min1.in -o min1.out -p comp_oct.top -c comp_oct.crd -r min1.rst -x min1.mdcrd -ref comp_oct.crd
pmemd.cuda -O -i min2.in -o min2.out -p comp_oct.top -c min1.rst -r min2.rst -x min2.mdcrd -ref min1.rst
pmemd.cuda -O -i min3.in -o min3.out -p comp_oct.top -c min2.rst -r min3.rst -x min3.mdcrd -ref min2.rst

# 升温
pmemd.cuda -O -i heat.in -o heat.out -p comp_oct.top -c min3.rst -r heat.rst -x heat.mdcrd -ref min3.rst

# NPT 平衡
pmemd.cuda -O -i density.in -o density.out -p comp_oct.top -c heat.rst -r density.rst -x density.mdcrd -ref heat.rst

# 生产模拟
pmemd.cuda -O -i product.in -o product.out -p comp_oct.top -c density.rst -r product.rst -x product.nc
```

> **注意：** CPU 并行版请将 `pmemd.cuda` 替换为 `mpirun -np {N} pmemd.MPI`。

---

## 7. 关键参数速查表

### 模拟控制

| 参数 | 含义 | 常见取值 |
|------|------|----------|
| `imin` | 任务类型 | `0`=动力学模拟 / `1`=能量优化 |
| `irest` / `ntx` | 重启控制 | `0,1`=新模拟（仅读坐标）/ `1,5`=续跑（读坐标+速度+盒子） |
| `nstlim` | 总模拟步数 | 升温/平衡 25000; 生产 500000（1 ns） |
| `dt` | 积分步长（ps） | `0.001`=1 fs 无 SHAKE / `0.002`=2 fs 含 SHAKE |
| `ntpr` | 输出频率（步） | `100`（能量优化）/ `500`（动力学） |
| `ntwx` | 轨迹写入频率（步） | `500`=每 1 ps 保存一帧 |
| `ntwr` | 重启文件写入频率（步） | `500` |

### 温度控制

| 参数 | 含义 | 常见取值 |
|------|------|----------|
| `ntt` | 温度控制方法 | `3`=Langevin 动力学 |
| `gamma_ln` | Langevin 碰撞频率（ps⁻¹） | `1.0`~`5.0`，常用 `2.0` |
| `tempi` | 初始温度（K） | 新模拟 `0.0`；续跑 `300.0` |
| `temp0` | 目标温度（K） | `300.0`（室温） |
| `nmropt` | NMR 选项开关 | `0`=关闭 / `1`=启用（升温控制需要） |

### 压强控制

| 参数 | 含义 | 常见取值 |
|------|------|----------|
| `ntp` | 压强控制方法 | `0`=无压控 / `1`=各向同性 Berendsen 缩放 |
| `taup` | 压强耦合常数（ps） | 平衡用 `1.0`；生产用 `2.0` |
| `pres0` | 目标压强（bar） | `1.0`（常压） |

### 边界条件

| 参数 | 含义 | 常见取值 |
|------|------|----------|
| `ntb` | 周期边界条件 | `0`=真空 / `1`=恒容 / `2`=恒压 |
| `cut` | 非键截断距离（Å） | `8.0`（默认值） |

### 约束

| 参数 | 含义 | 常见取值 |
|------|------|----------|
| `ntc` / `ntf` | SHAKE 约束 | `1`=无约束 / `2`=约束含 H 键 |
| `ntr` | 位置约束开关 | `0`=无约束 / `1`=施加约束 |
| `restraint_wt` | 约束力常数（kcal/mol·Å²） | `500`=强约束（优化）/ `2.0`=弱约束（升温） |
| `restraintmask` | 约束范围 Amber mask | `'!:WAT,Na+,Cl-'`=约束除溶剂外的所有原子 |

### 能量优化专用

| 参数 | 含义 | 常见取值 |
|------|------|----------|
| `ncyc` | 最陡下降法步数 | `500` |
| `maxcyc` | 最大总优化步数 | `1000`（ncyc + 共轭梯度步数） |
| `drms` | 梯度均方根收敛判据 | `0.001` kcal/mol·Å |
