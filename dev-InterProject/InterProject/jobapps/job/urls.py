from django.urls import path, include
from jobapps.job import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()  # 把类实例化
router.register(prefix="", viewset=views.JobViewSet)  # 把视图集注册到这个路由实例里面

urlpatterns = [
    path("", include(router.urls))
]
