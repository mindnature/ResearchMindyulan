# Competition Specification

## 目标赛事

全球人工智能创新·治理·安全大赛

- 主办：中国人民大学高瓴人工智能学院
- 赛道：赛道一｜AI 智能体应用赛道
- 赛题：面向真实学术场景的深度研究智能体设计大赛
- 当前报名与初赛作品提交截止：2026-09-15 23:59（北京时间）
- 决赛：2026 年 10 月下旬
- 官方网站：https://www.yulan-onesim.cn/contest/

## 初赛必须交付

### 1. 技术文档

PDF 格式。

建议正文控制在 15–25 页，必须让评委快速回答五个问题：

1. 解决了什么真实科研问题？
2. 为什么现有 Deep Research / 通用 Agent 解决得不够好？
3. ResearchMind Yulan 的核心技术与流程是什么？
4. 有什么可验证实验能够证明它更好？
5. 系统是否真实可运行、可复现、可继续落地？

建议结构：

```text
01 Problem
02 Existing Limitations
03 System Overview
04 Agent Architecture
05 Evidence & Validation Mechanism
06 ResearchMind Advisor Module
07 Benchmark Design
08 Experiments & Results
09 Case Study
10 Safety / Limitations
11 Deployment & Future Work
```

### 2. 系统演示视频

- MP4
- ≤ 10 分钟

视频不是功能列表，应演示一个完整科研任务：

```text
真实研究问题
→ 普通 Deep Research 的不足
→ ResearchMind Yulan 执行
→ 找到证据冲突 / 研究 Gap
→ 方法审计
→ Advisor 决策增强
→ 输出研究路线图
→ 展示 Evidence Audit Trail
```

### 3. 代码

代码 ZIP，并附 README 运行说明。

GitHub 仓库应至少满足：

- 一条命令可运行 Demo；
- 明确依赖；
- API Key 使用 `.env.example`；
- 不提交密钥；
- 提供示例输入与预期输出；
- Benchmark 可独立运行；
- 关键输出有 JSON/Markdown 等可检查中间结果。

## 评审逆向设计

官方强调：创新性、技术可行性、系统完整性、实验真实性、落地潜力。

因此本项目按以下内部评分卡施工：

| 维度 | 内部目标 | 证据 |
|---|---:|---|
| 场景真实性 | 20 | 真实科研问题与教师/研究者案例 |
| 方法创新 | 20 | Decision Intelligence + Evidence Audit + Scholar Lens |
| 系统完整 | 20 | 可运行端到端 Agent |
| 实验真实性 | 25 | Benchmark + baseline + ablation |
| 产品与落地 | 15 | 可复用、可部署、可扩展 |

## P0 必须完成

在截止日前，以下项目缺一不可：

- [ ] 一个可运行的端到端 Deep Research pipeline
- [ ] Evidence Registry
- [ ] Literature Matrix
- [ ] 5 类 Gap Detector
- [ ] Counter-evidence / Skeptic 模块
- [ ] Method Auditor
- [ ] Research Advisor 接口
- [ ] Evidence Audit Trail
- [ ] 至少 10 个 Benchmark case
- [ ] 至少 2 个 baseline
- [ ] 至少 1 组 ablation
- [ ] 1 个完整 Golden Demo
- [ ] 技术文档
- [ ] ≤10 分钟演示视频
- [ ] 可复现运行说明

## P1 加分项

时间允许再做：

- 多学科适配；
- 多模型对比；
- Scholar Lens 自动选择；
- Web UI；
- 可视化研究图谱；
- 多智能体并行；
- Arbor adapter；
- 用户研究；
- 云端部署。

## 明确不做

截止日前避免以下范围膨胀：

- 不蒸馏几十位学者；
- 不追求完整论文写作；
- 不做复杂社交协作平台；
- 不先做华丽前端再补评测；
- 不把“生成很长的报告”当作核心能力；
- 不把所有科研流程都做成同等深度。

比赛版优先把一条链跑深、跑真、跑得可验证。
