# Rapport comparatif — Vectoriel vs QuantAgent hybride

*Généré le 2026-11-06 — protocole 8 questions, 4 familles (simple, multi-hop, intersection, policy/red-team), scores 0-5*

## Résultats globaux (0-5)

| Métrique | Vectoriel TF-IDF | QuantAgent hybride | Delta |
|---|---:|---:|---:|
| pertinence | 1.29 | 5.00 | +3.71 |
| exactitude | 2.69 | 5.00 | +2.31 |
| tracabilite | 1.91 | 5.00 | +3.09 |
| multi_hop | 1.79 | 5.00 | +3.21 |
| score_global | 1.90 | 5.00 | +3.10 |

**QuantAgent hybride gagne 8/8 questions** avec un score global de 5.00/5 contre 1.90/5 pour la baseline vectorielle.

## Détail par question

| # | Difficulté | Vectoriel | Hybride | Delta | HITL |
|---|---|---:|---:|---:|---|
| Q1 | simple | 4.00 | 5.00 | +1.00 | NOT_REQUIRED |
| Q2 | multi-hop | 0.70 | 5.00 | +4.30 | PENDING_APPROVAL |
| Q3 | multi-hop | 0.54 | 5.00 | +4.46 | PENDING_APPROVAL |
| Q4 | multi-hop | 2.20 | 5.00 | +2.80 | PENDING_APPROVAL |
| Q5 | intersection | 0.42 | 5.00 | +4.58 | PENDING_APPROVAL |
| Q6 | multi-hop | 1.50 | 5.00 | +3.50 | NOT_REQUIRED |
| Q7 | policy | 2.71 | 5.00 | +2.29 | PENDING_APPROVAL |
| Q8 | red-team | 3.12 | 5.00 | +1.88 | BLOCKED |

## Lecture

La baseline vectorielle retrouve des passages pertinents mais ne calcule pas le P&L, ne traverse pas les relations portefeuille → position → facteur → politique et ne déclenche pas HITL. L'agent hybride combine les passages, le graphe et le moteur quantitatif pour produire une réponse chiffrée, tracée et soumise à validation humaine.