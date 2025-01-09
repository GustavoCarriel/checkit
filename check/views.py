from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from .models import Equipamento, RegistroTransacao, Usuario
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Count, F
import json
from django.db.models.functions import ExtractWeekDay





@login_required
def index(request):
    """
    View para exibir a página inicial.

    Args:
        request (HttpRequest): Objeto que contém os dados da solicitação HTTP.

    Returns:
        HttpResponse: Resposta renderizando o template 'index.html'.
    """

    # ====================================
    # Data Table
    # ====================================

    equipamentos_data = []
    # Obtem todos os equipamentos
    equipamentos = Equipamento.objects.all()
    for equipamento in equipamentos:
        if equipamento.status == 'Retirado':
            # Busca o último registro de transação do equipamento, se existir
            ultima_transacao = RegistroTransacao.objects.filter(equipamento=equipamento).order_by('-timestamp').first()

            # Se a transação for encontrada
            if ultima_transacao:
                equipamentos_data.append({
                    'id': equipamento.id,
                    'serial_number': equipamento.serial_number,
                    'modelo': equipamento.modelo,
                    'marca': equipamento.marca,
                    'status': equipamento.status,
                    'tipo_transacao': ultima_transacao.tipo,
                    'usuario': ultima_transacao.usuario_login,
                    'timestamp': ultima_transacao.timestamp,
                })
            else:
                # Caso não haja transação, preenche com dados padrão
                equipamentos_data.append({
                    'id': equipamento.id,
                    'serial_number': equipamento.serial_number,
                    'modelo': equipamento.modelo,
                    'marca': equipamento.marca,
                    'status': equipamento.status,
                    'tipo_transacao': 'Não encontrado',
                    'usuario': 'Não disponível',
                    'timestamp': 'Não disponível',
                })
        else:
            continue
    
    # Caso não haja equipamentos, adiciona uma linha indicando que não há dados
    if not equipamentos_data:
        equipamentos_data.append({
            'id': '-',
            'serial_number': '-',
            'modelo': '-',
            'marca': '-',
            'status': '-',
            'tipo_transacao': '-',
            'usuario': '-',
            'timestamp': '-',
        })


    chart_data = dashboard_view_porcentagem_modelo()
    chart_data2 = pda_retirado_por_turno()

    return render(request, 'index.html', {'equipamentos_data': equipamentos_data, 'chart_data': chart_data, 'chart_data2': chart_data2})


def custom_login(request):
    form = AuthenticationForm()  # Cria o formulário vazio por padrão

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Verifica se o usuário pertence a um grupo específico
            if user.groups.filter(name='GrupoEspecifico').exists():
                return redirect('index')

            # Redireciona com base no parâmetro 'next'
            next_url = request.GET.get('next', '')
            if next_url:
                return HttpResponseRedirect(next_url)
            else:
                return redirect('index')
        else:
            # Adiciona mensagem de erro apenas em requisições POST inválidas
            messages.error(request, "Usuário ou senha inválidos. Verifique suas credenciais e tente novamente.")

    return render(request, 'login.html', {'form': form})


@login_required
def cadastrar_usuario(request):
    """
    View para cadastrar um novo usuário no sistema.

    Args:
        request (HttpRequest): Objeto que contém os dados da solicitação HTTP.

    Returns:
        HttpResponse:
            - Redireciona para a página de cadastro com mensagem de erro, caso o login já exista.
            - Redireciona para a página inicial ou outra especificada, após cadastro bem-sucedido.
            - Renderiza o template 'cadastrar_usuario.html' em caso de requisição GET.
    """
    if request.method == 'POST':
        login_usuario = request.POST.get('login_usuario')
        nome_usuario = request.POST.get('nome_usuario')
        turno_usuario = request.POST.get('turno_usuario')
        coordenador = request.POST.get('coordenador')
        
        # Validação simples para verificar se o login já existe
        if Usuario.objects.filter(login_usuario=login_usuario).exists():
            messages.error(request, "Esse login já está em uso.")
            return redirect('cadastrar_usuario')
        
        # Cria e salva o novo usuário
        usuario = Usuario(
            login_usuario=login_usuario,
            nome_usuario=nome_usuario,
            turno_usuario=turno_usuario,
            coordenador=coordenador
        )
        usuario.save()
        
        messages.success(request, "Usuário cadastrado com sucesso!")
        return redirect('index')  # Substitua 'index' pela página de redirecionamento desejada

    return render(request, 'cadastrar_usuario.html')


@csrf_exempt
@login_required
def auto_logout(request):
    """
    Realiza logout automático do usuário.
    """
    logout(request)
    return redirect('login')  # Redirecione para a página de login



