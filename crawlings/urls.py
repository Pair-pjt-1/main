from django.urls import path
from . import views

app_name = 'crawlings'

urlpatterns = [
    path('index/', views.index, name='index'),
    path('find/', views.find, name='find'),
    path('delete_comment/<int:pk>/', views.delete_comment, name='delete_comment'),
    path('ai_analyze/', views.ai_analyze, name='ai_analyze')
]
