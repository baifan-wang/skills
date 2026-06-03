# Amber MD 模拟结果分析命令参考

本参考涵盖从轨迹预处理到自由能计算的完整分析流程，基于 TRPcage-吲哚复合物体系（PDB: 1L2Y，蛋白残基 1-20，配体残基 21）。

---

## 1. 轨迹预处理 (strip.in)

去除溶剂和离子，居中、成像、对齐。**所有路径相对于 `analysis/strip/` 子目录。**

```
parm ../../prep/comp_dry.top
trajin ../../md/product.nc
strip :WAT,:Na+,:Cl-
center :1-20 mass
image center familiar
rms reference first
trajout strip.nc netcdf
```

运行：`cd analysis/strip && cpptraj -i strip.in`。注意根据实际体系调整残基范围（`:1-20`）和离子类型。

**为什么必须用 `comp_dry.top`？** 去水后的轨迹不含水和离子原子，若用 `comp_oct.top`（含 ~6800+ 原子）匹配去水轨迹（~300 原子），cpptraj 报错：`Number of atoms in NetCDF file (306) does not match number in associated topology (6847)`。

---

## 2. 热力学数据提取

```bash
mkdir physical && cd physical
# 使用技能自带的 process_mdout.perl（无需单独安装）
cp ../../scripts/process_mdout.perl .
perl process_mdout.perl ../heat.out ../density.out ../product.out
```

输出 `summary.TEMP`、`summary.DENSITY`、`summary.EKTOT`、`summary.EPTOT`、`summary.ETOT`。

```python
# plot_thermo.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

files = {
    "Temperature (K)": "summary.TEMP",
    "Density (g/mL)": "summary.DENSITY",
    "Kinetic Energy (kcal/mol)": "summary.EKTOT",
    "Potential Energy (kcal/mol)": "summary.EPTOT",
    "Total Energy (kcal/mol)": "summary.ETOT",
}

fig, axes = plt.subplots(len(files), 1, figsize=(10, 12), sharex=True)
for ax, (title, fname) in zip(axes, files.items()):
    data = pd.read_csv(fname, delim_whitespace=True, comment="#", header=None)
    # process_mdout.perl 对不同文件生成不同列数；DENSITY 可能只有 1 列
    if data.shape[1] >= 2:
        x, y = data.iloc[:, 0], data.iloc[:, 1]
    else:
        y = data.iloc[:, 0]
        x = np.arange(len(y))
    ax.plot(x, y, linewidth=0.8)
    ax.set_ylabel(title)
    ax.grid(True, alpha=0.3)
axes[-1].set_xlabel("Time (ps)")
plt.tight_layout()
plt.savefig("thermodynamics.png", dpi=150)
```

---

## 3. RMSD + RMSF + Rg (rmsd.in)

```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
rms first mass out rmsd_bb.dat @CA,C,N time 1.0
rms first mass out rmsd_all.dat time 1.0
atomicfluct out rmsf_byres.dat :1-20 byres
atomicfluct out rmsf_bb.dat :1-20@CA,C,N byres
radgyr out rg.dat :1-20
```

运行：`cpptraj -i rmsd.in`

```python
# plot_rmsd_rmsf_rg.py
import pandas as pd
import matplotlib.pyplot as plt

rmsd_bb = pd.read_csv("rmsd_bb.dat", delim_whitespace=True, comment="#", header=None)
rmsd_all = pd.read_csv("rmsd_all.dat", delim_whitespace=True, comment="#", header=None)
rmsf = pd.read_csv("rmsf_byres.dat", delim_whitespace=True, comment="#", header=None)
rg = pd.read_csv("rg.dat", delim_whitespace=True, comment="#", header=None)

fig, axes = plt.subplots(3, 1, figsize=(10, 12))

# RMSD: 时间序列线图
axes[0].plot(rmsd_bb[0], rmsd_bb[1], label="Backbone (CA,C,N)", linewidth=0.8)
axes[0].plot(rmsd_all[0], rmsd_all[1], label="All atoms", linewidth=0.8, alpha=0.7)
axes[0].set_ylabel("RMSD (Å)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# RMSF: dot-line plot per residue
axes[1].plot(rmsf[0], rmsf[1], marker='o', linewidth=1.0, markersize=4,
             color="steelblue")
axes[1].set_ylabel("RMSF (Å)")
axes[1].set_xlabel("Residue")
axes[1].grid(True, alpha=0.3, axis="y")

# Rg: time series
axes[2].plot(rg[0], rg[1], linewidth=0.8, color="darkgreen")
axes[2].set_ylabel("Rg (Å)")
axes[2].set_xlabel("Time (ps)")
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("rmsd_rmsf_rg.png", dpi=150)
```

