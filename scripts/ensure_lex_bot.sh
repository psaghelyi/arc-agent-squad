#!/bin/bash
# Ensure AWS Lex Bot exists for GRC Agent Squad
set -e

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AWS_PROFILE=${AWS_PROFILE:-acl-playground}

echo "🔍 Checking for existing AWS Lex bot..."

# First, try to find an existing bot
if bash "$SCRIPT_DIR/check_lex_bot.sh" > /dev/null 2>&1; then
  echo "✅ Found existing Lex bot"
  # Source the environment variables from the temporary file
  source .lex_bot_env
  echo "Using LEX_BOT_ID: $LEX_BOT_ID"
  echo "Using LEX_BOT_ALIAS_ID: $LEX_BOT_ALIAS_ID"
else
  echo "🤖 No existing Lex bot found, creating new one..."
  bash "$SCRIPT_DIR/create_lex_bot.sh"
  # Source the environment variables from the temporary file
  source .lex_bot_env
fi

# Output for use in scripts
echo "LEX_BOT_ID=$LEX_BOT_ID"
echo "LEX_BOT_ALIAS_ID=$LEX_BOT_ALIAS_ID" 