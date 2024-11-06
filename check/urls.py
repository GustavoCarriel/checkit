from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('retirar_equipamento/<int:equipamento_id>/', views.retirar_equipamento, name='retirar_equipamento'),
    path('cadastrar_equipamento/', views.cadastrar_equipamentos, name='cadastrar_equipamento'),
    path('buscar_equipamentos/', views.buscar_equipamentos, name='buscar_equipamentos'),
    ]