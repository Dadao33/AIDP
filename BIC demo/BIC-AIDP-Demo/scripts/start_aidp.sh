#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export BIC_MODE=aidp
export AIDP_AGENT_CHAT_URL="${AIDP_AGENT_CHAT_URL:-https://gateway.aidp.eu-frankfurt-1.oci.oraclecloud.com/agentendpoint/6273a6c2-4e07-4e40-ab24-8a44c9475f69/chat}"
export OCI_CONFIG_PROFILE="${OCI_CONFIG_PROFILE:-DEFAULT}"
export OCI_CLI="${OCI_CLI:-oci}"
exec python3 runtime/server.py --port "${BIC_PORT:-8766}"
