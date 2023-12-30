import uuid

from django.http import JsonResponse
from rest_framework import generics, serializers
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appuser.models import AppUser
from appuser.serializers import AppUserSerializer, UpdateAppUserSerializer
from finance import settings
from utils import SchoolIdMixin, IsSuperUser, UUID_from_PrimaryKey


class AppUserCreateView(generics.CreateAPIView):
    serializer_class = AppUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            response_data = self.perform_create(serializer)
            mypass = response_data.get('mypass', 'Password Empty')
            if settings.DEBUG:
                return Response({'detail': 'User saved successfully', 'mypass': mypass}, status=status.HTTP_201_CREATED)
            else:
                return Response({'detail': 'User saved successfully'}, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({'detail': e.detail}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        email = serializer.validated_data['email']

        qs = AppUser.objects.filter(username=email)
        if qs.exists():
            raise serializers.ValidationError({'detail': 'User already exists'})

        if serializer.is_valid():
            print("Serializer is valid. Data:")
            print(serializer.validated_data)
            user = serializer.save()
            return user
        else:
            print("Serializer is not valid. Errors:")
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppUserListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = AppUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AppUser.objects.all()
        return queryset


class AppUserDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = AppUser.objects.all()
    serializer_class = AppUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return AppUser.objects.get(id=id)
        except (ValueError, AppUser.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def patch(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school in token'}, status=401)

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({'detail': 'User updated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school in token'}, status=401)

        instance = self.get_object()
        instance.delete()
        return Response({'detail': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class FineAppUserListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = AppUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school in token'}, status=401)

        user_id = self.request.user.id
        queryset = AppUser.objects.filter(school_id=school_id, id=user_id)
        return queryset


class UpdateAppUserView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    def patch(self, request, pk):
        try:
            app_user = AppUser.objects.get(pk=pk)
        except AppUser.DoesNotExist:
            return Response({'error': 'AppUser not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateAppUserSerializer(app_user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'User updated successfully'}, status=status.HTTP_200_OK)
        return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RoleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if user_id:
            user = get_object_or_404(AppUser, id=user_id)
        else:
            user = request.user

        roles = user.roles.all() if user else []
        role_data = [{'name': role.name, 'id': role.id} for role in roles]
        return Response(role_data)
