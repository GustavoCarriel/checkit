from django.shortcuts import render, redirect, get_object_or_404
from .models import Equipamento, RegistroTransacao, Usuario
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

def buscar_usuario(login_usuario):
    """
    Verifica se um usuário existe pelo login.
    Retorna o usuário se encontrado, ou None se não encontrado.
    """
    try:
        usuario = Usuario.objects.get(login_usuario=login_usuario)
        return usuario
    except Usuario.DoesNotExist:
        return None


# Função para retirar equipamento
def retirar_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)
    
    if request.method == 'POST':
        login_usuario = request.POST.get('usuario_login')
        usuario = buscar_usuario(login_usuario)


        if not usuario:
            messages.error(request, "Por favor, insira o login do usuário.")
            return redirect('retirar_equipamento', equipamento_id=equipamento_id)
        
        if equipamento.status == 'Disponível':
            equipamento.status = 'Retirado'
            transacao = RegistroTransacao(
                equipamento=equipamento,
                usuario_login=usuario,
                tipo='Retirada',
                timestamp=timezone.now()
            )
            equipamento.save()
            transacao.save()
            messages.success(request, "Equipamento retirado com sucesso!")
            return redirect('index')
        else:
            messages.error(request, "Equipamento não está disponível.")
            return redirect('retirar_equipamento', equipamento_id=equipamento_id)

    return render(request, 'retirar_equipamento.html', {'equipamento': equipamento})

# Função para devolver equipamento
def devolver_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)

    if request.method == 'POST':
        login_usuario = request.POST.get('usuario_login')
        usuario = buscar_usuario(login_usuario)

        if not usuario:
            messages.error(request, "Usuário não encontrado. Por favor, insira o login correto.")
            return redirect('devolver_equipamento', equipamento_id=equipamento_id)

        # Busca a última transação de retirada para o equipamento
        transacao_retirada = RegistroTransacao.objects.filter(
            equipamento=equipamento, tipo='Retirada'
        ).order_by('-timestamp').first()

        # Verifica se o equipamento foi retirado pelo mesmo usuário
        if transacao_retirada and transacao_retirada.usuario_login == login_usuario:
            # Atualiza o status do equipamento e registra a devolução
            equipamento.status = 'Disponível'
            transacao = RegistroTransacao(
                equipamento=equipamento,
                usuario_login=login_usuario,
                tipo='Devolução',
                timestamp=timezone.now()
            )
            equipamento.save()
            transacao.save()
            messages.success(request, "Equipamento devolvido com sucesso!")
            return redirect('index')
        else:
            # Exibe uma mensagem de erro se o login do usuário não corresponde ao da retirada
            messages.error(request, "Erro na devolução. Este equipamento só pode ser devolvido pelo usuário que o retirou.")
            return redirect('devolver_equipamento', equipamento_id=equipamento_id)

    return render(request, 'devolver_equipamento.html', {'equipamento': equipamento})