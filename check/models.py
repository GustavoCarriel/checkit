from django.db import models
from django.utils import timezone

# Modelo de Equipamento
class Equipamento(models.Model):
    serial_number = models.CharField(max_length=50, unique=True)
    modelo = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[('Disponível', 'Disponível'), ('Retirado', 'Retirado'), ('Manutenção', 'Manutenção')], default='Disponível')

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.serial_number}"

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
