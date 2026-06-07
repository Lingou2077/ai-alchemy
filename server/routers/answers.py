from fastapi import APIRouter

from schemas.question import CheckAnswerRequest, CheckAnswerResponse
from services.question_pipeline import check_answer, find_question

router = APIRouter(prefix="/api/v1/answers", tags=["answers"])


@router.post("/check", response_model=CheckAnswerResponse)
async def check_user_answer(request: CheckAnswerRequest) -> CheckAnswerResponse:
    question = find_question(request.session_id, request.question_id)
    is_correct = check_answer(question, request.user_answer)
    return CheckAnswerResponse(
        is_correct=is_correct,
        explanation=question.explanation,
        correct_answer=question.answer,
    )