---

## 4. SASA + DSSP (sasa.in)

```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
molsurf out sasa.dat :1-20
secstruct out dssp.dat :1-20
```

运行：`cpptraj -i sasa.in`

```python
# plot_sasa_dssp.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sasa = pd.read_csv("sasa.dat", delim_whitespace=True, comment="#", header=None)

fig, axes = plt.subplots(2, 1, figsize=(10, 8))

axes[0].plot(sasa[0], sasa[1], linewidth=0.8, color="teal")
axes[0].set_ylabel("SASA (Å²)")
axes[0].grid(True, alpha=0.3)

# DSSP: 宽格式矩阵，列0=帧号，列1-N=每残基整数SS码
# 码: 0=None 1=Para 2=Anti 3=3-10 4=Alpha 5=Pi 6=Turn 7=Bend
dssp_raw = pd.read_csv("dssp.dat", delim_whitespace=True, comment="#", header=None)
ss_data = dssp_raw.iloc[:, 1:].values
frames = dssp_raw.iloc[:, 0].values
ss_types = ["Alpha", "Beta", "3-10", "Turn", "Bend/Coil"]
ss_groups = {0: [4], 1: [1, 2], 2: [3], 3: [6], 4: [0, 5, 7]}
counts = np.zeros((len(frames), len(ss_types)))
for i in range(len(frames)):
    for code in ss_data[i]:
        for g_idx, codes in ss_groups.items():
            if int(code) in codes:
                counts[i, g_idx] += 1
                break
axes[1].stackplot(frames, counts.T, labels=ss_types, alpha=0.7)
axes[1].set_ylabel("Residue Count")
axes[1].set_xlabel("Frame")
axes[1].legend(loc="upper right", fontsize=8)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("sasa_dssp.png", dpi=150)
```

---

## 5. 氢键分析 (hbond.in)

### 5.1 整体氢键占有率

```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
hbond HBOND out hbond.dat :1-20 :21 avgout hbond_avg.dat
```

### 5.2 特定原子对的距离和角度（示例：配体 N1 与 Arg16 O）

```
distance d1 :21@N1 :16@O out dist_N1_O.dat
angle a1 :21@N1 :21@H2 :16@O out angle_N1_H2_O.dat
```

```python
# plot_hbond.py
import pandas as pd
import matplotlib.pyplot as plt

dist = pd.read_csv("dist_N1_O.dat", delim_whitespace=True, comment="#", header=None)
angle = pd.read_csv("angle_N1_H2_O.dat", delim_whitespace=True, comment="#", header=None)

fig, axes = plt.subplots(2, 1, figsize=(10, 8))

axes[0].plot(dist[0], dist[1], linewidth=0.8, color="darkblue")
axes[0].axhline(y=3.5, color="red", linestyle="--", label="H-bond cutoff (3.5 Å)")
axes[0].set_ylabel("Distance (Å)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(angle[0], angle[1], linewidth=0.8, color="darkorange")
axes[1].axhline(y=180, color="gray", linestyle="--", alpha=0.5, label="Ideal angle 180°")
axes[1].set_ylabel("Angle (°)")
axes[1].set_xlabel("Frame")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("hbond_distance_angle.png", dpi=150)
```

