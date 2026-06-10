from config import settings
from schemas.research import EXPLORE_ALL_TOPIC_ID, TopicCandidate, WebMaterial
from services.research.context_budget import format_materials_for_prompt


def assemble_focused_document(
    user_content: str,
    candidate: TopicCandidate,
    materials: list[WebMaterial],
) -> str:
    body = format_materials_for_prompt(materials, settings.grounding_budget)
    return (
        f"## 用户原始输入\n{user_content}\n\n"
        f"## 用户确认的学习主题\n{candidate.title}: {candidate.summary}\n\n"
        f"## 联网检索摘要（请仅依据以下内容抽取知识）\n{body}"
    )


def assemble_explore_all_document(
    user_content: str,
    candidates: list[TopicCandidate],
    materials: list[WebMaterial],
) -> str:
    direction_lines = [
        f"### 方向 {index + 1}: {item.title} — {item.summary}"
        for index, item in enumerate(candidates)
    ]
    body = format_materials_for_prompt(materials, settings.grounding_budget)
    return (
        f"## 用户原始输入\n{user_content}\n\n"
        "## 学习范围：用户尚未确定方向，需广泛了解以下相关含义\n"
        + "\n".join(direction_lines)
        + "\n\n## 联网检索摘要（涵盖各方向相关材料）\n"
        + body
    )


def collect_grounding_sources(materials: list[WebMaterial]) -> list[str]:
    urls = [item.url for item in materials if item.url]
    return list(dict.fromkeys(urls))


def resolve_grounding_mode(selected_topic_id: str) -> str:
    return "explore_all" if selected_topic_id == EXPLORE_ALL_TOPIC_ID else "focused"
