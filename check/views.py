from django.shortcuts import render, redirect, get_object_or_404
from .models import Equipamento, RegistroTransacao
from django.utils import timezone
from django.contrib import messages


# Index
def index(request):
    return render(request, 'index.html')

def cadastrar_equipamentos(request):
    if request.method == 'POST':
        numero_serie = request.POST.get('numeroSerialInput', '').strip()
        marca = request.POST.get('marcaEquipamentoInput', '').strip()
        modelo = request.POST.get('modeloEquipamentoInput', '').strip()
        
        if not numero_serie or not marca or not modelo:
            messages.error(request, "Todos os campos são obrigatórios.")
        else:
            # Cria e salva o equipamento
            Equipamento.objects.create(
                serial_number=numero_serie,
                marca=marca,
                modelo=modelo,
                status='Disponível'
            )
            messages.success(request, "Equipamento cadastrado com sucesso!")
            return redirect('cadastrar_equipamento')  # Redireciona para limpar o formulário

    return render(request, 'cadastro_equipamento.html')

def buscar_equipamentos(request):
    equipamentos = None  # Inicializa para evitar erro no template
    erro = None  # Variável para armazenar mensagem de erro

    # Verifica se um número de série foi enviado pelo formulário
    sn = request.GET.get('sn')
    
    if sn:
        # Tenta buscar o equipamento pelo SN
        equipamentos = Equipamento.objects.filter(serial_number__icontains=sn)
        
        # Se não encontrar nenhum equipamento, define uma mensagem de erro
        if not equipamentos:
            erro = "Nenhum equipamento encontrado combuscar_equipamento.html esse número de série."

    # Renderiza o template com os resultados da busca ou a mensagem de erro
    return render(request, 'index.html', {'equipamentos': equipamentos, 'erro': erro})

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
            return redirect('index.html')
        else:
            messages.error(request, "Equipamento não está disponível.")
            return redirect('retirar_equipamento', equipamento_id=equipamento_id)

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
