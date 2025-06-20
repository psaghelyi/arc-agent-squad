#!/bin/bash

# Create AWS Lex Bot for GRC Agent Squad
set -e

BOT_NAME="grc-agent-squad-bot"
REGION="us-west-2"

echo "🤖 Creating AWS Lex bot: $BOT_NAME"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Create the bot
echo "Step 1: Creating bot..."
BOT_RESPONSE=$(aws lexv2-models create-bot \
    --bot-name "$BOT_NAME" \
    --description "Bot for GRC (Governance, Risk, Compliance) agent interactions" \
    --region $REGION \
    --idle-session-ttl-in-seconds 300 \
    --role-arn "arn:aws:iam::$ACCOUNT_ID:role/aws-service-role/lexv2.amazonaws.com/AWSServiceRoleForLexV2Bots" \
    --data-privacy '{"childDirected": false}' \
    --output json)

BOT_ID=$(echo $BOT_RESPONSE | jq -r '.botId')
echo "✅ Bot created with ID: $BOT_ID"

# Create bot locale
echo "Step 2: Creating bot locale..."
aws lexv2-models create-bot-locale \
    --bot-id $BOT_ID \
    --bot-version "DRAFT" \
    --locale-id "en_US" \
    --region $REGION \
    --description "English locale for GRC bot" \
    --nlu-intent-confidence-threshold 0.40 \
    --voice-settings '{"voiceId": "Joanna", "engine": "neural"}' > /dev/null

echo "✅ Bot locale created"

# Create a simple Welcome intent
echo "Step 3: Creating Welcome intent..."
aws lexv2-models create-intent \
    --bot-id $BOT_ID \
    --bot-version "DRAFT" \
    --locale-id "en_US" \
    --region $REGION \
    --intent-name "Welcome" \
    --description "Welcome intent for GRC bot" \
    --sample-utterances '[
        {"Utterance": "Hello"},
        {"Utterance": "Hi"},
        {"Utterance": "I need help"},
        {"Utterance": "Start"}
    ]' > /dev/null

echo "✅ Welcome intent created"

# Build the bot locale
echo "Step 4: Building bot locale..."
aws lexv2-models build-bot-locale \
    --bot-id $BOT_ID \
    --bot-version "DRAFT" \
    --locale-id "en_US" \
    --region $REGION > /dev/null

echo "✅ Bot build initiated"

# Wait for build to complete
echo "Step 5: Waiting for build to complete..."
while true; do
    STATUS=$(aws lexv2-models describe-bot-locale \
        --bot-id $BOT_ID \
        --bot-version "DRAFT" \
        --locale-id "en_US" \
        --region $REGION \
        --query 'botLocaleStatus' \
        --output text)
    
    echo "Build status: $STATUS"
    
    if [ "$STATUS" = "Built" ]; then
        echo "✅ Bot build completed successfully!"
        break
    elif [ "$STATUS" = "Failed" ]; then
        echo "❌ Bot build failed"
        exit 1
    else
        echo "⏳ Build in progress... waiting 10 seconds"
        sleep 10
    fi
done

# Create bot alias
echo "Step 6: Creating bot alias..."
ALIAS_RESPONSE=$(aws lexv2-models create-bot-alias \
    --bot-id $BOT_ID \
    --bot-alias-name "Development" \
    --bot-version "DRAFT" \
    --region $REGION \
    --description "Development alias for GRC bot")

ALIAS_ID=$(echo $ALIAS_RESPONSE | jq -r '.botAliasId')
echo "✅ Bot alias created with ID: $ALIAS_ID"

echo ""
echo "🎉 Lex bot creation completed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Bot ID: $BOT_ID"
echo "Alias ID: $ALIAS_ID"
echo "Region: $REGION"
echo ""
echo "📋 Next steps:"
echo "1. Add this to your .env file:"
echo "   LEX_BOT_ID=$BOT_ID"
echo "   LEX_BOT_ALIAS_ID=$ALIAS_ID"
echo ""
echo "2. Test your application:"
echo "   make local-start"
echo ""
echo "3. View bot in AWS Console:"
echo "   https://console.aws.amazon.com/lexv2/home?region=$REGION#bots" 