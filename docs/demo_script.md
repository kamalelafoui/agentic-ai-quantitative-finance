# Démo — QuantAgent (5 minutes)

## 1. Lancer le dashboard

```bash
python main.py serve
```

Ouvrir **http://localhost:8007**.

## 2. Vue d'ensemble (45 s)

- Logo QuantAgent, badges du mini-projet.
- KPI : 22 documents, 105 entités, 362 relations, score 5,00/5, 8/8, JSON 100 %.
- Graphiques : allocation sectorielle, contributeurs au scénario +100 bp, utilisation des limites.
- Carte « Dernier cas de démonstration » : -8,14 M€ / -3,26 % NAV.

## 3. Agent hybride (2 min)

Menu **Agent hybride** → charger l'exemple **Q2** → **Lancer l'analyse**.

Question :

> Quel est l'impact estimé d'un choc de +100 pb sur les taux EUR pour le portefeuille Core Europe, et quelles positions contribuent le plus ?

Montrer :

- réponse chiffrée : -8,14 M€, -3,26 % NAV ;
- top contributeurs : Vonovia, EDF, Enel, Bund, AXA ;
- statut HITL : `PENDING_APPROVAL` (HITL-RISK + HITL-IC) ;
- onglet **Traçabilité JSON** : JSON complet + téléchargement ;
- onglet **Graphe de preuve** : chemins PF → positions → facteurs → politiques ;
- onglet **HITL & audit** : approuver / rejeter / escalader (simulation) ;
- onglet **Sources** : D04, D05, D21, etc.

## 4. Sécurité & Red Team (45 s)

Menu **Sécurité & Red Team** :

- 20/20 attaques bloquées ;
- 0 faux positif sur 10 requêtes bénignes ;
- tableau des attaques (injection, jailbreak, exfiltration, abus d'outils, conseil, poisoning) ;
- documents piégés isolés dans `data/attack_pack/`.

## 5. Statistiques (30 s)

Menu **Statistiques** :

- comparaison vectoriel 1,90/5 vs hybride 5,00/5 ;
- delta +3,10 ;
- détail par question ;
- validation JSON 100/100.

## 6. Workflow n8n (30 s)

Montrer `workflows/QuantAgent_n8n_FINAL.json` :

```text
Webhook → validation → API /ask → validation JSON
→ 403 sécurité / 202 HITL / 200 réponse
```

## 7. Conclusion (30 s)

- Agent hybride vecteur + graphe + quant + HITL + sécurité.
- 8/8 questions, 100/100 JSON, 20/20 attaques bloquées.
- Livrables : dashboard 8007, API 8000, notebook, Docker, DOCX/PDF, PPTX, GitHub, ZIP.

## En cas de question

- **Pourquoi pas seulement un LLM ?** Le LLM ne garantit ni le calcul, ni la traçabilité, ni le HITL. Ici, le graphe et le moteur quantitatif fournissent des preuves vérifiables.
- **Pourquoi 5,00/5 ?** Le benchmark est synthétique et contrôlé ; les 8 questions couvrent les cas prévus. Les limites sont assumées dans la documentation.
- **Comment passer en production ?** Embeddings denses, Neo4j, backtesting, alertes temps réel, audit réglementaire, signatures HITL.
