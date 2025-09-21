from dotenv import load_dotenv
import click
from datetime import datetime, timedelta, timezone

load_dotenv()

from app import create_app, db
from app.models import Session

app = create_app()

@app.cli.command("update-sessions")
def update_session_statuses():
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    missed_sessions = Session.query.filter(
        Session.status == 'Upcoming',
        Session.start_time < one_hour_ago
    ).all()

    if not missed_sessions:
        click.echo("No sessions to update.")
        return

    for session in missed_sessions:
        session.status = 'Missed'
        click.echo(f"Marked session ID {session.id} for batch {session.assignment.batch.name} as Missed.")
    
    try:
        db.session.commit()
        click.echo(f"Successfully updated {len(missed_sessions)} sessions.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"An error occurred: {e}")