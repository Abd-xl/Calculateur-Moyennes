"""Configuration commune aux tests.

Les tests doivent toujours utiliser une base SQLite éphémère, jamais la base
configurée pour une application en production.
"""
import os

# Forcer une base mémoire avant que les modules de l'application soient importés.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-only-secret-key-not-for-production"
os.environ.pop("RENDER", None)
