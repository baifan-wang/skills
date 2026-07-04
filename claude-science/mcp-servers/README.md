## bio-tools —— 生物信息学 MCP 工具集

### 整体定位

`bio-tools` 是一个**聚合式 MCP 服务端**，将 23 个生物信息学数据域、约 247 个查询工具统一到一个名为 `bio-mcp-server` 的 stdio 进程中。每个工具对应一个外部数据库或 API 的查询操作，AI 代理无需知道底层 HTTP/REST 细节，直接调用工具名和参数即可获取结构化结果。

启动入口是 `run_server.py` —— 一个轻量路由脚本，根据命令行参数从 `lib/` 下动态加载对应的 server 模块。所有 `mcp_` 前缀且包含 `server.py` 的包都是可独立运行的，但生产环境中由 `mcp_bio` 聚合器统一启动。

### 架构分层

代码库采用三层结构：

**1. Tier-1 服务器（5 个）** —— 直接对等原始托管连接器

这些服务器的工具名称、参数 schema 和输出格式与线上 Claude 的 hosted connector **完全一致**。每个包里有一个 `schemas.json`（从原连接器抓取的 verbatim 工具定义）和一个 `server.py`（手工编写的数据获取 + 格式化逻辑）。

- `mcp_pubmed` — PubMed 文献检索，7 个工具
- `mcp_chembl` — ChEMBL 化合物/靶点/活性数据，6 个工具
- `mcp_clinical_trials` — ClinicalTrials.gov 临床试验，6 个工具
- `mcp_biorxiv` — bioRxiv 预印本，7 个工具
- `mcp_biomart` — Ensembl BioMart 基因注释，8 个工具

**2. Tier-2 服务器（18 个）** —— 基于 FastMCP 的领域服务器

每个对应一个数据域：

| 包名 | 领域 | 工具数 | 代表数据源 |
|---|---|---|---|
| `mcp_variants` | 变异与群体遗传学 | 18 | gnomAD, ClinVar, dbSNP, CADD |
| `mcp_genomes` | 基因组与比较基因组学 | 11 | Ensembl REST, UCSC Genome Browser |
| `mcp_expression` | 基因表达 | 15 | GTEx, PanglaoDB |
| `mcp_regulation` | 基因调控 | 16 | ENCODE, JASPAR, UniBind |
| `mcp_structures_interactions` | 蛋白结构与互作 | 16 | PDB, AlphaFold, EMDB, IntAct, ComplexPortal |
| `mcp_protein_annotation` | 蛋白功能注释 | 13 | InterPro, Pfam, STRING, Protein Atlas |
| `mcp_genes_ontologies` | 基因与本体论 | 10 | GO, KEGG, Reactome, UniProt, MyGene |
| `mcp_chemistry` | 化学与化合物 | 12 | ChEBI, PubChem, Rhea, BindingDB |
| `mcp_clinical_genomics` | 临床基因组学 | 20 | CIViC, ClinGen, Open Targets |
| `mcp_drug_regulatory` | 药物监管 | 7 | OpenFDA (Drugs@FDA, Labels) |
| `mcp_cancer_models` | 癌症模型 | 11 | cBioPortal, DepMap |
| `mcp_human_genetics` | 人类遗传学 | 14 | GWAS Catalog, eQTL Catalogue, PheWeb |
| `mcp_literature` | 学术文献 | 9 | arXiv, OpenAlex |
| `mcp_omics_archives` | 组学数据存档 | 17 | GEO, ArrayExpress, PRIDE, MetaboLights, MGnify |
| `mcp_rna` | RNA 家族 | 9 | Rfam |
| `mcp_cellguide` | 细胞类型 | 5 | CZ CELLxGENE CellGuide |
| `mcp_research_resources` | 科研资源 | 5 | Antibody Registry, Grants.gov |
| `mcp_zinc` | 虚拟筛选化合物 | 5 | ZINC20 |

**3. Fleet 包（检索层）**

`lib/` 下还有 30+ 个不带 `mcp_` 前缀的"fleet"包（如 `pubmed_fetch`、`chembl_bioactivity`、`uniprot_fetch`），它们是纯数据检索客户端，封装了 HTTP 调用、速率限制、重试逻辑和 XML/JSON 解析。每个 server 调用这些 fleet 包获取原始数据，再通过本地的 `marshal.py` 格式化为连接器兼容的输出。

**4. 公共基础设施** —— `mcp_servers_common`

提供所有服务器共享的框架能力：
- `Tier1Server`（`tier1.py`）：轻量 MCP 服务端包装器，负责从 `schemas.json` 加载工具定义、验证 handler 与 schema 一一对应、通过 `anyio.to_thread` 在工作线程中执行同步 handler、并在输出存在 `outputSchema` 时附加 `structuredContent`
- `gate.py`：启动时应用 `deferred.json` 中的延迟/许可门控
- `ratelimit.py`、`errors.py`、`ua.py`：速率控制、错误检测、User-Agent 管理

