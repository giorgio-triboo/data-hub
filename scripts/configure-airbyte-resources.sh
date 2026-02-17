#!/bin/bash
# Script per configurare le risorse di Airbyte per migliorare le performance delle sync

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Configurazione Risorse Airbyte"
echo "=========================================="
echo ""

# Verifica che abctl sia installato
if ! command -v abctl &> /dev/null; then
    echo "❌ abctl non trovato!"
    echo "   Installa abctl: curl -LsfS https://get.airbyte.com | bash -"
    exit 1
fi

# Verifica che kubectl sia disponibile
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl non trovato!"
    exit 1
fi

KUBECONFIG="${HOME}/.airbyte/abctl/abctl.kubeconfig"
CONTEXT="kind-airbyte-abctl"
NAMESPACE="airbyte-abctl"
CONFIGMAP="airbyte-abctl-airbyte-env"

# Verifica che il cluster esista
if ! kubectl --kubeconfig "$KUBECONFIG" --context "$CONTEXT" get namespace "$NAMESPACE" &>/dev/null; then
    echo "❌ Namespace $NAMESPACE non trovato!"
    echo "   Assicurati che Airbyte sia installato: abctl local status"
    exit 1
fi

echo "📊 Configurazione attuale:"
kubectl --kubeconfig "$KUBECONFIG" --context "$CONTEXT" get configmap -n "$NAMESPACE" "$CONFIGMAP" -o jsonpath='{.data.JOB_MAIN_CONTAINER_CPU_LIMIT}' 2>/dev/null | xargs -I {} echo "   CPU Limit: {}" || echo "   CPU Limit: (non configurato)"
kubectl --kubeconfig "$KUBECONFIG" --context "$CONTEXT" get configmap -n "$NAMESPACE" "$CONFIGMAP" -o jsonpath='{.data.JOB_MAIN_CONTAINER_MEMORY_LIMIT}' 2>/dev/null | xargs -I {} echo "   Memory Limit: {}" || echo "   Memory Limit: (non configurato)"
echo ""

# Valori di default (ottimizzati per performance)
CPU_LIMIT="${AIRBYTE_CPU_LIMIT:-4}"
CPU_REQUEST="${AIRBYTE_CPU_REQUEST:-2}"
MEMORY_LIMIT="${AIRBYTE_MEMORY_LIMIT:-8Gi}"
MEMORY_REQUEST="${AIRBYTE_MEMORY_REQUEST:-4Gi}"

# Orchestrator (può essere più leggero)
ORCHESTRATOR_CPU_LIMIT="${AIRBYTE_ORCHESTRATOR_CPU_LIMIT:-2}"
ORCHESTRATOR_CPU_REQUEST="${AIRBYTE_ORCHESTRATOR_CPU_REQUEST:-1}"
ORCHESTRATOR_MEMORY_LIMIT="${AIRBYTE_ORCHESTRATOR_MEMORY_LIMIT:-4Gi}"
ORCHESTRATOR_MEMORY_REQUEST="${AIRBYTE_ORCHESTRATOR_MEMORY_REQUEST:-2Gi}"

echo "🔧 Applicazione nuove risorse:"
echo "   Source/Destination:"
echo "     CPU Limit: $CPU_LIMIT"
echo "     CPU Request: $CPU_REQUEST"
echo "     Memory Limit: $MEMORY_LIMIT"
echo "     Memory Request: $MEMORY_REQUEST"
echo "   Orchestrator:"
echo "     CPU Limit: $ORCHESTRATOR_CPU_LIMIT"
echo "     CPU Request: $ORCHESTRATOR_CPU_REQUEST"
echo "     Memory Limit: $ORCHESTRATOR_MEMORY_LIMIT"
echo "     Memory Request: $ORCHESTRATOR_MEMORY_REQUEST"
echo ""

# Applica le configurazioni
kubectl --kubeconfig "$KUBECONFIG" --context "$CONTEXT" patch configmap -n "$NAMESPACE" "$CONFIGMAP" --type merge -p "{
  \"data\": {
    \"JOB_MAIN_CONTAINER_CPU_LIMIT\": \"$CPU_LIMIT\",
    \"JOB_MAIN_CONTAINER_CPU_REQUEST\": \"$CPU_REQUEST\",
    \"JOB_MAIN_CONTAINER_MEMORY_LIMIT\": \"$MEMORY_LIMIT\",
    \"JOB_MAIN_CONTAINER_MEMORY_REQUEST\": \"$MEMORY_REQUEST\",
    \"REPLICATION_ORCHESTRATOR_CPU_LIMIT\": \"$ORCHESTRATOR_CPU_LIMIT\",
    \"REPLICATION_ORCHESTRATOR_CPU_REQUEST\": \"$ORCHESTRATOR_CPU_REQUEST\",
    \"REPLICATION_ORCHESTRATOR_MEMORY_LIMIT\": \"$ORCHESTRATOR_MEMORY_LIMIT\",
    \"REPLICATION_ORCHESTRATOR_MEMORY_REQUEST\": \"$ORCHESTRATOR_MEMORY_REQUEST\"
  }
}" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ ConfigMap aggiornato con successo!"
else
    echo "❌ Errore nell'aggiornamento del ConfigMap"
    exit 1
fi

echo ""
echo "🔄 Riavvio dei deployment per applicare le nuove configurazioni..."
kubectl --kubeconfig "$KUBECONFIG" --context "$CONTEXT" rollout restart deployment -n "$NAMESPACE" airbyte-abctl-workload-launcher > /dev/null
kubectl --kubeconfig "$KUBECONFIG" --context "$CONTEXT" rollout restart deployment -n "$NAMESPACE" airbyte-abctl-server > /dev/null

echo "✅ Deployment riavviati!"
echo ""
echo "⏳ Attendi 30-60 secondi per il completamento del rollout..."
echo ""
echo "📝 Nota: Le nuove risorse verranno applicate ai prossimi job di sync."
echo "   I job già in esecuzione continueranno con le vecchie risorse."
echo ""
echo "💡 Per personalizzare i valori, esporta le variabili prima di eseguire lo script:"
echo "   export AIRBYTE_CPU_LIMIT=8"
echo "   export AIRBYTE_MEMORY_LIMIT=16Gi"
echo "   ./scripts/configure-airbyte-resources.sh"