---

## 6. 距离矩阵 (distmat.in)

```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
matrix dist @CA out distmat.dat byres
```

```python
# plot_distmat.py
import numpy as np
import matplotlib.pyplot as plt

data = []
with open("distmat.dat", "r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        parts = line.split()
        data.append([float(x) for x in parts[1:]])

mat = np.array(data)
labels = [str(i+1) for i in range(len(mat))]

fig, ax = plt.subplots(figsize=(8, 7))
im = ax.imshow(mat, cmap="coolwarm", aspect="auto")
ax.set_xticks(range(len(mat))); ax.set_xticklabels(labels, fontsize=7)
ax.set_yticks(range(len(mat))); ax.set_yticklabels(labels, fontsize=7)
ax.set_xlabel("Residue"); ax.set_ylabel("Residue")
cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label("Cα Distance (Å)")
plt.tight_layout()
plt.savefig("distmat.png", dpi=150)
```

---

## 7. 聚类分析 (cluster.in)

三种方法示例。**`repout` 必须合并在主 `cluster` 命令中，不能单独写成第二条命令。**

```
# k-means（repout 并入主命令）
cluster C0 kmeans clusters 5 randompoint maxit 500 rms @CA sieve 10 \
  repout rep repframe \
  out cnumvtime.dat summary summary.dat info info.dat

# 层次凝聚聚类（hierarchical agglomerative）
cluster C0 hieragglo clusters 5 rms @CA sieve 10 \
  repout rep repframe \
  out cnumvtime.dat summary summary.dat info info.dat

# DBSCAN
cluster C0 dbscan minpoints 5 epsilon 2.0 rms @CA sieve 10 \
  out cnumvtime.dat summary summary.dat info info.dat
```

```python
# plot_cluster.py
import pandas as pd
import matplotlib.pyplot as plt

cvt = pd.read_csv("cnumvtime.dat", delim_whitespace=True, comment="#", header=None,
                   names=["frame", "cluster"])
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].plot(cvt["frame"], cvt["cluster"], linewidth=0.5, color="purple")
axes[0].set_xlabel("Frame"); axes[0].set_ylabel("Cluster")
axes[0].set_yticks(range(cvt["cluster"].nunique()))
axes[0].grid(True, alpha=0.3)

# summary.dat 首行以 "#" 开头；comment="#" 会跳过该行，需手动指定列名
summary = pd.read_csv("summary.dat", delim_whitespace=True, comment="#", header=None,
                      names=["cluster", "frames", "frac", "avgdist", "stdev", "centroid", "avgcdist"])
colors = plt.cm.Set3(range(len(summary)))
axes[1].pie(summary["frames"], labels=[f"Cluster {int(c)}" for c in summary["cluster"]],
            autopct="%1.1f%%", colors=colors, startangle=90)
axes[1].set_title("Cluster Population")

plt.tight_layout()
plt.savefig("cluster_analysis.png", dpi=150)
```

---

## 8. PCA 主成分分析 — 两步流程

**为什么必须分两步？** `diagmatrix` 是分析命令（在 `run` 后才执行），但 `projection` 在输入解析阶段就检查 eigenvector 数据集是否存在。同一次 cpptraj 调用中 `projection` 看不到 `diagmatrix` 的输出。两步法：第一步计算 eigenvector 并写入文件，第二步从文件读取并投影。

### 第一步：计算协方差矩阵 + 对角化

```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
rms first @CA
matrix covar @CA name covar
diagmatrix covar out evecs.dat vecs 50 name evecs
run
```

运行后生成 `evecs.dat`（含 eigenvector 和 eigenvalue）。

### 第二步：投影到 PC1-PC2

```
parm ../../prep/comp_dry.top
trajin ../strip/strip.nc
rms first @CA
projection evecs evecs.dat out proj.dat @CA beg 1 end 2
run
```

