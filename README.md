<div align="center">
  <img src="assets/TauricResearch.png" style="width: 60%; height: auto;" />
</div>

<div align="center" style="line-height: 1.2;">
  <a href="https://arxiv.org/abs/2412.20138" target="_blank"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2412.20138-B31B1B?logo=arxiv"/></a>
  <a href="https://discord.com/invite/hk9PGKShPK" target="_blank"><img alt="Discord" src="https://img.shields.io/badge/Discord-TradingResearch-7289da?logo=discord&logoColor=white&color=7289da"/></a>
  <a href="./assets/wechat.png" target="_blank"><img alt="WeChat" src="https://img.shields.io/badge/WeChat-TauricResearch-brightgreen?logo=wechat&logoColor=white"/></a>
  <a href="https://x.com/TauricResearch" target="_blank"><img alt="X Follow" src="https://img.shields.io/badge/X-TauricResearch-white?logo=x&logoColor=white"/></a>
</div>

---

# TradingAgents：多智能体 LLM 量化研究平台

> 🎉 TradingAgents 全面开源！感谢社区的长期关注，我们将持续迭代，共建智能投研的新范式。

## 平台亮点与创新点

| 创新维度 | 说明 |
| --- | --- |
| **多智能体协同链路** | 分离“分析－研究－交易－风控”四条链路，所有智能体基于 LangGraph 互相质询，自动形成“观点 → 争辩 → 决策”闭环。 |
| **A 股原生支持** | 默认启用 Akshare 数据管线（东财 / 腾讯 / 财新多源），自动 fallback 至 Alpha Vantage / OpenAI，既保证国内行情实时性，也保证海外用户可复现。 |
| **可交互 CLI 战情室** | 内置 Rich Live UI + 纯文本模式，自带流程追踪、工具调用日志与决策面板，适合高频调参与教学演示。 |
| **可插拔模型策略** | 同时兼容 DeepSeek、OpenAI 与其它兼容 OpenAI API 的大模型，可针对“慢思考/快思考”分别定制模型、温度与记忆策略。 |
| **投研资产双向适配** | 提供 `TradingAgentsGraph` Python API，既能驱动实盘研究，也能嵌入回测框架，实现“LLM 研究 + 传统量化”混合策略。 |

---

## 内容索引

1. [总体架构](#总体架构)
2. [快速开始](#快速开始)
3. [CLI 使用](#cli-使用)
4. [Python 接口](#python-接口)
5. [贡献指南](#贡献指南)
6. [引用](#引用)

---

## 总体架构

<p align="center">
  <img src="assets/schema.png" style="width: 100%; height: auto;" />
</p>

- **分析智能体**：基本面（Fundamentals）、情绪（Sentiment）、新闻（News）、技术面（Technical）四位分析师分别调用 Akshare/Alpha Vantage 工具栈，形成结构化报告。
- **研究智能体**：看多与看空研究员在统一上下文中辩论，并将“关键论据 + 风险点”回传给交易员。
- **交易与风控**：Trader 聚合所有观点后生成交易提案，Risk Analyst / Risk Judge 再次审核，Portfolio Manager 给出最终裁决。
- **本地记忆与工具**：可选 chroma 记忆库、DeepSeek/ OpenAI Embedding、Akshare 数据缓存，同时支持自定义工具扩展。

---

## 快速开始

### 1. 克隆与环境

```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
conda create -n tradingagents python=3.13
conda activate tradingagents
pip install -r requirements.txt
```

### 2. 配置 API

```bash
cp .env.example .env
# 必填：OPENAI_API_KEY 或 DEEPSEEK_API_KEY
# 可选：ALPHA_VANTAGE_API_KEY（用于 fallback）
```

> ⚠️ **DeepSeek 使用说明**：  
> - Base URL 必须为 `https://api.deepseek.com/v1`（含 `/v1`），否则会提示 “Model Not Exist”。  
> - 官方仅开放 `deepseek-chat` 与 `deepseek-reasoner`，CLI/Config 中请写真实模型名。  

### 3. Mainland A-share 模式

默认配置 (`tradingagents/default_config.py`) 已启用：

- `core_stock_apis` / `technical_indicators` / `fundamental_data` → **Akshare**  
- Akshare 异常时自动回落至 Alpha Vantage / OpenAI，避免停机  
- 支持 6 位纯代码或带 `sh`/`sz` 前缀的 A 股证券代码  

如需改回海外数据，只需修改 `DEFAULT_CONFIG["data_vendors"]`。

---

## CLI 使用

启动：

```bash
python -m cli.main
```

CLI 支持两种输出模式：

1. **Rich Live UI**（默认）：适合演示，可实时看到各智能体状态。  
2. **纯文本模式**：将 `DEFAULT_CONFIG["use_rich_ui"] = False`（或 CLI 增加 `--plain`）即可获得完整文本输出，避免终端宽度截断。

CLI 功能亮点：

- 交互式选择股票、交易日、LLM、Debate 轮数、数据供应商  
- 实时显示工具调用日志（包含 fallback 信息）  
- 最终报告自动按“关键论据、风险点、交易建议”生成中文输出  
- 默认为终端展示，不再强制写入 Markdown；如需保存，可在 Config 中设置 `results_dir`

---

## Python 接口

直接在代码中调用 `TradingAgentsGraph`：

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["trade_language"] = "zh"  # 可选：全中文输出

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("600519", "2025-12-17")
print(decision)
```

可自定义：

- 模型选择：`deep_think_llm` / `quick_think_llm`
- Debate 参数：`max_debate_rounds`、`risk_review_rounds`
- 数据供应商与 fallback 策略：`data_vendors`、`fallback_config`
- 工具扩展：在 `tradingagents/dataflows` 中添加自定义工具，然后注册到 `route_to_vendor`

---

## 贡献指南

1. Fork + 创建新分支  
2. 提交前运行基础检查：`ruff check`、`pytest -q`  
3. PR 请附上修改说明（尤其是新增工具 / LLM 适配）  
4. 欢迎贡献以下方向：
   - 更多本地化数据源（港股、期货等）
   - 记忆与检索增强（RAG、Agentic Memory）
   - 多语言报告模板 / Prompt
   - CLI 与 Web 可视化

如有合作意向或想加入社区，可通过 Discord / 微信群联系我们。

---

## 引用

```
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
      title={TradingAgents: Multi-Agents LLM Financial Trading Framework}, 
      author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
      year={2025},
      eprint={2412.20138},
      archivePrefix={arXiv},
      primaryClass={q-fin.TR},
      url={https://arxiv.org/abs/2412.20138}, 
}
```

---

**TradingAgents** 将持续深耕“LLM + 投研”场景，期待与你一起构建下一代智能投研工作站。欢迎 Star 🌟、Issue 与 PR！  
