#!/bin/bash
# Script per risolvere l'errore "400 Bad Request - Request Header Or Cookie Too Large" in Airbyte
# Questo script modifica la configurazione nginx nei container Airbyte in esecuzione

set -e

echo "🔧 Fixing nginx header buffer size in Airbyte containers..."

# Verifica se Airbyte è gestito tramite abctl (Kubernetes)
KUBECONFIG="${HOME}/.airbyte/abctl/abctl.kubeconfig"
KUBECTX="kind-airbyte-abctl"

if [ -f "$KUBECONFIG" ] && kubectl --kubeconfig "$KUBECONFIG" --context "$KUBECTX" get namespace airbyte-abctl &>/dev/null; then
    echo "📦 Rilevato Airbyte gestito tramite abctl (Kubernetes)"
    
    # Fix per ingress-nginx
    echo "🔨 Applicando fix a ingress-nginx..."
    
    # Ottieni la configurazione corrente
    kubectl --kubeconfig "$KUBECONFIG" --context "$KUBECTX" get configmap ingress-nginx-controller -n ingress-nginx -o yaml > /tmp/ingress-nginx-config.yaml
    
    # Verifica se la modifica è già presente
    BUFFER_SIZE=$(kubectl --kubeconfig "$KUBECONFIG" --context "$KUBECTX" get configmap ingress-nginx-controller -n ingress-nginx -o jsonpath='{.data.client-header-buffer-size}' 2>/dev/null || echo "")
    
    if [ -n "$BUFFER_SIZE" ]; then
        echo "   ⚠️  La modifica è già presente in ingress-nginx (client-header-buffer-size: $BUFFER_SIZE)"
    else
        # Aggiungi le direttive necessarie alla configurazione
        # Per ingress-nginx, le configurazioni vengono passate come chiavi nel ConfigMap
        echo "   🔨 Applicando modifica al ConfigMap..."
        
        # Ottieni la configurazione corrente
        CURRENT_CONFIG=$(kubectl --kubeconfig "$KUBECONFIG" --context "$KUBECTX" get configmap ingress-nginx-controller -n ingress-nginx -o json)
        
        # Aggiungi le nuove configurazioni
        UPDATED_CONFIG=$(echo "$CURRENT_CONFIG" | jq '.data["client-header-buffer-size"] = "16k" | .data["large-client-header-buffers"] = "8 16k"')
        
        # Applica la modifica
        echo "$UPDATED_CONFIG" | kubectl --kubeconfig "$KUBECONFIG" --context "$KUBECTX" apply -f - || {
            # Fallback: usa patch se jq non è disponibile
            echo "   ⚠️  jq non disponibile, uso metodo alternativo..."
            kubectl --kubeconfig "$KUBECONFIG" --context "$KUBECTX" patch configmap ingress-nginx-controller -n ingress-nginx --type merge --patch '{"data":{"client-header-buffer-size":"16k","large-client-header-buffers":"8 16k"}}' || {
                echo "   ❌ Errore nell'applicare la modifica al ConfigMap"
                echo "   💡 Prova manualmente:"
                echo "      kubectl --kubeconfig $KUBECONFIG --context $KUBECTX edit configmap ingress-nginx-controller -n ingress-nginx"
                echo "      Aggiungi nel campo 'data':"
                echo "        client-header-buffer-size: \"16k\""
                echo "        large-client-header-buffers: \"8 16k\""
                exit 1
            }
        }
        
        echo "   ✅ ConfigMap aggiornato"
        
        # Riavvia il pod ingress-nginx per applicare le modifiche
        echo "   🔄 Riavviando ingress-nginx controller..."
        kubectl --kubeconfig "$KUBECONFIG" --context "$KUBECTX" rollout restart deployment ingress-nginx-controller -n ingress-nginx
        
        echo "   ⏳ Attendere che il pod si riavvii..."
        sleep 5
        
        echo "   ✅ Fix applicato a ingress-nginx"
    fi
    
    echo ""
    echo "✅ Fix completato per Airbyte (Kubernetes)!"
    echo ""
    echo "💡 Le modifiche sono state applicate a ingress-nginx"
    echo "   Il controller si riavvierà automaticamente per applicare le modifiche"
    exit 0
fi

# Fallback: cerca container Docker
echo "📦 Cercando container Docker Airbyte..."

# Trova tutti i container Airbyte che usano nginx
containers=$(docker ps --filter "name=airbyte" --format "{{.Names}}" | grep -E "(webapp|nginx)" || true)

if [ -z "$containers" ]; then
    echo "❌ Nessun container Airbyte trovato in esecuzione"
    echo "   Assicurati che Airbyte sia avviato con: abctl local start"
    exit 1
fi

for container in $containers; do
    echo "📦 Processing container: $container"
    
    # Verifica se il container ha nginx
    if docker exec "$container" test -f /etc/nginx/nginx.conf 2>/dev/null; then
        echo "   ✓ Container $container ha nginx"
        
        # Verifica se la modifica è già stata applicata
        if docker exec "$container" grep -q "client_header_buffer_size" /etc/nginx/nginx.conf 2>/dev/null; then
            echo "   ⚠️  La modifica è già presente in $container"
            continue
        fi
        
        # Applica la modifica
        echo "   🔨 Applicando modifica a $container..."
        
        # Crea uno script temporaneo nel container
        docker exec "$container" sh -c 'cat > /tmp/fix-headers.sh << '\''EOF'\''
#!/bin/sh
sed -i.bak '\''/^http {/a\
    # Increased header buffer size to handle large headers/cookies\
    client_header_buffer_size 16k;\
    large_client_header_buffers 8 16k;
'\'' /etc/nginx/nginx.conf
EOF
chmod +x /tmp/fix-headers.sh
/tmp/fix-headers.sh
rm /tmp/fix-headers.sh
'
        
        # Riavvia nginx nel container
        echo "   🔄 Riavviando nginx in $container..."
        if docker exec "$container" nginx -t 2>/dev/null; then
            docker exec "$container" nginx -s reload 2>/dev/null || {
                echo "   ⚠️  Impossibile ricaricare nginx, potrebbe essere necessario riavviare il container"
            }
            echo "   ✅ Modifica applicata con successo a $container"
        else
            echo "   ❌ Errore nella configurazione nginx, verifica i log"
        fi
    else
        echo "   ⏭️  Container $container non ha nginx, saltato"
    fi
done

echo ""
echo "✅ Fix completato!"
echo ""
echo "💡 Se il problema persiste, potrebbe essere necessario:"
echo "   1. Riavviare i container Airbyte: abctl local stop && abctl local start"
echo "   2. Oppure ricostruire l'immagine nginx con la modifica permanente"
