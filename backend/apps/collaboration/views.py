from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.collaboration.models import Comment
from apps.core.permissions import IsProductOwner
from apps.requests import serializers
from apps.requests.services import bump_version, get_request, lock_request


class CommentCreateView(APIView):
    def post(self, request: Request, pk: int) -> Response:
        item = get_request(request.user, pk)
        body = str(request.data.get("body") or "").strip()
        if not body:
            return Response(
                {"body": ["Write a comment first."]}, status=status.HTTP_400_BAD_REQUEST
            )
        created = Comment.objects.create(request=item, author=request.user, body=body)
        return Response(serializers.comment(created), status=status.HTTP_201_CREATED)


class DecisionView(APIView):
    """O PO marca um comentário como a decisão do pedido (no máximo uma)."""

    permission_classes = [IsProductOwner]

    @transaction.atomic
    def post(self, request: Request, pk: int, comment_id: int) -> Response:
        item = lock_request(request.user, pk)
        target = get_object_or_404(Comment, pk=comment_id, request=item)
        if item.comments.filter(is_decision=True).exclude(pk=target.pk).exists():
            return Response(
                {"detail": "This request already has a decision."}, status=status.HTTP_409_CONFLICT
            )
        if not target.is_decision:
            target.is_decision = True
            target.save(update_fields=["is_decision"])
            bump_version(item, request.user, "Decision recorded")
        return Response(serializers.comment(target))
