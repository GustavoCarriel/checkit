from django.shortcuts import render, redirect, get_object_or_404
from .models import Equipamento, RegistroTransacao
from django.utils import timezone
from django.contrib import messages


# Index
def index(request):
    return render(request, 'index.html')

# Função para retirar equipamento
def retirar_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)
    
    if request.method == 'POST':
        usuario_login = request.POST.get('usuario_login')  # Captura o login do usuário inserido no formulário
        
        if equipamento.status == 'Disponível':
            equipamento.status = 'Retirado'
            transacao = RegistroTransacao(
                equipamento=equipamento,
                usuario_login=usuario_login,
                tipo='Retirada',
                timestamp=timezone.now()
            )
            equipamento.save()
            transacao.save()
            messages.success(request, "Equipamento retirado com sucesso!")
            return redirect('lista_equipamentos')
        else:
            messages.error(request, "Equipamento não está disponível.")
            return redirect('lista_equipamentos')

    return render(request, 'retirar_equipamento.html', {'equipamento': equipamento})

# Função para devolver equipamento
def devolver_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)

    if request.method == 'POST':
        usuario_login = request.POST.get('usuario_login')  # Captura o login do usuário inserido no formulário

        # Verifica se o equipamento foi retirado por esse usuário
        transacao_retirada = RegistroTransacao.objects.filter(
            equipamento=equipamento, usuario_login=usuario_login, tipo='Retirada'
        ).order_by('-timestamp').first()

        if equipamento.status == 'Retirado' and transacao_retirada:
            equipamento.status = 'Disponível'
            transacao = RegistroTransacao(
                equipamento=equipamento,
                usuario_login=usuario_login,
                tipo='Devolução',
                timestamp=timezone.now()
            )
            equipamento.save()
            transacao.save()
            messages.success(request, "Equipamento devolvido com sucesso!")
            return redirect('lista_equipamentos')
        else:
            messages.error(request, "Erro na devolução. Verifique se o equipamento foi retirado por esse usuário.")
            return redirect('lista_equipamentos')

    return render(request, 'devolver_equipamento.html', {'equipamento': equipamento})
