#!/bin/bash
echo "🧹 Cleaning unnecessary components for sandbox simulation..."

# Remove advanced systems
rm -f agent/chat_mode.py
rm -f agent/conversation_engine.py
rm -f agent/conversation_cli.py
rm -f agent/decision_maker.py
rm -f agent/wiki_query_engine.py
rm -f agent/semantic_query_engine*.py
rm -f agent/ge_strategy.py
rm -f agent/drop_rate_model.py
rm -f agent/xp_rate_model.py
rm -f agent/player_mode.py

# Remove all logs and test files
rm -f *.log
rm -f test_*.py

echo "✅ Cleaned. You are ready to refocus the project around adaptive learning AI."
