#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Shodan Telegram Bot — Azure Functions Deployment Script
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Prerequisites:
#    - Azure CLI installed (az)
#    - Azure Functions Core Tools installed (func)
#    - Logged in to Azure (az login)
#
#  Usage:
#    chmod +x deploy.sh
#    ./deploy.sh
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

# ─── Configuration ──────────────────────────────────────────
RESOURCE_GROUP="rg-fahmi-lab"
LOCATION="southeastasia"
STORAGE_ACCOUNT="stshodanbot$(date +%s | tail -c 6)"
FUNCTION_APP_NAME="Shodan-TelegramBot"
PYTHON_VERSION="3.12"

# ─── Colors ─────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🚀 Deploying Shodan Telegram Bot to Azure Functions ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# ─── Step 1: Check prerequisites ────────────────────────────
echo -e "\n${YELLOW}[1/7] Checking prerequisites...${NC}"
command -v az >/dev/null 2>&1 || { echo -e "${RED}❌ Azure CLI not found. Install: https://aka.ms/installazurecli${NC}"; exit 1; }
command -v func >/dev/null 2>&1 || { echo -e "${RED}❌ Azure Functions Core Tools not found. Install: npm i -g azure-functions-core-tools@4${NC}"; exit 1; }
echo -e "${GREEN}✅ Prerequisites OK${NC}"

# ─── Step 2: Create Resource Group ──────────────────────────
echo -e "\n${YELLOW}[2/7] Creating resource group: ${RESOURCE_GROUP}...${NC}"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none
echo -e "${GREEN}✅ Resource group ready${NC}"

# ─── Step 3: Create Storage Account ─────────────────────────
echo -e "\n${YELLOW}[3/7] Creating storage account: ${STORAGE_ACCOUNT}...${NC}"
az storage account create \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku Standard_LRS \
    --output none
echo -e "${GREEN}✅ Storage account ready${NC}"

# ─── Step 4: Create Function App ────────────────────────────
echo -e "\n${YELLOW}[4/7] Creating function app: ${FUNCTION_APP_NAME}...${NC}"
az functionapp create \
    --name "$FUNCTION_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --storage-account "$STORAGE_ACCOUNT" \
    --consumption-plan-location "$LOCATION" \
    --runtime python \
    --runtime-version "$PYTHON_VERSION" \
    --functions-version 4 \
    --os-type Linux \
    --output none
echo -e "${GREEN}✅ Function app created${NC}"

# ─── Step 5: Configure App Settings ─────────────────────────
echo -e "\n${YELLOW}[5/7] Configuring app settings...${NC}"
echo -e "${YELLOW}   Reading from .env file...${NC}"

# Read from .env
if [ -f .env ]; then
    TELEGRAM_TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' .env | cut -d'=' -f2-)
    SHODAN_KEY=$(grep -E '^SHODAN_API_KEY=' .env | cut -d'=' -f2-)
    AUTH_USERS=$(grep -E '^AUTHORIZED_USERS=' .env | cut -d'=' -f2-)
else
    echo -e "${RED}❌ .env file not found! Create it first.${NC}"
    exit 1
fi

if [ -z "$TELEGRAM_TOKEN" ] || [ "$TELEGRAM_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN not set in .env${NC}"
    exit 1
fi

if [ -z "$SHODAN_KEY" ] || [ "$SHODAN_KEY" = "your_shodan_api_key_here" ]; then
    echo -e "${RED}❌ SHODAN_API_KEY not set in .env${NC}"
    exit 1
fi

az functionapp config appsettings set \
    --name "$FUNCTION_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        "TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN" \
        "SHODAN_API_KEY=$SHODAN_KEY" \
        "AUTHORIZED_USERS=$AUTH_USERS" \
        "LOG_LEVEL=INFO" \
    --output none
echo -e "${GREEN}✅ App settings configured${NC}"

# ─── Step 6: Deploy Code ────────────────────────────────────
echo -e "\n${YELLOW}[6/7] Deploying code to Azure...${NC}"
func azure functionapp publish "$FUNCTION_APP_NAME" --python
echo -e "${GREEN}✅ Code deployed${NC}"

# ─── Step 7: Setup Webhook ──────────────────────────────────
echo -e "\n${YELLOW}[7/7] Setting up Telegram webhook...${NC}"

# Get function key for webhook auth
FUNC_KEY=$(az functionapp keys list \
    --name "$FUNCTION_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "functionKeys.default" -o tsv 2>/dev/null || echo "")

FUNC_URL="https://${FUNCTION_APP_NAME}.azurewebsites.net"

if [ -n "$FUNC_KEY" ]; then
    WEBHOOK_URL="${FUNC_URL}/api/webhook?code=${FUNC_KEY}"
    SETUP_URL="${FUNC_URL}/api/setup?code=${FUNC_KEY}&url=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${WEBHOOK_URL}', safe=''))")"
else
    WEBHOOK_URL="${FUNC_URL}/api/webhook"
    SETUP_URL="${FUNC_URL}/api/setup?url=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${WEBHOOK_URL}', safe=''))")"
fi

echo -e "${YELLOW}   Registering webhook...${NC}"
curl -s "$SETUP_URL" | python3 -m json.tool 2>/dev/null || echo "Setup request sent"

# ─── Done! ──────────────────────────────────────────────────
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${BLUE}Function App URL:${NC}  ${FUNC_URL}"
echo -e "  ${BLUE}Webhook URL:${NC}      ${WEBHOOK_URL}"
echo -e "  ${BLUE}Health Check:${NC}     ${FUNC_URL}/api/health"
echo ""
echo -e "  ${YELLOW}Resource Group:${NC}   ${RESOURCE_GROUP}"
echo -e "  ${YELLOW}Function App:${NC}     ${FUNCTION_APP_NAME}"
echo -e "  ${YELLOW}Storage:${NC}          ${STORAGE_ACCOUNT}"
echo -e "  ${YELLOW}Region:${NC}           ${LOCATION}"
echo ""
echo -e "  ${GREEN}Buka Telegram dan chat bot kamu! 🎉${NC}"
echo ""
echo -e "  ${YELLOW}Useful commands:${NC}"
echo -e "  • View logs:   ${BLUE}func azure functionapp logstream ${FUNCTION_APP_NAME}${NC}"
echo -e "  • Health:      ${BLUE}curl ${FUNC_URL}/api/health${NC}"
echo -e "  • Teardown:    ${BLUE}az group delete --name ${RESOURCE_GROUP} --yes${NC}"
