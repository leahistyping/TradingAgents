

# TradingAgents：多智能体 LLM 量化研究平台


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
