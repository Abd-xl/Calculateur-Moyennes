"""Commandes d'exploitation pour l'application Flask."""

import click

from calculateur.extensions import db
from calculateur.services.gradebook_audit import audit_gradebooks


@click.command("audit-gradebooks")
@click.option("--batch-size", type=click.IntRange(min=1), default=500, show_default=True)
@click.option("--max-issues", type=click.IntRange(min=0), default=50, show_default=True)
def audit_gradebooks_command(batch_size, max_issues):
    """Compare le JSON et les tables relationnelles sans modifier la base."""
    try:
        report = audit_gradebooks(
            db.session, batch_size=batch_size, max_issues=max_issues
        )
    finally:
        db.session.rollback()

    click.echo(f"Profils inspectés             : {report['profiles']}")
    click.echo(f"Profils initialisés           : {report['initialized_profiles']}")
    click.echo(
        "Matières JSON / relationnelles : "
        f"{report['legacy_subjects']} / {report['relational_subjects']}"
    )
    click.echo(
        "Notes JSON / relationnelles   : "
        f"{report['legacy_grades']} / {report['relational_grades']}"
    )
    click.echo(f"Profils avec écarts            : {report['profiles_with_issues']}")

    for issue in report["issues"]:
        click.echo(f"- Profil #{issue['visitor_id']}: {'; '.join(issue['details'])}")
    omitted = report["profiles_with_issues"] - len(report["issues"])
    if omitted:
        click.echo(f"... {omitted} profil(s) avec écart non affiché(s)")

    if report["issue_count"]:
        raise click.exceptions.Exit(1)
    click.echo("Audit réussi : JSON, matières, notes et moyennes concordent.")


def register_cli_commands(app):
    app.cli.add_command(audit_gradebooks_command)
