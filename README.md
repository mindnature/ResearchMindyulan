# ResearchMind Yulan

> 面向真实学术场景的科研决策增强型 Deep Research Agent

ResearchMind Yulan 是 ResearchMind 的竞赛版，面向「全球人工智能创新·治理·安全大赛」赛道一：**面向真实学术场景的深度研究智能体设计大赛**。

它不把 Deep Research 停留在“搜索更多资料 + 生成更长报告”，而是把科研过程拆成可检查的决策链：

```text
研究问题
  ↓
问题拆解与检索规划
  ↓
证据登记与来源审计
  ↓
Literature Matrix
  ↓
Research Gap 扫描
  ↓
竞争性解释 / 反证搜索
  ↓
方法风险审计
  ↓
Research Advisor 决策增强
  ↓
Research Decision Memo
  ↓
Evidence Audit Trail
```

## 核心问题

今天的大模型已经很擅长找论文、读论文和总结论文，但科研人员真正困难的往往是：

- 哪个问题值得继续追？
- 一个所谓 Research Gap 是否真的成立？
- 多种解释同时存在时，应该优先验证哪一个？
- 当前证据支持什么、不支持什么？
- 研究设计最脆弱的假设在哪里？
- 什么时候应该继续，什么时候应该调整方向？

ResearchMind Yulan 的目标是让 Deep Research 从“信息生产”进一步走向**可回源、可质疑、可验证的科研判断支持**。

## 当前可运行版本

`v0.2 — Runnable Pipeline Skeleton`

当前 `main` 已经具备一个最小端到端 Pipeline：

```text
Research Question
→ Question Mapper
→ Search Planner
→ Evidence Registry
→ Literature Matrix
→ Gap Detector
→ Skeptic / Counter-evidence
→ Method Auditor
→ Decision Synthesizer
→ final_report.md
→ audit_trail.json
```

每次运行还会单独保存各阶段结构化中间产物，便于复现、调试和比赛评审展示。

> 当前 Evidence Scout 使用本地 JSON corpus 完成可复现 MVP。真实学术搜索、论文抓取与来源验证是下一阶段 P0 工程任务，不把 synthetic demo corpus 冒充真实文献。

## 5分钟跑起来

要求：Python 3.10+。

```bash
git clone https://github.com/mindnature/ResearchMindyulan.git
cd ResearchMindyulan
python -m pip install -e .
```

不配置任何 API Key，也可以运行离线可复现 Demo：

```bash
researchmind-yulan run \
  --question "How should LLM refusal boundaries be evaluated?" \
  --discipline ai \
  --corpus examples/demo_corpus.json \
  --offline
```

也可以：

```bash
python -m researchmind_yulan run \
  --question "How should LLM refusal boundaries be evaluated?" \
  --discipline ai \
  --corpus examples/demo_corpus.json \
  --offline
```

运行后生成：

```text
runs/<run-id>/
├─ final_report.md
├─ audit_trail.json
├─ manifest.json
└─ stages/
   ├─ 01_question_mapper.json
   ├─ 02_search_planner.json
   ├─ 03_evidence_registry.json
   ├─ 04_literature_matrix.json
   ├─ 05_gap_detector.json
   ├─ 06_counter_evidence.json
   ├─ 07_method_audit.json
   └─ 08_stage_status.json
```

### 启用真实 LLM

复制环境变量模板：

```bash
cp .env.example .env
```

然后配置一个兼容 Chat Completions 请求格式的模型端点：

```text
RM_YULAN_LLM_ENDPOINT=...
RM_YULAN_LLM_API_KEY=...
RM_YULAN_LLM_MODEL=...
```

API Key 不应提交到仓库。

## 与原版 ResearchMind 的关系

原版 ResearchMind 聚焦“从科研历史中蒸馏顶尖学者可验证的科研判断结构”。

ResearchMind Yulan 保留这一能力，但将其作为 Deep Research Agent 的一个增强模块，而不是整个产品本身。

系统采用三层决策结构：

1. `DOMAIN_BASELINE`：目标学科自身的方法学与研究规范；
2. `SCHOLAR_LENS`：来自特定学者、具有证据支持的人物特异性判断；
3. `TRANSFER_INFERENCE`：判断某种科研决策结构能否迁移到当前问题。

目前 Scholar Advisor 尚未迁入主链，运行记录会显式标记 `scholar_advisor: not_enabled`，避免把规划中的能力写成已经实现。

## 比赛版核心模块

### 1. Research Question Mapper
把模糊主题转化为可研究的问题、冲突、证据缺口与方法风险检查方向。

### 2. Evidence Scout / Registry
当前 MVP 可对结构化 corpus 进行检索排序和证据登记；下一阶段接入真实学术来源检索与验证。

### 3. Literature Matrix
将证据按方法、结论、限制与立场结构化，而不是直接生成流水账综述。

### 4. Gap Detector
目标固定扫描五类 Research Gap：Theory / Data / Method / Context / Time。当前 MVP 已实现 evidence gap、method gap、finding conflict 和 verification gap 的最小检测器。

### 5. Skeptic / Falsification Agent
主动保留负向、混合和冲突证据，避免只围绕初步结论累积支持材料。

### 6. Method Auditor
检查方法信息缺失、实验性证据不足、证据覆盖过小等风险。后续将加入识别策略、外部有效性、Benchmark leakage 等领域规则。

### 7. Research Advisor
下一阶段迁入原 ResearchMind 的 `DOMAIN_BASELINE / SCHOLAR_LENS / TRANSFER_INFERENCE` 与 provenance 机制。

### 8. Evidence Audit Trail
每个运行实例保存完整机器可读审计记录和阶段中间产物。

## 比赛版差异化

ResearchMind Yulan 不追求“像一个大师说话”。核心差异是：

> **让每一条科研建议都尽可能回答：证据是什么？竞争性解释是什么？这条判断为什么成立？什么时候会失效？下一步应该验证什么？**

因此项目重点评测的不只是回答质量，还包括：

- Evidence Grounding
- Source Traceability
- Gap Validity
- Counter-evidence Coverage
- Decision Usefulness
- Methodological Rigor
- Unsupported Claim Rate

## 测试

仓库使用 GitHub Actions 持续集成。也可以本地运行：

```bash
python -m unittest discover -s tests -v
```

CI 除单元测试外还会执行一次 offline demo，确保 CLI 和端到端主链没有被后续修改破坏。

## 当前开发优先级

1. **P0：真实学术检索与 Evidence Registry**；
2. **P0：迁移 ResearchMind 的证据分级和 Research Advisor**；
3. **P0：10 个真实 Benchmark case + baseline + ablation**；
4. P1：可视化 Web Demo；
5. P1：比赛技术文档和 ≤10 分钟演示视频。

## 当前目录

```text
ResearchMindyulan/
├─ .github/workflows/ci.yml
├─ .env.example
├─ pyproject.toml
├─ README.md
├─ docs/
│  ├─ COMPETITION_SPEC.md
│  ├─ ARCHITECTURE.md
│  └─ BENCHMARK.md
├─ examples/
│  └─ demo_corpus.json
├─ src/researchmind_yulan/
│  ├─ __init__.py
│  ├─ __main__.py
│  ├─ cli.py
│  ├─ models.py
│  ├─ pipeline.py
│  ├─ providers.py
│  └─ stages.py
└─ tests/
   └─ test_pipeline.py
```

## 原项目

ResearchMind：<https://github.com/mindnature/researchmind>

---

**ResearchMind Yulan｜从 Deep Research 到 Research Decision Intelligence.**
