from apps.collaboration.models import Role
from apps.core.auth_views import display_name
from apps.requests.models import TRANSITIONS, FeatureRequest, Status


def assessment_of(item: FeatureRequest):
    try:
        return item.assessment
    except FeatureRequest.assessment.RelatedObjectDoesNotExist:
        return None


def summary(item: FeatureRequest, user) -> dict:
    if item.author_id == user.id:
        my_role = "created"
    elif item.voted:
        my_role = "voted"
    else:
        my_role = None
    return {
        "id": item.id,
        "key": item.key,
        "title": item.title,
        "category": {"id": item.category_id, "name": item.category.name},
        "tags": [tag.name for tag in item.tags.all()],
        "status": item.status,
        "status_label": item.get_status_display(),
        "votes": item.vote_count,
        "voted": item.voted,
        "my_role": my_role,
        "author_name": display_name(item.author),
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def comment(c) -> dict:
    membership = getattr(c.author, "membership", None)
    return {
        "id": c.id,
        "author_name": display_name(c.author),
        "author_role": membership.get_role_display() if membership else "Former member",
        "body": c.body,
        "is_decision": c.is_decision,
        "created_at": c.created_at.isoformat(),
    }


def detail(item: FeatureRequest, user) -> dict:
    role = user.membership.role
    is_po = role == Role.PRODUCT_OWNER
    is_customer = role == Role.CUSTOMER
    assessment = assessment_of(item)
    data = summary(item, user)
    data.update(
        {
            "description": item.description,
            "importance": item.importance,
            "version": item.version,
            "comments": [
                comment(c)
                for c in item.comments.select_related("author__membership").order_by(
                    "created_at", "id"
                )
            ],
            "versions": [
                {
                    "number": v.number,
                    "actor_name": display_name(v.actor),
                    "summary": v.public_summary if is_customer else v.summary,
                    "created_at": v.created_at.isoformat(),
                }
                for v in item.versions.select_related("actor")
                # Impacto, esforço e motivos de prioridade são internos: o cliente só vê
                # as alterações com resumo público.
                if v.public_summary or not is_customer
            ],
            # A avaliação é interna à equipa: os clientes não a veem.
            "assessment": None
            if is_customer
            else {
                "impact": assessment.impact if assessment else None,
                "effort": assessment.effort if assessment else None,
            },
            "can_assess": is_po,
            "next_statuses": [
                {"value": value, "label": Status(value).label}
                for value in (TRANSITIONS[item.status] if is_po else [])
            ],
        }
    )
    return data