**关键**：`projection` 直接从 `evecs.dat` 文件读取（不需 `readdata`），语法为 `projection evecs <filename> out <output> <mask> beg <n> end <m>`。

运行后生成 `proj.dat`（列：Frame, Mode1, Mode2）。

```python
# plot_pca.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

proj = pd.read_csv("proj.dat", delim_whitespace=True, comment="#",
                   names=["frame", "PC1", "PC2"])

# evecs.dat 格式特殊：第一行是文件头字符串，第二行是矩阵维度，
# 之后每组: "序号 特征值" → 多行分量 → "****" 分隔。需手动解析。
evals = []
with open("evecs.dat", "r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("****") or not line:
            continue
        if line.startswith("Eigenvector") or line[0].isdigit() and len(line.split()) == 2:
            continue  # skip header and dimension line
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit():
            evals.append(float(parts[1]))

evals = np.array(evals[:50])
if len(evals) == 0:
    evals = np.array([1.0])
var_pct = evals / evals.sum() * 100

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

sc = axes[0].scatter(proj["PC1"], proj["PC2"], c=proj["frame"],
                     cmap="viridis", s=3, alpha=0.6)
axes[0].set_xlabel(f"PC1 ({var_pct[0]:.1f}%)")
axes[0].set_ylabel(f"PC2 ({var_pct[1]:.1f}%)")
plt.colorbar(sc, ax=axes[0], label="Frame")

top_n = min(20, len(var_pct))
axes[1].bar(range(1, top_n+1), var_pct[:top_n], color="steelblue", edgecolor="white")
axes[1].set_xlabel("Principal Component"); axes[1].set_ylabel("Variance Explained (%)")
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("pca_analysis.png", dpi=150)
```

---

## 9. 自由能景观（基于 PCA 投影）

```python
# plot_free_energy.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

proj = pd.read_csv("../pca/proj.dat", delim_whitespace=True, comment="#",
                   names=["frame", "PC1", "PC2"])
pc1 = proj["PC1"].values.astype(np.float64)
pc2 = proj["PC2"].values.astype(np.float64)

H, xedges, yedges = np.histogram2d(pc1, pc2, bins=50)
P = H / H.sum()
with np.errstate(divide="ignore"):
    G = -0.001987 * 300 * np.log(P / P.max())
    G[G > 10] = 10
    G[~np.isfinite(G)] = 10

fig, ax = plt.subplots(figsize=(8, 6))
# levels 必须是显式数组（不是单个整数），matplotlib 3.x 中 contourf 的 levels=20 会报错
levels = np.linspace(0, 10, 21)
cf = ax.contourf(xedges[:-1], yedges[:-1], G.T, levels=levels, cmap="viridis")
cs = ax.contour(xedges[:-1], yedges[:-1], G.T, levels=10, colors="white", linewidths=1)
ax.clabel(cs, inline=True, fontsize=7, fmt="%.1f")
cbar = plt.colorbar(cf, ax=ax)
cbar.set_label("ΔG (kcal/mol)")
ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
ax.set_title("Free Energy Landscape (300 K)")
plt.tight_layout()
plt.savefig("free_energy_landscape.png", dpi=150)
```

---

## 10. MM-PBSA / MM-GBSA 结合自由能 (mmgbsa.in)

**适用范围**：仅蛋白-配体复合物或蛋白-蛋白复合物体系。纯蛋白体系无结合对象，MM-PBSA/GBSA 不适用。结合自由能 = G_complex − G_receptor − G_ligand，依赖两个独立组分的能量差。

**前置条件**：阶段 1 的 `leap.in` 中必须保存 `protein.top` 和 `ligand.top`（独立组分拓扑）。

输入文件：

```
Input file for running PB and GB
&general
  interval=5, verbose=1, startframe=21, endframe=1000
/
&gb
  igb=5, saltcon=0.100
/
```

运行命令（从 `analysis/mmpbsa/` 目录）：

