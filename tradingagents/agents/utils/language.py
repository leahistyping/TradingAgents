from tradingagents.dataflows.config import get_config


def get_language_instruction() -> str:
    """
    Fetch the language instruction configured for all agents.
    Defaults to Simplified Chinese guidance if not specified.
    """
    config = get_config()
    return config.get(
        "language_instruction",
        "请使用简体中文撰写所有分析、讨论和最终报告，并在必要时保留关键金融术语的英文简称。",
    )
