import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response

from studium_backend.decorators import catch_and_log_exceptions
from .serializers import *

from .models import Chat

logger = logging.getLogger(__name__)


class CreateNewChat(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ChatCreateSerializer

    @catch_and_log_exceptions
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        serializer.save()

        return Response(status=status.HTTP_201_CREATED)


class ListUserChats(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ChatListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Chat.objects.filter(
            participants=user
        ).select_related().prefetch_related(
            'participants',
            'messages'
        ).distinct().order_by('-updated_at')

        return queryset

    @catch_and_log_exceptions
    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        print('Serializer_List_Chats_Data', serializer.data)
        return serializer.data
