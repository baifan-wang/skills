# Agent Skills

面向计算化学、分子模拟、启蒙教育与智能体方法论的 Agent Skills 集合。

本仓库技能遵循通用 Agent Skill 规范（包含 `SKILL.md` 元数据与工作流定义），不局限于特定客户端，可无缝用于 **Antigravity**、**Claude Code**、**Codex**、**OpenCode** 等各类支持 Agent Skills 的智能体环境。

## 项目结构

| 目录 | 说明 |
|------|------|
| `autodock/` | 自动化分子对接技能 |
| `amber-md/` | Amber 分子动力学模拟技能 |
| `claude-science/` | 科学计算扩展集合（MCP 服务器 + 科学技能） |
| `storm-research/` | STORM 多视角研究综述技能 |
| `agent-deliberation/` | 独立分析与交叉检查推理技能 |
| `hanzi-pictogram-cards/` | 幼儿汉字字画联想识字卡生成技能 |

## 技能列表

### 1. claude-science — 科学计算扩展

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

Amber 分子动力学模拟全流程助手。Agent 直接执行体系构建和轨迹分析，用户自行运行计算密集的模拟步骤。

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
- 支持多 Agent 运行时适配，按需保存分析记录

**触发关键词：** 多 Agent 分析、独立分析、交叉检查、方案取舍、竞争方案、权衡、多视角判断、不确定解释

### 6. hanzi-pictogram-cards — 汉字字画联想识字卡

为宝宝批量制作中文汉字和词语识字卡。调用环境内置生图工具（如 Codex `image_gen`）绘制字形联想插画，左侧汉字和带声调拼音、右侧可爱图形，支持象形启发、避免生硬把字贴到图上，最后批量输出可打印 PNG 和拼版。

**核心功能：**
- 标准化卡片排版：左侧标准汉字与拼音，右侧基于字形联想的可爱生动插画
- 零额外 API 成本：生图由客户端内置生图能力执行，排版由本地 Python 脚本生成
- 丰富预置字库：提供 24 字启蒙常用字与 156 字完整汉字库（含拼音、部首、阶段划分）
- 批量卡片渲染与多合一拼版：生成高分辨率卡片并支持 A4 打印拼版

**触发关键词：** 汉字识字卡、儿童字卡、象形识字、字画联想、拼音卡片、宝宝识字

## 安装与配置

```powershell
git clone https://github.com/baifan-wang/skills.git
```

本仓库中的技能遵循开放的 Agent Skills 标准（以 `SKILL.md` 为核心），可直接放置到对应工具的 skills 目录下。

### 常见 Agent 环境目录对应

| 环境 | 用户级目录 (Windows) | Linux / macOS | 调用方式 |
|------|---------------------|---------------|----------|
| **通用 / Antigravity** | `$env:USERPROFILE\.agents\skills\<skill-name>\` | `~/.agents/skills/<skill-name>/` | 自动意图识别 / 自然语言激活 |
| **Claude Code** | `$env:USERPROFILE\.claude\skills\<skill-name>\` | `~/.claude/skills/<skill-name>/` | `/<skill-name>` 或自然语言 |
| **Codex** | `$env:USERPROFILE\.codex\skills\<skill-name>\` | `~/.codex/skills/<skill-name>/` | `$<skill-name>` |

### 批量安装示例 (PowerShell 7)

```powershell
# 1. 通用 Agent 目录（推荐，如 Antigravity / .agents 体系）
$target = "$HOME\.agents\skills"
New-Item -ItemType Directory -Force $target | Out-Null
Get-ChildItem -Directory | Where-Object { $_.Name -notin @('.git', 'claude-science') } | ForEach-Object {
    Copy-Item -Recurse -Force $_.FullName "$target\"
}

# 2. Claude Code
$claudeTarget = "$HOME\.claude\skills"
New-Item -ItemType Directory -Force $claudeTarget | Out-Null
Get-ChildItem -Directory | Where-Object { $_.Name -notin @('.git', 'claude-science') } | ForEach-Object {
    Copy-Item -Recurse -Force $_.FullName "$claudeTarget\"
}

# 3. Codex
$codexTarget = if ($env:CODEX_HOME) { "$env:CODEX_HOME\skills" } else { "$HOME\.codex\skills" }
New-Item -ItemType Directory -Force $codexTarget | Out-Null
Get-ChildItem -Directory | Where-Object { $_.Name -notin @('.git', 'claude-science') } | ForEach-Object {
    Copy-Item -Recurse -Force $_.FullName "$codexTarget\"
}
```

> **注意：** `claude-science` 集合包含专属的 MCP 服务器配置与 30+ 细分科学技能，详细安装指引请参见 [claude-science/README.md](claude-science/README.md)。

## 依赖概览

| 技能 | 外部软件 | Python 库 |
|------|---------|-----------|
| claude-science | 按技能各异（详见子目录） | 按技能各异（详见子目录） |
| autodock | AutoDock Vina, OpenBabel, MGLTools | numpy, pandas, matplotlib, rdkit |
| amber-md | AmberTools 26+, Amber 26+ | numpy, pandas, matplotlib |
| storm-research | 无 | Python 3.10+（用于引用验证脚本） |
| agent-deliberation | 无 | 无 |
| hanzi-pictogram-cards | 无 | Pillow |

## 许可证

各技能遵循其各自的许可证。autodock 采用 MIT 许可证。
