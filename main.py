from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use the default (Akshare-based) configuration and optionally tweak LLM params
config = DEFAULT_CONFIG.copy()
config["deep_think_llm"] = "deepseek-chat"
config["quick_think_llm"] = "deepseek-chat"
config["max_debate_rounds"] = 1

# Example: run the pipeline on a mainland A-share ticker (Moutai)
example_ticker = "600519"
analysis_date = "2025-12-17"

# Initialize with the Akshare config
ta = TradingAgentsGraph(debug=True, config=config)

# Forward propagate through the graph
_, decision = ta.propagate(example_ticker, analysis_date)
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
