# Benchmark Plan

## Why benchmark is central

赛道一不是“做一个能聊天的科研助手”就够了。

ResearchMind Yulan 必须证明：相比普通 Deep Research / 通用大模型，它在科研判断质量上带来了可测增量。

因此比赛版评测优先于复杂 UI。

## 1. Evaluation Questions

Benchmark 重点回答 6 个问题：

1. 系统给出的关键主张是否有真实来源支撑？
2. 它识别的 Research Gap 是否经得起反向检索？
3. 它是否主动发现与初步结论冲突的证据？
4. 它能否识别方法设计中的关键假设与风险？
5. 它给出的下一步研究建议是否比 baseline 更具体、可执行？
6. Scholar Lens 是否提供了超越 Generic ResearchMind 的真实增量？

## 2. Baselines

### B0 — Single-shot LLM

输入同一个研究问题，要求模型直接输出：

- 文献综述；
- research gap；
- 方法建议；
- 下一步研究计划。

不启用 ResearchMind pipeline。

### B1 — Generic Deep Research

使用常规“多轮搜索 + 总结 + 引用”流程。

保留检索能力，但不使用：

- Literature Matrix；
- Falsification Loop；
- Method Auditor；
- Research Advisor；
- Evidence Audit Trail。

### B2 — ResearchMind Yulan Full

完整系统。

## 3. Ablation

至少做一组组件消融。

建议：

### A1 — without Skeptic

移除反证搜索，观察：

- unsupported gap rate；
- counter-evidence coverage；
- confidence calibration。

### A2 — without Method Auditor

观察方法建议中关键假设遗漏率。

### A3 — without Scholar Lens

比较 Generic Advisor 与带 Scholar Lens 的决策增量。

如果时间有限，优先做 A1。

## 4. Benchmark Cases

初赛最低目标：10 个 case。

建议分两类。

### Track A — AI / Computer Science × 5

示例：

1. LLM refusal boundary evaluation
2. Agent benchmark contamination
3. Long-context retrieval robustness
4. AI-generated scientific hypothesis evaluation
5. Multi-agent debate reliability

### Track B — Economics / Management × 5

示例：

1. AI adoption and worker productivity
2. Platform labor and algorithmic management
3. Data factor income distribution
4. AI and firm innovation
5. Generative AI and knowledge-worker task restructuring

选择 case 时必须满足：

- 有足够公开文献；
- 存在争议或方法差异；
- 可以人工核验；
- 不是靠单篇论文即可回答；
- 对研究决策有现实意义。

## 5. Metrics

### M1 Evidence Grounding Precision

抽取最终报告中的关键事实性/学术性主张。

```text
有合适证据支撑的主张数
÷
被检查的主张总数
```

### M2 Citation / Source Traceability

评审者能否从最终主张回溯到具体 EvidenceItem。

评分：0 / 1 / 2

- 0：无法追溯
- 1：可追溯但定位模糊
- 2：可追溯到具体来源与支持关系

### M3 Gap Validity

每个候选 Gap 由人工评审：

- 0：搜索失败造成的伪 Gap
- 1：有一定依据但过度表述
- 2：证据支持且边界合理

### M4 Counter-evidence Coverage

对主要结论，是否存在主动反向搜索，以及是否记录冲突证据。

```text
完成反证检查的主要结论数
÷
主要结论总数
```

### M5 Method Risk Recall

预先由领域评审者标注每个 case 的关键方法风险。

```text
系统识别的关键风险数
÷
Gold risks 总数
```

### M6 Decision Usefulness

盲评 1–5 分：

- 是否具体；
- 是否可执行；
- 是否体现优先级；
- 是否说明失败/停止条件；
- 是否减少研究者下一步的不确定性。

### M7 Unsupported Claim Rate

```text
无证据或证据不支持的关键主张
÷
关键主张总数
```

越低越好。

### M8 Research Plan Specificity

检查建议是否包含：

- 明确下一步验证任务；
- 数据需求；
- 方法选择；
- 判定标准；
- stop/continue signal。

## 6. Human Evaluation

建议至少 3 名评审者。

如果比赛时间不足，可以采用：

- 1 名领域研究者；
- 1 名另一学科研究者；
- 1 名熟悉 AI / Agent 的评审者。

所有系统输出匿名化，只显示 A/B/C，不告诉评审者是哪种方法。

## 7. Golden Demo Case

建议比赛 Demo 使用一个你最熟悉、又能体现方法价值的问题：

> 如何严谨评估 LLM 在拒答边界上的处理机制？

理由：

- 属于 AI 研究真实问题；
- 有安全/评测/行为边界交叉性；
- 容易出现定义不一致和 benchmark 设计问题；
- 很适合展示“文献多 ≠ 研究问题已经被解决”；
- 可以展示 Method Auditor 与 Skeptic 的价值。

备选 Demo：

> 生成式 AI 是否真正提高知识工作者生产率？

该题适合展示跨论文、跨情境、跨方法冲突。

## 8. Result Table

最终技术文档至少出现一张核心结果表：

| System | Grounding ↑ | Gap Validity ↑ | Counter-evidence ↑ | Method Risk Recall ↑ | Usefulness ↑ | Unsupported ↓ |
|---|---:|---:|---:|---:|---:|---:|
| B0 Single-shot | TBD | TBD | TBD | TBD | TBD | TBD |
| B1 Deep Research | TBD | TBD | TBD | TBD | TBD | TBD |
| ResearchMind Yulan | TBD | TBD | TBD | TBD | TBD | TBD |

另加一张 ablation 表，证明核心模块不是装饰。

## 9. Competition Claim Discipline

实验阶段禁止预设“ResearchMind Yulan 一定优于 baseline”。

如果某项指标没有提升：

1. 如实记录；
2. 分析失败原因；
3. 缩小能力声明；
4. 将其作为 limitation。

比赛项目的可信度来自可复现证据，不来自夸张描述。
