# Claude Code Skills

面向计算化学、分子模拟与研究方法论的 Claude Code Skills 集合。

## 项目结构

| 目录 | 说明 |
|------|------|
| `autodock/` | 自动化分子对接技能 |
| `amber-md/` | Amber 分子动力学模拟技能 |
| `claude-science/` | Claude Science 扩展集合（MCP 服务器 + 科学技能） |
| `storm-research/` | STORM 多视角研究综述技能 |
| `agent-deliberation/` | 独立分析与交叉检查推理技能 |

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

### 4. storm-research — STORM 多视角研究综述

基于 Stanford STORM/Co-STORM 方法的多视角研究综述技能。使用多代理角色协作进行文献调研、证据综合与引用报告生成。

**核心功能：**
- 多视角研究（3-8 个视角，支持快速/标准/严格三种深度）
- 多种文献来源模式（本地优先 / 混合 / 网络优先 / 交互式）
- 证据基础综合与矛盾映射
- 引用审计与验证
- 生成结构化的文献综述报告

**触发关键词：** 文献综述、literature review、STORM、多视角研究、证据综合、引用报告、研究调研

### 5. agent-deliberation — 独立分析与交叉检查

围绕具体问题与证据形成判断的推理方法技能。适用于竞争方案、困难取舍、解释不确定，或用户明确要求多 Agent 分析的任务。不设人格角色，分析单位是证据与具体判断。

**核心功能：**
- 两种执行方式：单 Agent 分析（快速/低成本）或独立 Subagent 分析
- 两种分工：同题独立比较（隔离答案、避免预期结论外泄）与互补分析（按边界拆分）
- 针对性交叉检查：只复核可能改变结论的矛盾、反例或证据缺口
- 10 个可选分析视角（证据与解释、假设与反例、约束与实施等），按需使用而非固定阵容
- 区分事实、用户材料、推断与价值选择，不冒充真实多 Agent、不伪造来源或用户反馈
- 支持 Codex 与 Claude Code 双运行时适配，按需保存分析记录

**触发关键词：** 多 Agent 分析、独立分析、交叉检查、方案取舍、竞争方案、权衡、多视角判断、不确定解释

## 安装

```powershell
git clone https://github.com/baifan-wang/skills.git
```

### Claude Code

将需要的技能目录复制到 Claude Code 的 skills 目录：

```powershell
# claude-science
cp -r claude-science/mcp-servers/* $env:USERPROFILE\.claude\mcp\
cp -r claude-science/skills/<skill-name> $env:USERPROFILE\.claude\skills\<skill-name>

# autodock
cp -r autodock $env:USERPROFILE\.claude\skills\autodock

# amber-md
cp -r amber-md $env:USERPROFILE\.claude\skills\amber-md

# storm-research
cp -r storm-research $env:USERPROFILE\.claude\skills\storm-research

# agent-deliberation
cp -r agent-deliberation $env:USERPROFILE\.claude\skills\agent-deliberation
```

个人级目录在 Windows 上通常对应：

```text
C:\Users\你的用户名\.claude\skills\<skill-name>\
```

重新打开 Claude Code 后，可以显式调用：

```text
/<skill-name>
```

### Codex

全部技能都可原样复制到已配置的 Codex Skills 目录：

```powershell
# claude-science
cp -r claude-science/skills/<skill-name> $env:USERPROFILE\.codex\skills\<skill-name>

# autodock
cp -r autodock $env:USERPROFILE\.codex\skills\autodock

# amber-md
cp -r amber-md $env:USERPROFILE\.codex\skills\amber-md

# storm-research
cp -r storm-research $env:USERPROFILE\.codex\skills\storm-research

# agent-deliberation
cp -r agent-deliberation $env:USERPROFILE\.codex\skills\agent-deliberation
```

对应目录为：

```text
$CODEX_HOME/skills/<skill-name>/
```

未单独配置 `CODEX_HOME` 时，Windows 上常见的个人目录为：

```text
C:\Users\你的用户名\.codex\skills\<skill-name>\
```

重新打开 Codex 后，可以显式调用：

```text
$<skill-name>
```

`storm-research` 与 `agent-deliberation` 另带有 Codex 专用的运行时适配文档（`references/runtime-codex.md`）；`agent-deliberation` 还包含 `agents/openai.yaml`，提供 Codex 侧的显示名与默认提示。

各技能的详细安装和配置说明请参见对应目录下的 README。

## 依赖概览

| 技能 | 外部软件 | Python 库 |
|------|---------|-----------|
| claude-science | 按技能各异（详见子目录） | 按技能各异（详见子目录） |
| autodock | AutoDock Vina, OpenBabel, MGLTools | numpy, pandas, matplotlib, rdkit |
| amber-md | AmberTools 26+, Amber 26+ | numpy, pandas, matplotlib |
| storm-research | 无 | Python 3.10+（用于引用验证脚本） |
| agent-deliberation | 无 | 无 |

## 许可证

各技能遵循其各自的许可证。autodock 采用 MIT 许可证。
