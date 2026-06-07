from fastapi import APIRouter

from schemas.question import (
    CheckAnswerRequest,
    CheckAnswerResponse,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
)
from services.question_pipeline import (
    build_generate_response,
    check_answer,
    find_question,
    run_question_pipeline,
)

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


@router.post("/generate", response_model=GenerateQuestionsResponse)
async def generate_questions(request: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    session_id, knowledge, questions, truncated = await run_question_pipeline(
        request.content,
        request.questions_per_level,
    )
    return build_generate_response(session_id, knowledge, questions, truncated)
