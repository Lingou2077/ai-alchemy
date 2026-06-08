"""等级阈值与称号配置（批次四结算复用）。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelDefinition:
    level: int
    min_exp: int
    title: str


LEVELS: list[LevelDefinition] = [
    LevelDefinition(1, 0, "见习炼金师"),
    LevelDefinition(2, 30, "初级炼金师"),
    LevelDefinition(3, 80, "初级炼金师"),
    LevelDefinition(4, 150, "中级炼金师"),
    LevelDefinition(5, 250, "中级炼金师"),
    LevelDefinition(6, 380, "中级炼金师"),
    LevelDefinition(7, 550, "高级炼金师"),
    LevelDefinition(8, 750, "高级炼金师"),
    LevelDefinition(9, 1000, "高级炼金师"),
    LevelDefinition(10, 1300, "大师炼金师"),
]


def level_for_exp(exp: int) -> tuple[int, str]:
    current = LEVELS[0]
    for definition in LEVELS:
        if exp >= definition.min_exp:
            current = definition
        else:
            break
    if exp >= LEVELS[-1].min_exp:
        extra_levels = (exp - LEVELS[-1].min_exp) // 400
        if extra_levels > 0:
            return LEVELS[-1].level + extra_levels, "传奇炼金师"
    return current.level, current.title


def exp_progress(exp: int) -> tuple[int, int, int]:
    """返回 (当前等级内经验, 升级所需经验, 下一级最低总经验)。"""
    level, _ = level_for_exp(exp)
    if level >= 10 and exp >= LEVELS[-1].min_exp:
        base = LEVELS[-1].min_exp
        overflow = exp - base
        segment = overflow % 400
        return segment, 400, base + ((overflow // 400) + 1) * 400

    current_def = LEVELS[0]
    next_def = LEVELS[1] if len(LEVELS) > 1 else None
    for index, definition in enumerate(LEVELS):
        if definition.level == level:
            current_def = definition
            next_def = LEVELS[index + 1] if index + 1 < len(LEVELS) else None
            break

    current_in_level = exp - current_def.min_exp
    if next_def is None:
        return current_in_level, 400, exp + 400
    required = next_def.min_exp - current_def.min_exp
    return current_in_level, required, next_def.min_exp
