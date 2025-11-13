
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.utils.discord_notifier import send_discord_webhook
from backend.utils.logger import logger

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackSubmission(BaseModel):
    text: str

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def submit_feedback(feedback: FeedbackSubmission):
    """
    Accepts feedback from users and sends it to a Discord channel.
    """
    if not feedback.text or len(feedback.text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback text must be at least 10 characters long."
        )

    try:
        logger.info(f"Received new feedback: {feedback.text[:50]}...")
        send_discord_webhook(feedback.text)
        return {"message": "Feedback received. Thank you!"}
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your feedback."
        )

