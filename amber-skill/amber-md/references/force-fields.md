# Amber 分子动力学模拟力场选择指南

---

## 1. 蛋白质力场对比

| 力场名称 | LEaP 载入命令 | 推荐度 | 说明 |
|----------|--------------|--------|------|
| ff19SB | `leaprc.protein.ff19SB` | ★★★ 首选 | Amber20+ 默认蛋白力场；骨架二面角参数基于更高水平的 QM 数据重新拟合；修正了 ff14SB 中部分氨基酸（如甘氨酸、脯氨酸）的二级结构偏好偏差 |
| ff14SB | `leaprc.protein.ff14SB` | ★★☆ 备选 | Amber14-18 默认力场；ff99SB 的基础上改进了侧链扭转参数；文献中大量使用，验证充分 |
| ff03 | `leaprc.ff03` | ★☆☆ 避免 | 旧版力场；静电势拟合电荷方案与当前主流不同；不建议新项目使用 |

**选择建议**：新项目默认使用 ff19SB；如需与使用 ff14SB 的文献进行直接比较，可选 ff14SB。

---

## 2. 水模型对比

| 水模型 | LEaP 载入 | 类型 | 推荐度 | 说明 |
|--------|----------|------|--------|------|
| TIP3P | `leaprc.water.tip3p` | 3-point | ★★★ 默认 | 计算速度最快；与蛋白力场联用验证最充分；扩散系数约为实验值的 2-3 倍 |
| OPC | `leaprc.water.opc` | 4-point | ★★☆ | 更准确的介电常数和扩散性质；计算量约增加 20-30% |
| TIP4P-Ew | `leaprc.water.tip4pew` | 4-point | ★☆☆ | 旧版 4-site 水模型；OPC 在各方面表现更优 |

**选择建议**：默认使用 TIP3P；当水的动力学性质（扩散、弛豫时间）对研究问题有重要影响时，使用 OPC。

---

## 3. 小分子力场 GAFF2

小分子配体使用 GAFF2（General Amber Force Field 2）：

```tcl
# LEaP 中加载 GAFF2
source leaprc.gaff2
```

### 3.1 antechamber 生成文件

| 输出文件 | 作用 |
|----------|------|
| `.prepin` | 定义原子类型、残基、电荷和成键信息 |
| `.frcmod` | 补充 GAFF2 中缺失或需要覆盖的成键参数 |

### 3.2 电荷方法

| 方法 | 命令 | 特点 | 适用场景 |
|------|------|------|----------|
| AM1-BCC | `-c bcc` | 快速，半经验方法；无需额外 QM 计算 | 有机小分子，推荐首选 |
| RESP | `-c resp` | 需要 Gaussian 等 QM 软件提供静电势格点 | 特殊电子结构、带形式电荷分子 |

**重要：`-nc` 指定小分子净电荷（整数，默认 0）**。净电荷由分子在生理 pH 下的质子化状态决定。若设置错误，antechamber 会失败或产生不合理电荷。

```bash
# AM1-BCC（推荐默认），-nc 0 表示净电荷为零
antechamber -i ligand.mol2 -fi mol2 -o ligand.prepin -fo prepi -c bcc -nc 0 -s 2

# RESP（需先完成 Gaussian 静电势计算）
antechamber -i ligand.mol2 -fi mol2 -o ligand.prepin -fo prepi -c resp -nc 0
```

---

## 4. 离子参数

Joung-Cheatham 单价离子参数，专为 TIP3P 水模型优化：

```tcl
# LEaP 中加载离子参数
loadamberparams frcmod.ionsjc_tip3p
```

支持的离子：Na+、K+、Cl-（也包含 Cs+、Rb+、I-、Br-）。此参数修正了早期离子参数在水溶液中形成非物理性离子对的问题。

---

## 5. LEaP 载入模板

### 5.1 纯蛋白体系

```tcl
source leaprc.protein.ff19SB
source leaprc.water.tip3p
```

### 5.2 蛋白-配体复合物

```tcl
source leaprc.protein.ff19SB
source leaprc.water.tip3p
source leaprc.gaff2
loadamberprep ligand.prepin
loadamberparams ligand.frcmod
loadamberparams frcmod.ionsjc_tip3p
```

### 5.3 蛋白-蛋白复合物

```tcl
source leaprc.protein.ff19SB
source leaprc.water.tip3p
loadamberparams frcmod.ionsjc_tip3p
```

---

## 6. 力场选择决策树

```
1. 包含标准氨基酸？ → 是 → ff19SB（默认首选）
                    → 否 → 跳过蛋白力场

2. 含小分子配体？   → 是 → 加载 leaprc.gaff2 + antechamber 生成 prepin/frcmod
                    → 否 → 跳过

3. 水动力学重要？   → 是 → OPC 水模型
                    → 否 → TIP3P（默认）

4. 体系带净电荷？   → 是 → addions2 + ionsjc_tip3p 中和
                    → 否 → 跳过

5. 特殊组分？
   - 膜蛋白     → Lipid21 + Slipids（本 skill 暂不覆盖）
   - DNA/RNA    → OL15 + OL3（本 skill 暂不覆盖）
   - 糖类       → GLYCAM_06j（本 skill 暂不覆盖）
   - 有机溶剂   → 本 skill 暂不覆盖
```

---

## 7. 参考资料

- Tian C, et al. ff19SB: Amino-acid-specific protein backbone parameters trained against quantum mechanics energy surfaces in solution. *JCTC*, 2020, 16(1): 528-552.
- Maier JA, et al. ff14SB: Improving the accuracy of protein side chain and backbone parameters from ff99SB. *JCTC*, 2015, 11(8): 3696-3713.
- He X, et al. (GAFF2). *JCC*, 2020, 41(13): 1271-1281.
- Izadi S, et al. (OPC). *JPC Letters*, 2014, 5(21): 3863-3871.
- Joung IS, Cheatham TE III. *JPCB*, 2008, 112(30): 9020-9041.
