import django_cas_ng
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from JobRecServer.apps.user import views
from .views import CustomAuthToken
import django_cas_ng.views as cas_views

router = DefaultRouter()  # 把类实例化
router.register(prefix="", viewset=views.UserViewSet)  # 把视图集注册到这个路由实例里面

urlpatterns = [
    path('login/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('casLogin/', django_cas_ng.views.LoginView.as_view(), name='cas_ng_login'),
    # path('logout/', django_cas_ng.views.LogoutView.as_view(), name='cas_ng_logout'),
    path("", include(router.urls)),
]
