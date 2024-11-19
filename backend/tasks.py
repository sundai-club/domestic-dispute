from celery import Celery
import redis
from database import SessionLocal, Dispute
from ai import result

app = Celery('tasks', broker='redis://localhost:6379/0')

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@app.task(time_limit=300)
def process_dispute(dispute_id: int):
    db = SessionLocal()
    try:
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        dispute.status = "processing"
        db.commit()

        analysis = result(
            person1={"name": dispute.party_one_name, "context": dispute.context1},
            person2={"name": dispute.party_two_name, "context": dispute.context2},
            conversation=dispute.conversation
        )

        dispute.result = analysis
        dispute.status = "completed"
        db.commit()

    except Exception as e:
        dispute.status = "failed"
        dispute.error = str(e)
        db.commit()
    finally:
        db.close() 