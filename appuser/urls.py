from django.urls import path
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from appuser.views import *


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        print(f"I was called ${user.school_id}")
        token = super().get_token(user)
        token['email'] = user.email
        token['is_superuser'] = user.is_superuser
        token['is_staff'] = user.is_staff
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['userid'] = str(uuid.UUID(str(user.id)))
        if user.school_id:
            token['school_id'] = str(uuid.UUID(str(user.school_id.id)))
        else:
            token['school_id'] = None
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


urlpatterns = [
    path('roles', RoleListView.as_view(), name="school-list"),
    path('register', AppUserCreateView.as_view(), name='register'),
    path('login', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('list', AppUserListView.as_view(), name="appuser-list"),
    path('list/schoolusers', FineAppUserListView.as_view(), name="userdetails-list"),
    path('<str:pk>', AppUserDetailView.as_view(), name="appuser-detail"),
    path('update/<str:pk>', UpdateAppUserView.as_view(), name="appuser-detail"),
]
