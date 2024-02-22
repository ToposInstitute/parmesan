from django.urls import path
from . import views

app_name = "concepts"
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about', views.AboutView.as_view(), name='about'),
    path('search', views.SearchView.as_view(), name='search'),
]