@login_required
def cadastrar_equipamentos(request):
    """
    View para cadastrar novos equipamentos no sistema.

    Args:
        request (HttpRequest): Objeto que contém os dados da solicitação HTTP.

    Returns:
        HttpResponse:
            - Redireciona para a mesma página de cadastro após salvar o equipamento com sucesso.
            - Renderiza o template 'cadastro_equipamento.html' em caso de requisição GET ou erro no cadastro.
    """
    if request.method == 'POST':
        numero_serie = request.POST.get('numeroSerialInput', '').strip()
        marca = request.POST.get('marcaEquipamentoInput', '').strip()
        modelo = request.POST.get('modeloEquipamentoInput', '').strip()
        
        # Validação para verificar campos obrigatórios
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



@login_required
def buscar_equipamentos(request):
    """
    View para buscar equipamentos pelo número de série.

    Essa função permite que o usuário busque por equipamentos no sistema utilizando o número de série.
    Se um número de série for fornecido, a busca será realizada e os equipamentos encontrados serão
    retornados para o template. Caso contrário, ou se nenhum equipamento for encontrado, uma mensagem de erro
    será exibida.

    Args:
        request (HttpRequest): Objeto que contém os dados da solicitação HTTP, incluindo qualquer parâmetro
                                de consulta enviado na URL.

    Returns:
        HttpResponse: 
            - Renderiza o template 'buscar_equipamento.html' com os resultados da busca ou mensagem de erro.
    """
    equipamentos = None  # Inicializa para evitar erro no template
    erro = None  # Variável para armazenar mensagem de erro

    # Verifica se um número de série foi enviado pelo formulário
    sn = request.GET.get('sn')
    
    if sn:
        # Tenta buscar o equipamento pelo SN (número de série)
        equipamentos = Equipamento.objects.filter(serial_number__icontains=sn)
        
        # Se não encontrar nenhum equipamento, define uma mensagem de erro
        if not equipamentos:
            erro = "Nenhum equipamento encontrado com esse número de série."

    # Renderiza o template com os resultados da busca ou a mensagem de erro
    return render(request, 'buscar_equipamento.html', {'equipamentos': equipamentos, 'erro': erro})


def buscar_usuario(login_usuario):
    """
    Busca um usuário pelo login de usuário fornecido.

    Esta função tenta localizar um usuário no banco de dados com base no login informado. Se o usuário
    for encontrado, ele é retornado. Caso contrário, a função retorna None.

    Args:
        login_usuario (str): O login do usuário a ser buscado no banco de dados.

    Returns:
        Usuario or None: O objeto Usuario correspondente ao login fornecido, se encontrado, 
                         ou None se nenhum usuário com esse login for encontrado.
    """
    try:
        usuario = Usuario.objects.get(login_usuario=login_usuario)
        return usuario
    except Usuario.DoesNotExist:
        return None
    
    
@login_required
def listar_equipamentos_em_operacao(request):
    """
    View para listar todos os equipamentos que estão em operação.

    Essa função retorna apenas os equipamentos que possuem o status "em operação"
    para serem exibidos em uma tabela no template.

    Args:
        request (HttpRequest): Objeto que contém os dados da solicitação HTTP.

    Returns:
        HttpResponse:
            - Renderiza o template 'listar_equipamentos.html' com a lista de equipamentos em operação.
    """
    # Filtra os equipamentos que estão em operação
    equipamentos_em_operacao = Equipamento.objects.filter(status='Retirado')

    # Configura o paginator para limitar a 10 equipamentos por página
    paginator = Paginator(equipamentos_em_operacao, 10)  # Alterar "10" para o número desejado por página

    # Obtém o número da página a partir dos parâmetros da URL
    page_number = request.GET.get('page')
    equipamentos_page = paginator.get_page(page_number)

    # Renderiza o template com a página atual dos equipamentos
    return render(request, 'listar_equipamentos.html', {'equipamentos': equipamentos_page})



