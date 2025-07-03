#!/bin/bash
# Check for existing AWS Lex Bot for GRC Agent Squad
set -e

BOT_NAME="grc-agent-squad-bot"
REGION="us-west-2"
AWS_PROFILE=${AWS_PROFILE:-acl-playground}

echo "🔍 Checking for existing Lex bot: $BOT_NAME"

# Use aws-vault if we're not running in an environment with AWS credentials
if [[ -z "$AWS_ACCESS_KEY_ID" ]]; then
  echo "Using aws-vault with profile: $AWS_PROFILE"
  AWS_CMD="aws-vault exec $AWS_PROFILE -- aws"
else
  echo "Using existing AWS credentials"
  AWS_CMD="aws"
fi

# List bots and filter for our bot name
BOT_LIST=$($AWS_CMD lexv2-models list-bots --region $REGION --output json)
BOT_ID=$(echo $BOT_LIST | jq -r '.botSummaries[] | select(.botName == "'$BOT_NAME'") | .botId')

if [[ -z "$BOT_ID" ]]; then
  echo "❌ Bot not found: $BOT_NAME in region $REGION"
  exit 1
else
  echo "✅ Found bot: $BOT_NAME with ID: $BOT_ID in region $REGION"
  
  # Get the alias ID for this bot
  ALIAS_LIST=$($AWS_CMD lexv2-models list-bot-aliases --bot-id $BOT_ID --region $REGION --output json)
  ALIAS_ID=$(echo $ALIAS_LIST | jq -r '.botAliasSummaries[0].botAliasId')
  
  if [[ -z "$ALIAS_ID" ]]; then
    echo "❌ No alias found for bot"
    exit 1
  else
    echo "✅ Found alias with ID: $ALIAS_ID"
  fi
  
  # Output in a format suitable for .env or environment variables
  echo ""
  echo "LEX_BOT_ID=$BOT_ID"
  echo "LEX_BOT_ALIAS_ID=$ALIAS_ID"
  echo "LEX_BOT_REGION=$REGION"
  
  # Store in a temp file that can be sourced by the Makefile
  echo "export LEX_BOT_ID=$BOT_ID" > .lex_bot_env
echo "export LEX_BOT_ALIAS_ID=$ALIAS_ID" >> .lex_bot_env
echo "export LEX_BOT_REGION=$REGION" >> .lex_bot_env
fi 