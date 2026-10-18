"""Migration idempotente du schéma avant de servir les requêtes."""

import logging
from threading import Lock

from alembic import command
from sqlalchemy import text

from calculateur.extensions import db
from calculateur.services.gradebook_audit import audit_gradebooks
from calculateur.services.gradebook_preflight import preflight_gradebooks

logger = logging.getLogger(__name__)
_sqlite_migration_lock = Lock()
_POSTGRES_LOCK_KEY = (1396919620, 1296648276)


def _acquire_migration_lock(connection):
    if connection.dialect.name == "postgresql":
        connection.execute(
            text("SELECT pg_advisory_lock(:namespace, :key)"),
            {"namespace": _POSTGRES_LOCK_KEY[0], "key": _POSTGRES_LOCK_KEY[1]},
        )
        connection.commit()
        return True
    _sqlite_migration_lock.acquire()
    return False


def _release_migration_lock(connection, postgres_lock):
    if postgres_lock:
        try:
            connection.execute(
                text("SELECT pg_advisory_unlock(:namespace, :key)"),
                {"namespace": _POSTGRES_LOCK_KEY[0], "key": _POSTGRES_LOCK_KEY[1]},
            )
            connection.commit()
        except Exception:
            connection.rollback()
    else:
        _sqlite_migration_lock.release()


def _format_preflight_failure(report):
    issues = report["issues"]
    details = "; ".join(
        f"profil {issue['visitor_id']}: {', '.join(issue['details'])}"
        if issue["visitor_id"] is not None
        else ", ".join(issue["details"])
        for issue in issues
    )
    omitted = report["profiles_with_issues"] - len(issues)
    if omitted:
        details += f"; {omitted} autre(s) profil(s) invalide(s)"
    return details or "les données historiques ne passent pas la validation"


def migrate_and_audit_database(app):
    """Verrouille, valide, migre puis audite avant d'autoriser le démarrage."""
    with app.app_context():
        with db.engine.connect() as lock_connection:
            postgres_lock = _acquire_migration_lock(lock_connection)
            try:
                with db.engine.connect() as connection:
                    preflight = preflight_gradebooks(connection)
                if preflight["profiles_with_issues"]:
                    raise RuntimeError(
                        "Migration automatique annulée avant toute écriture : "
                        + _format_preflight_failure(preflight)
                    )
                logger.info(
                    "Précontrôle de migration réussi : %s profils, %s matières, %s notes.",
                    preflight["profiles"],
                    preflight["subjects"],
                    preflight["grades"],
                )

                migration = app.extensions["migrate"].migrate
                config = migration.get_config()
                command.upgrade(config, "head")

                report = audit_gradebooks(db.session)
                if report["profiles_with_issues"]:
                    raise RuntimeError(
                        "Audit après migration en échec : "
                        f"{report['profiles_with_issues']} profil(s) avec "
                        f"{report['issue_count']} écart(s). "
                        "Le JSON historique est conservé dans anonymous_visitors.data."
                    )
                logger.info(
                    "Migration et audit réussis : %s profils, %s matières, %s notes.",
                    report["profiles"],
                    report["relational_subjects"],
                    report["relational_grades"],
                )
            finally:
                db.session.rollback()
                _release_migration_lock(lock_connection, postgres_lock)
