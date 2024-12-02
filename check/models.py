from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

# Modelo de Equipamento
class Equipamento(models.Model):
    serial_number = models.CharField(max_length=50, unique=True)
    modelo = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20, 
        choices=[('Disponível', 'Disponível'), ('Retirado', 'Retirado'), ('Manutenção', 'Manutenção')], 
        default='Disponível'
    )

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.serial_number}"


# Usuários do sistema (administradores ou operadores)
# class UsuarioSistema(AbstractUser):
#     TURNOS = [
#         ('T1', 'Manhã'),
#         ('T2', 'Tarde'),
#         ('T3', 'Noite'),
#     ]
    
#     turno_usuario = models.CharField(max_length=2, choices=TURNOS)
#     criado_em = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.username} ({self.cargo})"
    
# Modelo de Usuario
class Usuario(models.Model):
    TURNOS = [
        ('T1', 'Manhã'),
        ('T2', 'Tarde'),
        ('T3', 'Noite'),
    ]

    login_usuario = models.CharField(max_length=15, unique=True)
    nome_usuario = models.CharField(max_length=50)
    turno_usuario = models.CharField(max_length=2, choices=TURNOS)
    coordenador = models.CharField(max_length=50, blank=True, null=True)  # Ou você pode usar um relacionamento caso "coordenador" seja outro usuário

    def __str__(self):
        return f"{self.nome_usuario} ({self.login_usuario})"

# Modelo de Registro de Transações (Retirada e Devolução)
class RegistroTransacao(models.Model):
    TIPO_CHOICES = [
        ('Retirada', 'Retirada'),
        ('Devolução', 'Devolução'),
    ]
    
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE)
    usuario_login = models.CharField(max_length=50)  # Armazenamos o login como string
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.tipo} - {self.equipamento.serial_number} por {self.usuario_login} em {self.timestamp}"