### 聚合器：`mcp_bio`

`mcp_bio/server.py` 是整个 `bio-tools` 的真正生产入口。它在单个进程中实例化所有 23 个域服务器，将全部 247 个工具暴露为一个 MCP 服务（`bio-mcp-server`）。域划分信息存储在 `domains.json`。

### 许可与延迟门控

`deferred.json` 控制哪些工具当前**不启用**：
- `license_tools` 列出了上游许可受限的工具（KEGG 仅学术用途、CADD 仅非商业用途、PanglaoDB 未验证再分发条款、Sanger Cell Model Passports 禁止商业使用），这些工具需经法务审批后才能启用
- `domains` / `tools` 列表目前在代码提交中已清空，对应工具已启用

### 设计约束

每个服务器都遵循严格的兼容性约束：
- 工具名和参数名必须与原始托管连接器完全一致
- 输出 JSON 格式保持 `original_json()` 编码（`ensure_ascii=False`，插入顺序保留）
- 所有工具被标注为 `readOnlyHint=True`
- 错误格式化的响应通过 `is_error_payload()` 检测并标记为 `isError=True`

---

## ketcher-chemistry —— 交互式化学结构编辑器

### 整体定位

`ketcher-chemistry` 是一个基于 **EPAM Ketcher** 内核的 **交互式 2D 分子结构编辑器**，以 MCP Server 形式呈现给 AI 代理。它不仅是一个"读"工具，还提供了**可视化交互界面** —— AI 可以打开一个分子素描画布，用户可以在上面手动编辑结构，AI 再读取编辑结果。

入口为 `server.js`（1019 KB，Bun 打包的单文件），服务名为 `ketcher-chemistry`，版本 `0.1.0`。

### 核心工具

**`open_sketcher`** —— 打开分子素描画布

唯一的顶层工具。接受一个或多个分子表示格式作为输入（`smiles` / `molfile` / `ket` / `rxn`），在 UI 中渲染一个可交互的 Ketcher 编辑面板。返回 `artifact_id`。

支持的输入格式：
| 格式 | 说明 | MIME 类型 |
|---|---|---|
| SMILES | 简化分子线性表示 | `chemical/x-daylight-smiles` |
| MOL/SDF | MDL 分子文件格式 | `chemical/x-mdl-*` |
| KET | Ketcher 原生格式（推荐，无损） | `application/json` |
| RXN | 反应式格式 | — |

**会话内子工具**（画布挂载后可用）

一旦画布打开，以下工具会出现在 AI 的工具列表中：
- `set_structure` —— 以编程方式设置画布内容（替换当前分子）
- `highlight_atoms` —— 高亮指定原子（用于教学/讨论）
- `get_structure` —— 读取画布当前状态，返回 KET/SMILES/molfile

### 前端控件

Ketcher 编辑器前端打包为单个 HTML 文件 `widget/index.html`（约 26 MB），包含完整的 Ketcher Web 应用，支持：
- 原子的增删改
- 键类型切换（单键 / 双键 / 三键 / 芳香键）
- 立体化学标记
- 官能团模板
- 反应式编辑
- 撤销 / 重做

### 与 AI 工作流的集成

`ketcher-chemistry` 的设计深度融入了 Claude Science 的 artifact 系统：

- **资源协议**：通过 MCP Resource 暴露 Ketcher HTML 控件，资源 URI 为固定常量
- **artifact 保存**：用户在画布上的编辑会被自动跟踪（`hasChangeField`），AI 可通过 `get_structure` 读取结果并保存为 `.ket` 文件
- **上下文传递**：画布状态（SMILES、反应式、选中原子、高亮原子等）通过 `contextSchema` 暴露，AI 无需读取文件就能感知当前分子状态
- **文件关联**：注册了 8 种化学文件扩展名（`.smi`, `.mol`, `.sdf`, `.ket`, `.rxn` 等），双击这些文件直接打开编辑器

### 技术架构

- **运行时**：Bun（Node.js 兼容），打包为单文件 ESM
- **框架**：直接使用 `@modelcontextprotocol/sdk` 的低级 `McpServer` API
- **验证**：Zod schema 做参数验证
- **资源加载**：启动时通过 `loadWidgetHtml()` 从磁盘读取 Ketcher 前端包到内存

---

## 总结

`mcp-servers` 目录本质上是 Claude Science 的**数据中间层**，两条产品线定位清晰：

- **bio-tools**：面向**数据检索**，将上百个生命科学数据库封装成统一的函数调用接口，AI 代理像调用库函数一样查询生物医学数据。架构上通过 fleet 包 + marshal + schema 三层分离，保证了与线上 hosted connector 的字节级兼容性，同时允许本地下线开发。

- **ketcher-chemistry**：面向**交互编辑**，提供了 AI 与人类用户之间的化学结构协作编辑能力。它不只是"读"工具，而是完整的 GUI 控件，让化学信息学的"所见即所得"能力进入 AI 工作流。