```bash
MMPBSA.py -O -i mmgbsa.in -o mmgbsa.dat -sp ../../prep/comp_oct.top \
  -cp ../../prep/comp_dry.top -rp ../../prep/protein.top -lp ../../prep/ligand.top -y ../../md/product.nc
```

结果解读：`DELTA TOTAL` 即为结合自由能 (kcal/mol)。负值表示有利结合。

**数据格式注意**：`mmgbsa.dat` 中的总结统计是空格分隔（非逗号），格式为：
```
DELTA TOTAL                -16.0897                4.0117              0.2865
```
Per-frame 数据在 `_MMPBSA_*` 中间文件中。直接从 `mmgbsa.dat` 提取总结统计即可。

```python
# plot_mmgbsa.py
import re
import numpy as np
import matplotlib.pyplot as plt

# mmgbsa.dat 总结统计是空格分隔格式
# 例："DELTA TOTAL                -16.0897                4.0117              0.2865"
terms = {}
with open("mmgbsa.dat", "r") as f:
    for line in f:
        m = re.match(r"(VDWAALS|EEL|EGB|ESURF|DELTA\s+G\s+gas|DELTA\s+G\s+solv|DELTA\s+TOTAL)\s+([-\d.]+)\s+([-\d.]+)", line)
        if m:
            key = m.group(1).replace("  ", " ").strip()
            val = float(m.group(2))
            std = float(m.group(3))
            terms[key] = (val, std)

if not terms:
    print("No energy terms found in mmgbsa.dat")
    exit(1)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# 左图：能量分解
comp_terms = ["VDWAALS", "EEL", "EGB", "ESURF"]
comp_labels = ["VDWAALS\n(van der Waals)", "EEL\n(Electrostatic)", "EGB\n(Polar Solvation)", "ESURF\n(Non-polar Solvation)"]
comp_values = [terms.get(t, (0, 0))[0] for t in comp_terms]
comp_errs = [terms.get(t, (0, 0))[1] for t in comp_terms]
colors = plt.cm.Set2(range(len(comp_terms)))
axes[0].bar(comp_labels, comp_values, yerr=comp_errs, color=colors, capsize=5)
axes[0].set_ylabel("能量 (kcal/mol)")
axes[0].set_title("MM-GBSA Energy Decomposition")
axes[0].grid(True, alpha=0.3, axis="y")

# 右图：结合自由能总结
d_total = terms.get("DELTA TOTAL", (0, 0))
d_gas = terms.get("DELTA G gas", (0, 0))
d_solv = terms.get("DELTA G solv", (0, 0))
summary_terms = ["ΔG_gas\n(Gas Phase)", "ΔG_solv\n(Solvation)", "ΔG_total\n(Binding)"]
summary_vals = [d_gas[0], d_solv[0], d_total[0]]
summary_errs = [d_gas[1], d_solv[1], d_total[1]]
summary_colors = ["steelblue", "orange", "darkred" if d_total[0] < 0 else "darkgreen"]
axes[1].bar(summary_terms, summary_vals, yerr=summary_errs, color=summary_colors, capsize=5)
axes[1].axhline(y=0, color="black", linestyle=":", alpha=0.5)
axes[1].set_ylabel("能量 (kcal/mol)")
axes[1].set_title(f"MM-GBSA Binding Free Energy\nΔG_binding = {d_total[0]:.2f} ± {d_total[1]:.2f} kcal/mol")
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("mmgbsa_results.png", dpi=150)
print(f"DeltaG_binding = {d_total[0]:.2f} +/- {d_total[1]:.2f} kcal/mol")
```

---

## 附录：Python 环境准备

```powershell
$env:PYTHONIOENCODING="utf-8"
pip install pandas matplotlib seaborn numpy
```

所有 Python 脚本均需设置 `$env:PYTHONIOENCODING="utf-8"` 确保 Windows 终端中文正常输出。每个模块的脚本均包含完整的文件读写、数据处理和绘图保存逻辑，可直接在对应分析目录下运行。
