from fastapi import APIRouter, HTTPException
from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.services.sheet_manager import faq_sheet_manager

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    try:
        feedback_id = faq_sheet_manager.save_feedback(feedback)
        return FeedbackResponse(
            success=True,
            message="피드백이 성공적으로 저장되었습니다.",
            feedback_id=feedback_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