@login_required
def retirar_equipamento(request, equipamento_id):
    """
    Realiza a retirada de um equipamento pelo usuário.

    Esta função permite que um usuário retire um equipamento, alterando o seu status para 'Retirado' 
    e registrando a transação no banco de dados. Caso o equipamento esteja disponível, o status é 
    alterado e uma transação é criada. Caso contrário, uma mensagem de erro é exibida.

    Args:
        request (HttpRequest): O objeto de requisição que contém os dados enviados pelo formulário.
        equipamento_id (int): O ID do equipamento a ser retirado.

    Returns:
        HttpResponseRedirect: Redireciona para a página inicial em caso de sucesso ou erro na operação.
    """
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)
    
    if request.method == 'POST':
        # Obtém o login do usuário do formulário
        login_usuario = request.POST.get('usuario_login')
        usuario = buscar_usuario(login_usuario)

        # Verifica se o usuário foi encontrado
        if not usuario:
            messages.error(request, f"Usuário com login '{login_usuario}' não encontrado.")
            return redirect('retirar_equipamento', equipamento_id=equipamento_id)

        # Verifica se o equipamento está disponível para retirada
        if equipamento.status == 'Disponível':
            # Atualiza o status do equipamento para "Retirado"
            equipamento.status = 'Retirado'
            equipamento.save()

            # Cria o registro de transação
            RegistroTransacao.objects.create(
                equipamento=equipamento,
                usuario_login=usuario.login_usuario,
                tipo='Retirada',
                timestamp=timezone.now()
            )

            messages.success(request, f"Equipamento {equipamento.serial_number} retirado com sucesso!")
            return redirect('index')

        # Equipamento não está disponível
        messages.error(request, f"O equipamento {equipamento.serial_number} não está disponível para retirada.")
        return redirect('retirar_equipamento', equipamento_id=equipamento_id)

    return render(request, 'retirar_equipamento.html', {'equipamento': equipamento})


@login_required
def devolver_equipamento(request, equipamento_id):
    """
    Realiza a devolução de um equipamento pelo usuário que o retirou.

    Esta função permite que um usuário devolva um equipamento, alterando o seu status para 'Disponível' 
    e registrando a transação de devolução. A devolução só é permitida se o usuário que está tentando 
    devolvê-lo for o mesmo que realizou a retirada.

    Args:
        request (HttpRequest): O objeto de requisição que contém os dados enviados pelo formulário.
        equipamento_id (int): O ID do equipamento a ser devolvido.

    Returns:
        HttpResponseRedirect: Redireciona para a página inicial em caso de sucesso ou erro na operação.
    """
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
            return redirect('index')
        else:
            # Exibe uma mensagem de erro se o login do usuário não corresponde ao da retirada
            messages.error(request, "Erro na devolução. Este equipamento só pode ser devolvido pelo usuário que o retirou.")
            return redirect('devolver_equipamento', equipamento_id=equipamento_id)

    return render(request, 'devolver_equipamento.html', {'equipamento': equipamento})


def dashboard_view_porcentagem_modelo():
    # Consulta ao banco de dados: contagem de retiradas por modelo de equipamento
    total_retiradas = RegistroTransacao.objects.filter(tipo="Retirada").count()

    # Agrupa por modelo de equipamento e conta as retiradas
    retiradas_por_modelo = (
        RegistroTransacao.objects.filter(tipo="Retirada")
        .values(modelo=F('equipamento__modelo'))  # Substitui 'equipamento__modelo' no agrupamento
        .annotate(total=Count('id'))  # Conta as retiradas por modelo
    )

    # Calcula a porcentagem de retiradas por modelo
    data = {
        "categories": [item['modelo'] for item in retiradas_por_modelo],
        "series": [
            round((item['total'] / total_retiradas) * 100, 2)
            for item in retiradas_por_modelo
        ],
    }

    # Retorna os dados como JSON
    return json.dumps(data)


def pda_retirado_por_turno():
    # Anotar o dia da semana e o turno do usuário
    registros = RegistroTransacao.objects.annotate(
        weekday=ExtractWeekDay('timestamp')
    ).values(
        'weekday', 'usuario_login'
    ).annotate(
        total=Count('id')
    )

    # Preparar os dados para o gráfico
    data = {}
    turnos = {'T1': 'Manhã', 'T2': 'Tarde', 'T3': 'Noite'}
    for registro in registros:
        weekday = registro['weekday']
        login = registro['usuario_login']
        usuario = Usuario.objects.filter(login_usuario=login).first()
        if not usuario:
            continue
        turno = usuario.turno_usuario
        total = registro['total']

        if weekday not in data:
            data[weekday] = {t: 0 for t in turnos.values()}
        data[weekday][turnos[turno]] += total

    # Organizar os dados para o Chart.js
    labels = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    chart_data = {"labels": labels, "datasets": []}
    cores = ['rgba(75, 192, 192, 1)', 'rgba(153, 102, 255, 1)', 'rgba(255, 99, 132, 1)']

    for i, turno in enumerate(turnos.values()):
        dataset = {"label": turno, "data": [], "borderColor": cores[i], "fill": False}
        for day in range(1, 8):  # Dias da semana: 1 (domingo) a 7 (sábado)
            dataset["data"].append(data.get(day, {}).get(turno, 0))
        chart_data["datasets"].append(dataset)

    return json.dumps(chart_data)