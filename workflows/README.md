# Workflows — QuantAgent FINAL

Deux workflows sont fournis :

| Workflow | Fichier | Usage |
|---|---|---|
| **Langflow 1.7.0** | `QuantAgent_FINAL.json` | Playground Langflow — question → API FastAPI → réponse |
| **n8n** | `QuantAgent_n8n_FINAL.json` | Automatisation webhook → API → 403/202/200 |

La vidéo de démonstration est disponible dans `docs/demo_playground.mp4` (56 s).

---

## 1. Langflow — `QuantAgent_FINAL.json`

### Importer

1. Lancer l'API QuantAgent :
   ```bash
   python main.py api
   # ou : docker compose up api
   ```
2. Ouvrir Langflow 1.7.x.
3. **New Flow → Import from JSON** → sélectionner `QuantAgent_FINAL.json`.
4. Vérifier le champ **API URL** du composant `QuantAgent API` :
   - local : `http://127.0.0.1:8000/ask`
   - Docker : `http://api:8000/ask`
5. Ouvrir le **Playground**, saisir une question et exécuter.

### Structure du flow

```text
Text Input (question)
   → Custom Component « QuantAgent API »
        → POST /ask
        → réponse JSON + statut HITL
   → Text Output (réponse)
```

Le composant appelle l'API FastAPI et ajoute une mention `[HITL]` lorsque le dossier est en attente d'approbation.

### Vidéo Playground

`docs/demo_playground.mp4` — 56 s : dashboard, formulaire, réponse chiffrée, JSON, HITL, sécurité et statistiques.

---

## 2. n8n — `QuantAgent_n8n_FINAL.json`

### Importer

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

### Endpoint

```http
POST http://localhost:5678/webhook/quantagent
Content-Type: application/json

{
  "question": "Quel est l'impact d'un choc de +100 pb sur les taux EUR ?",
  "portfolio_id": "PF-CORE-EU",
  "mode": "hybrid"
}
```

### Codes de réponse

| Situation | Code | Contenu |
|---|---:|---|
| Réponse autorisée | 200 | JSON QuantAgent complet |
| HITL requis | 202 | JSON + statut `PENDING_APPROVAL` |
| Requête bloquée | 403 | JSON de refus sécurité |
| Erreur de contrat | 500 | Message d'erreur n8n |

Le workflow ne prend jamais de décision d'exécution : il transmet le dossier à un humain et journalise la décision.
