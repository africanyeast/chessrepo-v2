from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/game/<int:game_id>/pgn/', views.get_game_pgn, name='get_game_pgn'),
]