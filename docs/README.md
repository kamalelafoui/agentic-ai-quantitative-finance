# Documentation — QuantAgent

Ce dossier contient les livrables de documentation et les visuels du mini-projet final.

| Fichier | Contenu |
|---|---|
| `Documentation_Agentic_AI_Quantitative_Finance.docx` | Documentation technique et fonctionnelle (Word) |
| `Documentation_Agentic_AI_Quantitative_Finance.pdf` | Version PDF de la documentation |
| `Presentation_Agentic_AI_Quantitative_Finance.pptx` | Présentation de soutenance — **5 slides** (version courte) |
| `Presentation_Agentic_AI_Quantitative_Finance.pdf` | Version PDF — 5 slides |
| `archive/Presentation_Agentic_AI_Quantitative_Finance_16slides.pptx` | Version longue archivée (16 slides) |
| `architecture_globale.png` | Architecture globale |
| `architecture_agent.png` | Boucle de l'agent en 9 étapes |
| `workflow_hitl.png` | Workflow HITL |
| `security_layers.png` | Défense en profondeur |
| `graph_overview.png` | Vue simplifiée du Knowledge Graph |
| `dashboard_home.png` | Dashboard — vue d'ensemble |
| `dashboard_agent.png` | Dashboard — formulaire et réponse |
| `dashboard_security.png` | Dashboard — sécurité et Red Team |
| `dashboard_stats.png` | Dashboard — statistiques |
| `dashboard_graph.png` | Dashboard — graphe interactif |
| `demo_playground.mp4` | Vidéo Playground — démonstration 56 s |
| `demo_playground_poster.png` | Poster de la vidéo |
| `demo_script.md` | Script de démonstration (5 minutes) |

## Régénérer

```bash
python main.py demo
python scripts/build_docs.py
python scripts/build_presentation.py
python scripts/build_notebook.py
```

La conversion PDF utilise Microsoft Word / PowerPoint (COM) ou LibreOffice selon l'environnement.

