# Workflow n8n — QuantAgent FINAL

Fichier : `QuantAgent_n8n_FINAL.json`

## Importer dans n8n

1. Lancer n8n :
   ```bash
   docker compose --profile workflow up -d n8n
   ```
   ou `npx n8n` en local.
2. Ouvrir http://localhost:5678.
3. **Workflows → Import from File** → sélectionner `QuantAgent_n8n_FINAL.json`.
4. Vérifier la variable `QUANTAGENT_API_URL` :
   - Docker : `http://api:8000/ask`
   - Local : `http://host.docker.internal:8000/ask` ou `http://localhost:8000/ask`
5. Activer le workflow.

## Endpoint

```http
POST http://localhost:5678/webhook/quantagent
Content-Type: application/json

{
  "question": "Quel est l'impact d'un choc de +100 pb sur les taux EUR ?",
  "portfolio_id": "PF-CORE-EU",
  "mode": "hybrid"
}
```

## Codes de réponse

| Situation | Code | Contenu |
|---|---:|---|
| Réponse autorisée | 200 | JSON QuantAgent complet |
| HITL requis | 202 | JSON + statut `PENDING_APPROVAL` |
| Requête bloquée | 403 | JSON de refus sécurité |
| Erreur de contrat | 500 | Message d'erreur n8n |

Le workflow ne prend jamais de décision d'exécution : il transmet le dossier à un humain et journalise la décision.
