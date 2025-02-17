from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.index, name='index'),
    path('retirar_equipamento/<int:equipamento_id>/', views.retirar_equipamento, name='retirar_equipamento'),
    path('devolver_equipamento/<int:equipamento_id>/', views.devolver_equipamento, name='devolver_equipamento'),
    path('cadastrar_equipamento/', views.cadastrar_equipamentos, name='cadastrar_equipamento'),
    path('buscar_equipamentos/', views.buscar_equipamentos, name='buscar_equipamentos'),
    path('cadastrar_usuario/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('login/', views.custom_login, name='login'),
    path('auto_logout/', views.auto_logout, name='auto_logout'),
    path('dashboard_nao_entregue/', views.dashboard_view_porcentagem_modelo, name='dashboard_view_porcentagem_modelo'),
<<<<<<< HEAD
    path('importar_excel/', views.importar_excel, name='importar_excel'),
=======
>>>>>>> b60e2b0cca2c51b86a831732c1a432c19fd3c3f8
    ]