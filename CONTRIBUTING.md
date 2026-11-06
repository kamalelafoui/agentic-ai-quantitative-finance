# Contribuer

1. Forker le dépôt.
2. Créer une branche : `git checkout -b feature/ma-contribution`.
3. Installer les dépendances : `pip install -r requirements-dev.txt`.
4. Lancer les tests : `pytest -q`.
5. Régénérer les artefacts : `python main.py demo`.
6. Ouvrir une pull request avec une description claire.

## Style

- Python 3.12, type hints, docstrings.
- Données synthétiques uniquement.
- Toute nouvelle politique de sécurité doit être testée dans `tests/test_security.py`.
- Toute nouvelle question d'évaluation doit être ajoutée à `data/questions.json` et au protocole.
