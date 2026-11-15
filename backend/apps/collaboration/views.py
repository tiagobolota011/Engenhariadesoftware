from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.collaboration.models import Comment
from apps.core.api import payload, text
from apps.core.permissions import IsProductOwner
from apps.requests import serializers
from apps.requests.services import bump_version, get_request, lock_request


class CommentCreateView(APIView):
    def post(self, request: Request, pk: int) -> Response:
        data = payload(request)
        item = get_request(request.user, pk)
        body = text(data.get("body"))
        if not body:
            return Response(
                {"body": ["Write a comment first."]}, status=status.HTTP_400_BAD_REQUEST
            )
        created = Comment.objects.create(request=item, author=request.user, body=body)
        return Response(serializers.comment(created), status=status.HTTP_201_CREATED)


class DecisionView(APIView):
    """O PO marca (POST) ou retira (DELETE) a decisão de um pedido.

    Há no máximo uma decisão por pedido: marcar outro comentário move-a.
    """

    permission_classes = [IsProductOwner]

    @transaction.atomic
    def post(self, request: Request, pk: int, comment_id: int) -> Response:
        item = lock_request(request.user, pk)
        target = get_object_or_404(Comment, pk=comment_id, request=item)
        if not target.is_decision:
            moved = item.comments.filter(is_decision=True).update(is_decision=False)
            target.is_decision = True
            target.save(update_fields=["is_decision"])
            summary = "Decision changed" if moved else "Decision recorded"
            bump_version(item, request.user, summary, public=summary)
        return Response(serializers.comment(target))

    @transaction.atomic
    def delete(self, request: Request, pk: int, comment_id: int) -> Response:
        item = lock_request(request.user, pk)
        target = get_object_or_404(Comment, pk=comment_id, request=item)
        if target.is_decision:
            target.is_decision = False
            target.save(update_fields=["is_decision"])
            bump_version(item, request.user, "Decision removed", public="Decision removed")
        return Response(serializers.comment(target))
