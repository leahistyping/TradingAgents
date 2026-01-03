import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # Global fallback toggle (per-category overrides available via fallback_config)
    "enable_vendor_fallback": True,
    "fallback_config": {
        # 基本面仍优先 Akshare，但当接口异常时允许回退，避免流程直接中断
        "fundamental_data": True,
        # Akshare 某些日期可能没有新闻，允许回退避免直接报错
        "news_data": True,
    },

    # =========================
    # LLM settings (DeepSeek)
    # =========================
    "llm_provider": "deepseek",

    # 深度推理模型（用于风险讨论 / 决策辩论）
    "deep_think_llm": "deepseek-chat",

    # 快速模型（用于普通 agent response）
    "quick_think_llm": "deepseek-chat",

    "backend_url": "https://api.deepseek.com/v1",

    # =========================
    # Debate and discussion
    # =========================
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,

    # =========================
    # Data vendor configuration
    # =========================
    "data_vendors": {
        "core_stock_apis": "akshare",
        "technical_indicators": "akshare",
        "fundamental_data": "akshare",
        "news_data": "akshare",
    },

    "tool_vendors": {
        # 可留空
    },

    # =========================
    # Language / localization
    # =========================
    "language_instruction": os.getenv(
        "TRADINGAGENTS_LANGUAGE_INSTRUCTION",
        "请使用简体中文撰写所有分析、讨论和最终报告，并在必要时保留关键金融术语的英文简称。",
    ),
}
