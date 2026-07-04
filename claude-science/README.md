# Claude Science

面向生命科学与计算化学的 Claude Code 扩展集合，包含 **MCP 服务器**（数据中间层）和 **技能**（AI 工作流模板）。

## 目录结构

```
claude-science/
├── mcp-servers/          # MCP 数据与交互服务
│   ├── bio-tools/        # 生物信息学统一查询接口（~247 个工具）
│   └── ketcher-chemistry/ # 交互式化学结构编辑器
└── skills/               # 科学计算技能集合（30+ 个）
    ├── 蛋白质结构预测与设计
    ├── 基因组与单细胞分析
    ├── 远程计算与 HPC
    ├── 模型部署与推理
    ├── 科研写作与可视化
    └── 系统与元技能
```

## mcp-servers —— 数据与交互中间层

### bio-tools

将 23 个生物信息学数据域的约 **247 个查询工具**统一为一个 `bio-mcp-server` 进程，AI 代理无需了解底层 HTTP/REST 细节即可查询生物医学数据库。

**Tier-1 服务器**（与 Claude 线上托管连接器完全兼容）：

| 服务器 | 领域 | 工具数 |
|---|---|---|
| mcp_pubmed | PubMed 文献检索 | 7 |
| mcp_chembl | ChEMBL 化合物/靶点/活性 | 6 |
| mcp_clinical_trials | ClinicalTrials.gov 临床试验 | 6 |
| mcp_biorxiv | bioRxiv 预印本 | 7 |
| mcp_biomart | Ensembl BioMart 基因注释 | 8 |

**Tier-2 服务器**（18 个领域服务器），涵盖：变异与群体遗传学、基因组与比较基因组学、基因表达、基因调控、蛋白结构与互作、蛋白功能注释、基因与本体论、化学与化合物、临床基因组学、药物监管、癌症模型、人类遗传学、学术文献、组学数据存档、RNA 家族、细胞类型、科研资源、虚拟筛选化合物。

### ketcher-chemistry

基于 EPAM Ketcher 的交互式 2D 分子结构编辑器。支持 SMILES / MOL / SDF / KET / RXN 格式，提供所见即所得的分子编辑能力，支持 AI 与人类用户协作编辑化学结构。

---

## skills —— 科学计算技能

### 1. 蛋白质结构预测与设计（11 个）

| 技能 | 功能 |
|---|---|
| **alphafold2** | AF2/AF2-Multimer via ColabFold |
| **boltz** | Boltz-2 全原子扩散共折叠（推荐默认） |
| **chai1** | Chai-1 基础模型共折叠 |
| **openfold3** | AF3 PyTorch 开源复现 |
| **esmfold2** | ESMFold2 单序列结构预测 |
| **fair-esm2** | ESM-2 蛋白语言模型嵌入与突变打分 |
| **diffdock** | DiffDock-L 全盲分子对接 |
| **proteinmpnn** | ProteinMPNN 序列逆向设计 |
| **ligandmpnn** | LigandMPNN 含配体/核酸的序列设计 |
| **solublempnn** | SolubleMPNN 可溶偏向序列设计 |

### 2. 基因组与单细胞分析（4 个）

| 技能 | 功能 |
|---|---|
| **evo2** | 长上下文基因组基础模型（最长 1M bp） |
| **borzoi** | DNA→功能轨预测模型 |
| **scgpt** | 单细胞基础模型（Transformer） |
| **scvi-tools** | 概率深度生成模型（scVI/scANVI） |

### 3. 远程计算与 HPC（3 个）

| 技能 | 功能 |
|---|---|
| **compute-env-setup** | 远程计算环境搭建 |
| **remote-compute-ssh** | SSH/SLURM 任务提交流程 |
| **remote-compute-modal** | Modal 无服务器 GPU 任务提交 |

### 4. 模型部署与推理（2 个）

| 技能 | 功能 |
|---|---|
| **managed-model-endpoints** | 模型服务注册与管理 |
| **using-model-endpoint** | 从已注册端点调用推理 |

### 5. 科研写作与可视化（6 个）

| 技能 | 功能 |
|---|---|
| **figure-style** | 出版级单图样式规范 |
| **figure-composer** | 出版级多面板组合图编排 |
| **paper-narrative** | 论文"故事线"评判与图表建议 |
| **literature-review** | 科学文献检索与综述 |
| **pdf-explore** | PDF 深度解析与查询 |
| **indication-dossier** | 治疗适应症档案生成 |

### 6. 系统与元技能（4 个）

| 技能 | 功能 |
|---|---|
| **customize** | 自定义 agent profile 和 skill |
| **self-awareness** | Claude Science 自身状态查询 |
| **product-self-knowledge** | Anthropic 产品事实源 |
| **skill-creator** | Skill 全生命周期管理 |

---

## 安装

```powershell
git clone https://github.com/baifan-wang/skills.git
```

将需要的组件复制到 Claude Code 对应目录：

```powershell
# MCP 服务器
cp -r claude-science/mcp-servers/* $env:USERPROFILE\.claude\mcp\

# 技能
cp -r claude-science/skills/<skill-name> $env:USERPROFILE\.claude\skills\<skill-name>
```

各组件详细说明请参见对应子目录下的 README。

## 许可证

各组件遵循其各自的许可证。详见 `skills/THIRD_PARTY_LICENSES.md`。
