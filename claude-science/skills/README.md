## 1. 蛋白质结构预测与设计（11 个技能）


### 结构预测（共折叠）

| 技能 | 一句话 | 输入 | 核心特点 |
|---|---|---|---|
| **alphafold2** | AF2/AF2-Multimer via ColabFold 跑单体或多聚体 | FASTA | MSA 通过 MMseqs2 公网服务器、五模型默认全跑、pLDDT+ipTM 排序、不处理配体/核酸 |
| **boltz** | Boltz-2: 全原子扩散共折叠（蛋白+DNA/RNA+SMILES/CCD 配体） | YAML | MIT 权重、最快的采样器、可选亲和力预测头、默认 binder 验证首选 |
| **chai1** | Chai-1 基础模型共折叠 | FASTA（header 标实体类型） | Apache-2.0、Python 入口方便批量循环、ESM embedding 模式可跳过 MSA |
| **openfold3** | AF3 的 PyTorch 开源复现（AlQuraishi Lab） | FASTA | Apache-2.0 权重、命令行为主、MSA 默认走公网 |
| **esmfold2** | Biohub ESMFold2/ESMFold2-Fast 全原子共折叠 | FASTA | 单序列模式无需 MSA、MIT 权重、还带 ESMC 蛋白语言模型（embedding/突变打分/SAE） |

**选择逻辑**：默认用 `boltz`（快+全开源）。需要共识投票时加 `chai1`。想和 AF3 对标用 `openfold3`。不想等 MSA 用 `esmfold2`。纯蛋白单体验证用 `alphafold2`。

### 蛋白嵌入与序列建模

| 技能 | 一句话 |
|---|---|
| **fair-esm2** | Meta AI 的 ESM-2 蛋白语言模型：残基/序列嵌入、masked-LM 似然突变打分、接触预测 |

> 注意：`fair-esm` 和 Biohub 的 `esm` fork 共享 `esm` 命名空间但不兼容——`fair-esm2` 是 Meta 原版，`esmfold2` 是 Biohub 的 fork。

### 分子对接

| 技能 | 一句话 |
|---|---|
| **diffdock** | DiffDock-L 全盲分子对接——不给搜索框，在整个蛋白表面扩散采样配体姿态并打分排序；预测几何，不预测亲和力 |

### 序列逆向设计（inverse folding）

| 技能 | 一句话 | 设计上下文 |
|---|---|---|
| **proteinmpnn** | ProteinMPNN：给定骨架构象反推氨基酸序列 | 蛋白-蛋白界面；不含配体/核酸/金属 |
| **ligandmpnn** | LigandMPNN：在 proteinmpnn 基础上加入配体、核酸、金属 | 结合口袋周围的残基重设计 |
| **solublempnn** | SolubleMPNN：同架构但在可溶 PDB 子集上重训练 | 偏向可溶表达的序列，减少包涵体 |

**选择逻辑**：纯蛋白界面 → `proteinmpnn`；有配体/辅因子 → `ligandmpnn`；下一步要做大肠杆菌表达筛选 → `solublempnn`。`ligandmpnn` 的 `run.py` 也是唯一会把设计序列穿回输入结构的 runner。

## 2. 基因组与单细胞分析（3 个技能）

| 技能 | 一句话 | 输入 | 典型场景 |
|---|---|---|---|
| **evo2** | Arc Institute 的长上下文基因组基础模型 | 最长 1M bp DNA 序列 | 变异效应打分、基因组窗口嵌入、条件 DNA 生成、跨物种调控区评分 |
| **borzoi** | Calico 的 DNA→功能轨预测模型 | 524 kb one-hot 窗口 | 预测 RNaseq/CAGE/DNase/ChIP 等 7,611 条人类功能轨、非编码变异优先级排序、生成 locus 覆盖轨 |
| **scgpt** | 单细胞基础模型，Transformer 架构 | AnnData (scRNA-seq) | 细胞嵌入（聚类/整合）、零样本或微调细胞类型注释、基因级表示（扰动/GRN） |
| **scvi-tools** | 概率深度生成模型——scVI/scANVI | 原始整数 UMI 计数 | 批次校正隐空间嵌入、半监督标签迁移、贝叶斯差异表达 |

