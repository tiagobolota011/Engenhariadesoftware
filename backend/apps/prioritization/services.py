from apps.requests.models import Status

# Pedidos fechados não entram na priorização.
OPEN_STATUSES = [
    Status.SUBMITTED,
    Status.UNDER_REVIEW,
    Status.APPROVED,
    Status.PLANNED,
    Status.IN_PROGRESS,
]

BASIS = (
    "Calculated by FeatureHub from votes, impact and effort "
    "(score = votes × impact ÷ effort). No external AI service is used."
)


def score(votes: int, impact: int | None, effort: int | None) -> float | None:
    """Pontuação = votos × impacto ÷ esforço; None enquanto faltar uma estimativa."""
    if not impact or not effort:
        return None
    return round(votes * impact / effort, 1)


def _assessment(item):
    try:
        return item.assessment
    except type(item).assessment.RelatedObjectDoesNotExist:
        return None


def row(item) -> dict:
    assessment = _assessment(item)
    impact = assessment.impact if assessment else None
    effort = assessment.effort if assessment else None
    manual_rank = assessment.manual_rank if assessment else None
    return {
        "id": item.id,
        "key": item.key,
        "title": item.title,
        "category": item.category.name,
        "votes": item.vote_count,
        "impact": impact,
        "effort": effort,
        "score": score(item.vote_count, impact, effort),
        "manual": manual_rank is not None,
        "manual_rank": manual_rank,
        "override_reason": assessment.override_reason if assessment else "",
    }


def by_score(rows: list[dict]) -> list[dict]:
    """Ordem calculada: pontuação decrescente; sem estimativa fica no fim."""
    return sorted(
        rows,
        key=lambda r: (r["score"] is None, -(r["score"] or 0), -r["votes"], r["id"]),
    )


def ranked(rows: list[dict]) -> list[dict]:
    """Ordem final: a calculada, com as posições manuais do PO por cima."""
    result = by_score([r for r in rows if not r["manual"]])
    for manual in sorted(
        (r for r in rows if r["manual"]), key=lambda r: (r["manual_rank"], r["id"])
    ):
        result.insert(min(manual["manual_rank"], len(result)), manual)
    return result


def explain(r: dict) -> str:
    if r["score"] is None:
        return "Needs an impact and effort estimate first."
    votes = "1 vote" if r["votes"] == 1 else f"{r['votes']} votes"
    return f"Score {r['score']}: {votes} × impact {r['impact']} ÷ effort {r['effort']} pts."
