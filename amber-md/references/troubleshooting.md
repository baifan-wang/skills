# Amber MD 模拟故障排除指南

按模拟阶段组织。每个条目格式：**症状** -> **可能原因** -> **解决方案**

---

## 1. antechamber 阶段

**antechamber 报错 / 计算结果异常（如原子类型分配错误）**
-> 未指定小分子净电荷（`-nc`）
-> 运行前必须询问用户小分子的净电荷（整数）。生理 pH 下多数有机分子为 0，含羧基/胺基等可电离基团则不为 0。在命令中添加 `-nc N` 参数（N 为净电荷值）。

**"No matching atomic type found for atom X"**
-> 原子类型不在 GAFF2 数据库中
-> 检查分子是否含有异常元素或价态。尝试使用 `-at gaff2` 标志。若 BCC 方法失败，可考虑使用 RESP 电荷方法。

**"Bond parameters missing for X-Y"**
-> parmchk2 无法找到对应参数
-> 检查 frcmod 输出文件。如果只有 angle/dihedral 参数缺失，通常可以接受。若 bond 参数也缺失，该分子可能需要 QM 级别参数化。

**prepin 文件中的残基名称与 PDB 不匹配**
-> LEaP 将无法识别该残基
-> 打开 prepin 文件，检查第 5 行的残基名称。必须与 ligand.pdb 中的残基名称完全一致。

---

## 2. LEaP 阶段

**"check: ERROR: The unperturbed charge of the unit is not zero"**
-> 体系带有净电荷，但未添加抗衡离子
-> 在溶剂化之前，先运行 `check` 查看体系净电荷，然后使用 `addions2` 添加相应的抗衡离子。

**"check: ERROR: Could not find bond parameter for..."**
-> 缺少 bond/angle/dihedral 力场参数
-> 检查是否已加载所有需要的力场文件和 frcmod 文件。使用 `desc <residue>` 命令检查有问题的残基。

**"Residue XXX not found in library"**
-> PDB 中的残基名称与 Amber 命名规范不匹配
-> 重命名残基：HIS→HIE/HID/HIP，CYS→CYX（有二硫键）/CYM（去质子化），对其他非标准残基进行相应重命名。

**"WARNING: There is a bond of X angstrom between..."**
-> 原子距离过近（空间位阻冲突）或过远（缺少成键）
-> 对于冲突：检查原始 PDB 结构是否合理。对于缺少成键：检查原子的连接性是否正确。

---

## 3. 能量优化阶段

**能量不降反升**
-> 初始几何构型较差，存在严重的空间位阻冲突
-> 增加 restraint_wt 约束力常数，减少第一阶段 maxcyc 步数，或使用更强的约束条件。

**优化在 maxcyc 步数后仍未收敛**
-> 结构偏离能量极小值点较远
-> 增大 maxcyc（例如设为 2000）。同时检查约束条件是否设置正确。

**能量输出中出现 NaN 或 Infinity**
-> 原子重叠导致力场溢出
-> 检查初始结构。严重的原子冲突会导致此问题。尝试使用更强的初始约束条件。

---

## 4. 动力学模拟阶段

**"SHAKE algorithm failed to converge"**
-> 积分步长过大，或体系中存在过强的力
-> 将 dt 减小至 0.001（即 1fs）。检查能量优化输出的能量值：如果仍然很高，需要重新进行能量优化。

**"vlimit exceeded"**
-> 原子速度过高（通常来自不良接触）
-> 回到能量优化阶段，使用更强的约束条件。检查盒子尺寸是否足够大。

**模拟盒子急剧膨胀或收缩**
-> 压力耦合不稳定
-> 减小 taup（例如设为 0.5），检查密度是否在震荡。初始阶段可使用较弱的压力耦合。

**温度显著偏离目标值**
-> 恒温器（thermostat）耦合过弱
-> 减小 gamma_ln，或在初始平衡阶段使用 Berendsen 恒温器（ntt=1）。

**体系总能量持续漂移**
-> 长时间模拟的不稳定性
-> 检查成品模拟（production run）参数是否与平衡阶段一致。可考虑使用 ntt=3 搭配 gamma_ln=5.0 以获得更好的稳定性。

---

## 5. 分析阶段

**"Number of atoms in NetCDF file (306) does not match number in associated topology (6847)"**
-> `comp_dry.top` 在 `solvateoct` **之后**保存，导致真空拓扑包含了水和离子的原子
-> 重新运行 tleap，确保 `saveamberparm comp comp_dry.top comp_dry.crd` 在 `solvateoct` **之前**执行。验证：`comp_dry.top` 应远小于 `comp_oct.top`（例如 267K vs 1.3M）。

**"cpptraj: Could not find topology/parameters" 或 parm/trajin 路径错误**
-> 分析目录结构与 SKILL.md 规定的 `analysis/<模块>/` 结构不一致
-> 所有 cpptraj 输入文件中的路径应相对于所在子目录：`parm ../../prep/comp_dry.top`，`trajin ../strip/strip.nc`。

**PCA: "Warning: Set 'evecs' contains no data"**
-> `diagmatrix`（分析命令）和 `projection`（动作命令）放在了同一次 cpptraj 调用中，但 `diagmatrix` 在 `run` 后才执行，`projection` 在解析时检查数据
-> 分两步执行：第一步 `matrix covar` + `diagmatrix` + `run`，第二步 `projection evecs evecs.dat out proj.dat @CA beg 1 end 2` + `run`（直接从文件读取 eigenvectors）。

**聚类: "Warning: No clustering algorithm specified; defaulting to 'hieragglo'"**
-> `cluster C0 repout rep repframe` 被当作独立的第二条 `cluster C0` 命令（无算法参数），覆盖了前面的 kmeans 设置
-> 将 `repout rep repframe` 合并到主 cluster 命令中：`cluster C0 kmeans clusters 5 ... repout rep repframe out cnumvtime.dat ...`。

**氢键分析: "Warning: Set 'HBOND[UU]' contains no data"**
-> 蛋白和配体之间确实没有满足氢键判据（距离 ≤ 3.5 Å，角度 ≥ 135°）的相互作用
-> 这不一定是错误。如实报告"未检测到稳定蛋白-配体氢键，结合可能由疏水/π-π 堆积主导"。检查 hbond_avg.dat 是否为空。

**Python: "single positional indexer is out-of-bounds" 读 summary 文件**
-> `process_mdout.perl` 对不同输出文件生成不同列数；`summary.DENSITY` 有时只有 1 列（值），而其他文件有 2 列（时间 + 值）
-> Python 脚本需检查 `data.shape[1]`：如果只有 1 列，用 `np.arange(len(y))` 生成 x 轴。

**Python: "TypeError: unsupported operand type(s) for /: 'str' and 'str'" 读 evecs.dat**
-> `evecs.dat` 格式特殊（header、维度行、"****"分隔符），不能用 `pd.read_csv` 直接读取
-> 手动解析：跳过 header 行和维度行，只在 `len(parts) == 2 and parts[0].isdigit()` 时提取特征值。

**Python: KeyError 读 cluster summary.dat**
-> `summary.dat` 首行以 `#` 开头（如 `#Cluster Frames Frac ...`），`pd.read_csv(comment="#")` 会跳过该行导致列名变成第一行数据的值
-> 使用 `comment="#"` + `header=None` + 手动 `names=[...]` 指定列名。

---

*本指南涵盖 Amber 模拟中最常见的故障场景。如遇到未列出的问题，请查阅 Amber 官方手册或邮件列表。*
