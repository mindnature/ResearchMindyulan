# ResearchMind Yulan

> 面向真实学术场景的科研决策增强型 Deep Research Agent

ResearchMind Yulan 是 ResearchMind 的竞赛版，面向「全球人工智能创新·治理·安全大赛」赛道一：**面向真实学术场景的深度研究智能体设计大赛**。

它不把 Deep Research 停留在“搜索更多资料 + 生成更长报告”，而是把科研过程拆成可检查的决策链：

```text
研究问题
  ↓
证据检索与来源分级
  ↓
Literature Matrix
  ↓
Research Gap 扫描
  ↓
竞争性解释 / 反证搜索
  ↓
研究问题凝练
  ↓
方法与识别策略审计
  ↓
Research Advisor 决策增强
  ↓
研究路线图
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

## 与原版 ResearchMind 的关系

原版 ResearchMind 聚焦“从科研历史中蒸馏顶尖学者可验证的科研判断结构”。

ResearchMind Yulan 保留这一能力，但将其作为 Deep Research Agent 的一个增强模块，而不是整个产品本身。

系统采用三层决策结构：

1. `DOMAIN_BASELINE`：目标学科自身的方法学与研究规范；
2. `SCHOLAR_LENS`：来自特定学者、具有证据支持的人物特异性判断；
3. `TRANSFER_INFERENCE`：判断某种科研决策结构能否迁移到当前问题。

## 比赛版核心模块

### 1. Research Question Mapper
把模糊主题转化为可研究的问题、变量、机制、边界条件与待验证假设。

### 2. Evidence Scout
检索并建立来源登记表，记录来源类型、时间、可信等级和可回溯链接。

### 3. Literature Matrix
将文献按理论、数据、方法、样本、结论、限制和冲突证据结构化，而不是直接生成流水账综述。

### 4. Gap Detector
固定扫描五类 Research Gap：

- Theory Gap
- Data Gap
- Method Gap
- Context Gap
- Time Gap

每一个 Gap 都必须绑定证据，并接受反向检索验证。

### 5. Skeptic / Falsification Agent
主动寻找反例、替代解释、失败证据和与初步结论冲突的研究，降低确认偏误。

### 6. Method Auditor
检查研究问题与方法是否匹配，显式暴露识别假设、数据限制、Benchmark 泄漏、外部有效性等风险。

### 7. Research Advisor
调用 Generic ResearchMind 与经过证据约束的 Scholar Lens，为研究方向、实验设计和下一步行动提供决策建议。

### 8. Evidence Audit Trail
最终输出不仅给结论，还保存“这条判断来自哪里、经过了什么验证、仍存在哪些不确定性”。

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
- Hallucination / Unsupported Claim Rate

## 当前状态

`v0.1 — Competition Architecture`

当前工作重点：

1. 固定参赛问题定义与系统架构；
2. 将原版 ResearchMind 的证据审计与 Advisor 能力迁入新主流程；
3. 建立最小可运行 Deep Research Agent；
4. 建立 Benchmark 与 baseline 对照实验；
5. 完成可复现 Demo、技术文档和参赛视频。

## 目录规划

```text
ResearchMindyulan/
├─ README.md
├─ docs/
│  ├─ COMPETITION_SPEC.md
│  ├─ ARCHITECTURE.md
│  ├─ BENCHMARK.md
│  └─ DEMO_PLAN.md
├─ src/
│  ├─ agents/
│  ├─ pipeline/
│  ├─ retrieval/
│  ├─ evaluation/
│  └─ models/
├─ prompts/
├─ schemas/
├─ examples/
├─ benchmark/
├─ tests/
└─ scripts/
```

## 原项目

ResearchMind：<https://github.com/mindnature/researchmind>

---

**ResearchMind Yulan｜从 Deep Research 到 Research Decision Intelligence.**
