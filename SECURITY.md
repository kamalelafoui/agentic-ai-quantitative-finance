# Sécurité

## Signaler une vulnérabilité

Ce projet est pédagogique et utilise des **données fictives**. Pour signaler un problème de sécurité :

1. ne pas ouvrir d'issue publique avec des données sensibles ;
2. contacter l'auteur : `kamal.elafoui@gmail.com` ;
3. décrire le scénario, l'impact et les étapes de reproduction.

## Périmètre

- Filtre d'entrée : injection de prompt, jailbreak, PII, exfiltration, abus d'outils.
- Isolation documentaire : `data/attack_pack/` n'est jamais indexé.
- Sortie : masquage PII, refus, JSON validé.
- Audit : `results/red_team_evidence.jsonl`.
- HITL : aucune exécution automatique d'ordre.

## Limites

- Les données sont synthétiques.
- Le mode `vector` est une **baseline d'évaluation** ; il est volontairement moins protégé pour mesurer l'apport de l'agent hybride. En production, utiliser le mode `hybrid`.
- Aucun secret réel ne doit être placé dans le dépôt.