**组合推荐**：`evo2` + `borzoi` 可以做双轴变异优先级排序（序列似然 + 功能轨 delta）。

## 3. 远程计算与 HPC（3 个技能）

| 技能 | 一句话 | 适用场景 |
|---|---|---|
| **compute-env-setup** | 在远程 provider 上搭建计算环境 | 新 provider 上线、conda 环境移植、Slurm/apptainer 配置、权重缓存挂载、GPU 镜像构建 |
| **remote-compute-ssh** | SSH/SLURM 主机的提交→等待通知→取回工作流 | 自有集群、学校 HPC、实验室 Slurm 节点 |
| **remote-compute-modal** | Modal 无服务器 GPU 的提交→等待通知→取回工作流 | 用户自己的 Modal 账号、弹性 GPU 弹性扩容 |

**使用模式**：`compute-env-setup` 是一次性环境初始化；`remote-compute-ssh` 和 `remote-compute-modal` 是日常任务提交的模板。流程统一：`host.compute.create(provider)` → `submit_job()` → `wait_for_notification` 脑工具 → 收到 `compute_done` 通知后 `save_artifacts`。

## 4. 模型部署与推理服务（2 个技能）

| 技能 | 一句话 | 关键操作 |
|---|---|---|
| **managed-model-endpoints** | 将模型服务注册进 managed 家族 | 读 runbook → 分配端口（本地）→ 写幂等启停脚本 → 注册一次即可；支持本地容器和远程 HTTPS |
| **using-model-endpoint** | 从已注册的 endpoint 调推理 | 在 scoped inference kernel 中用预载的 `BASE_URL` 调 HTTP API |

## 5. 科研写作与可视化（6 个技能）

| 技能 | 一句话 | 输入 | 输出 |
|---|---|---|---|
| **figure-style** | 出版级单图样式规则和校验清单 | 数据 + 一句话声明 | 单幅发表级图（300 dpi） |
| **figure-composer** | 出版级多面板组合图编排器 | 一句话声明 + 数据引用 或已有 PNG | 多面板 composite figure + 字母标注 + adversarial review |
| **paper-narrative** | 评判论文"故事线"并给出图表重排建议 | 手稿/摘要 + figure deck | hook_verdict、arc、figure_moves、missing_panels、kill_list |
| **literature-review** | 科学文献检索、验证、综述 | 研究问题 | 经过验证的引文综述、避免伪造引用 |
| **pdf-explore** | 深度解析 PDF（一次性解析后随意查询） | PDF 文件 | `pdf_pages`、`pdf_outline`、`pdf_scan`、`pdf_map` 等结构化数据 |
| **indication-dossier** | 治疗适应症档案生成 | 适应症名 | 五阶段结构化档案：患者人群→流行病学→疾病生物学→标准治疗→监管先例→关键临床试验 |

**调用层级**：`paper-narrative` 管全局叙事 → `figure-composer` 管多面板合成 → `figure-style` 管单幅图形规范和渲染。不要跳过层级直接调用底层。

## 6. 系统与元技能（4 个技能）

| 技能 | 一句话 | 何时触发 |
|---|---|---|
| **customize** | 创建/配置自定义 agent profile 和 skill | 用户想新建 agent、修改能力集、挂载/卸载 skill/connector、或需要 `host.agents.*` / `host.skills.*` SDK |
| **self-awareness** | Claude Science 自身会话数据库 schema 和内省接口 `host.query()` | 查询 token 用量、成本、执行日志、artifact 元数据、消息存储位置等自身状态 |
| **product-self-knowledge** | Anthropic 产品事实源（Claude Code / API / Claude.ai） | 任何涉及 Anthropic 产品细节的回答——安装要求、定价、模型、功能对比等，避免凭过时训练数据回答 |
| **skill-creator** | Skill 全生命周期管理 | 从零创建、修改、跑 eval、benchmark、优化描述触发精度、打包 `.skill` 文件 |

---