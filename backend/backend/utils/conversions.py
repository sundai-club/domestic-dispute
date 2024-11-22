from database.models import Dispute
from schemas.models import DisputeResponse, ArgumentResult
import json

def dispute_to_response(db_dispute: Dispute) -> DisputeResponse:
    result = None
    if db_dispute.result:
        if isinstance(db_dispute.result, str):
            result = ArgumentResult(**json.loads(db_dispute.result))
        else:
            result = ArgumentResult(**db_dispute.result)
            
    return DisputeResponse(
        id=db_dispute.id,
        status=db_dispute.status,
        result=result,
        error=db_dispute.error
    )