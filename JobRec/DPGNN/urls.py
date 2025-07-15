# recommender/urls.py

from django.urls import path
from . import views
from JobRec.DPGNN.views import recommend,index

urlpatterns = [
    path('', index, name='index'),
    path('recommend/', recommend, name='recommend'),
]
