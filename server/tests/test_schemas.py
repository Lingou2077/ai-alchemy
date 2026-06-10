from schemas.knowledge import Concept, StructuredKnowledge
from schemas.question import Option, Question, QuestionPublic
from schemas.report import AnswerRecord, ConceptNode, ReportData, WeakPoint


def test_structured_knowledge_validation():
    knowledge = StructuredKnowledge(
        topic="Go 并发",
        summary="介绍 goroutine 与 channel。",
        concepts=[Concept(name="goroutine", description="轻量线程", importance="high")],
        key_facts=["栈约 2KB"],
        misconceptions=["栈与线程相同"],
    )
    assert knowledge.topic == "Go 并发"
    assert knowledge.concepts[0].importance == "high"


def test_question_public_excludes_answer():
    question = Question(
        id="q1",
        type="single",
        difficulty="easy",
        stem="test",
        options=[Option(key="A", text="选项A")],
        answer=["A"],
        explanation="因为 A",
        concept_tags=["goroutine"],
    )
    public = QuestionPublic.from_question(question)
    assert not hasattr(public, "answer") or "answer" not in public.model_dump()


def test_report_schema_aliases():
    report = ReportData(
        sessionId="sid",
        topic="Go",
        accuracy=80.0,
        totalQuestions=5,
        correctCount=4,
        wrongCount=1,
        duration=120,
        weakPoints=[WeakPoint(name="channel", reason="答错一题")],
        summary="总结",
        suggestion="建议",
        shareTagline="Go 炼成成功！",
        conceptMastery=[
            ConceptNode(name="goroutine", mastery="mastered", relatedQuestionCount=2)
        ],
    )
    dumped = report.model_dump(by_alias=True)
    assert dumped["weakPoints"][0]["name"] == "channel"
    assert dumped["shareTagline"] == "Go 炼成成功！"
    assert dumped["conceptMastery"][0]["relatedQuestionCount"] == 2


def test_answer_record_shape():
    record = AnswerRecord(
        question_id="q1",
        user_answer=["A"],
        is_correct=True,
        time_spent=500,
    )
    assert record.time_spent == 500
