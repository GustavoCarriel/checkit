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
from django.db.models import Count, F, Max
import json
from django.db.models.functions import ExtractWeekDay
from datetime import timedelta




@login_required
def index(request):
    """
    View para exibir a página inicial.

    Args:
        request (HttpRequest): Objeto que contém os dados da solicitação HTTP.

    Returns:
        HttpResponse: Resposta renderizando o template 'index.html' com os dados necessários.
    """
    # ====================================
    # Data Table
    # ====================================
    equipamentos_data = []  # Lista para armazenar informações dos equipamentos.

    # Obtém todos os equipamentos cadastrados no banco de dados.
    equipamentos = Equipamento.objects.all()
    for equipamento in equipamentos:
        if equipamento.status == 'Retirado':  # Verifica se o equipamento está retirado.
            # Busca a última transação registrada para o equipamento, ordenada pela data (mais recente primeiro).
            ultima_transacao = RegistroTransacao.objects.filter(equipamento=equipamento).order_by('-timestamp').first()

            # Se a transação mais recente for encontrada, adiciona seus dados à lista.
            if ultima_transacao:
                equipamentos_data.append({
                    'id': equipamento.id,  # ID único do equipamento.
                    'serial_number': equipamento.serial_number,  # Número serial do equipamento.
                    'modelo': equipamento.modelo,  # Modelo do equipamento.
                    'marca': equipamento.marca,  # Marca do equipamento.
                    'status': equipamento.status,  # Status atual do equipamento (neste caso, 'Retirado').
                    'tipo_transacao': ultima_transacao.tipo,  # Tipo da última transação (ex.: retirada ou devolução).
                    'usuario': ultima_transacao.usuario_login,  # Usuário associado à última transação.
                    'timestamp': ultima_transacao.timestamp,  # Data e hora da última transação.
                })
            else:
                # Caso não exista transação registrada, preenche com valores padrão.
                equipamentos_data.append({
                    'id': equipamento.id,
                    'serial_number': equipamento.serial_number,
                    'modelo': equipamento.modelo,
                    'marca': equipamento.marca,
                    'status': equipamento.status,
                    'tipo_transacao': 'Não encontrado',  # Indica ausência de transação.
                    'usuario': 'Não disponível',  # Indica que o usuário não está disponível.
                    'timestamp': 'Não disponível',  # Indica que a data/hora não está disponível.
                })
        else:
            continue  # Ignora equipamentos que não estão no status "Retirado".

    # Caso nenhum equipamento esteja na lista, adiciona uma linha indicando ausência de dados.
    if not equipamentos_data:
        equipamentos_data.append({
            'id': '-',  # Valor padrão indicando que não há dados.
            'serial_number': '-',
            'modelo': '-',
            'marca': '-',
            'status': '-',
            'tipo_transacao': '-',
            'usuario': '-',
            'timestamp': '-',
        })

    # ====================================
    # Dashboard Data
    # ====================================
    # Obtém informações gerais para os cards do dashboard.
    data_dashboard_info = dashboard_info_view()

    # Obtém dados para o gráfico de porcentagem por modelo.
    data_view_porcentagem = dashboard_view_porcentagem_modelo()

    # Obtém dados sobre PDAs retirados por turno.
    data_pda_por_turno = pda_retirado_por_turno()

    # Obtém dados adicionais para o controle de PDAs.
    data_pda_controle = dashboard_view_pda()

    # ====================================
    # Renderização do Template
    # ====================================
    # Renderiza o template 'index.html', passando os dados necessários.
    return render(
        request,
        'index.html',
        {
            "data_dashboard_info": data_dashboard_info,  # Informações dos cards do dashboard.
            "equipamentos_data": equipamentos_data,  # Dados da tabela de equipamentos.
            "chart_data_porcentagem": data_view_porcentagem,  # Dados do gráfico de porcentagem.
            "chart_data_por_turno": data_pda_por_turno,  # Dados sobre PDAs por turno.
            "data_pda_controle": data_pda_controle,  # Dados adicionais para controle de PDAs.
        }
    )


def custom_login(request):
    """
    View para gerenciar o login do usuário.

    Args:
        request (HttpRequest): Objeto que contém os dados da solicitação HTTP.

    Returns:
        HttpResponse: Renderiza o template 'login.html' ou redireciona para outra página, dependendo da autenticação.
    """
    # Cria um formulário de autenticação vazio por padrão.
    form = AuthenticationForm()

    if request.method == 'POST':  # Verifica se a solicitação é do tipo POST (tentativa de login).
        # Popula o formulário com os dados enviados pelo usuário.
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():  # Verifica se os dados fornecidos no formulário são válidos.
            user = form.get_user()  # Obtém o usuário autenticado a partir do formulário.
            login(request, user)  # Realiza o login do usuário.

            # Verifica se o usuário pertence a um grupo específico.
            if user.groups.filter(name='GrupoEspecifico').exists():
                # Redireciona para a página inicial se o usuário pertence ao grupo.
                return redirect('index')

            # Obtém a URL de redirecionamento do parâmetro 'next' (caso exista).
            next_url = request.GET.get('next', '')
            if next_url:
                # Redireciona para a URL especificada no parâmetro 'next'.
                return HttpResponseRedirect(next_url)
            else:
                # Caso não haja parâmetro 'next', redireciona para a página inicial.
                return redirect('index')
        else:
            # Adiciona uma mensagem de erro caso o formulário seja inválido (ex.: credenciais incorretas).
            messages.error(
                request,
                "Usuário ou senha inválidos. Verifique suas credenciais e tente novamente."
            )

    # Renderiza o template de login, enviando o formulário (vazio ou com erros).
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
            - Redireciona para a página inicial (ou outra página especificada) após cadastro bem-sucedido.
            - Renderiza o template 'cadastrar_usuario.html' em caso de requisição GET.
    """
    if request.method == 'POST':  # Verifica se a solicitação é do tipo POST (dados do formulário enviados).
        # Obtém os dados enviados pelo formulário.
        login_usuario = request.POST.get('login_usuario')  # Login do novo usuário.
        nome_usuario = request.POST.get('nome_usuario')  # Nome completo do usuário.
        turno_usuario = request.POST.get('turno_usuario')  # Turno associado ao usuário.
        coordenador = request.POST.get('coordenador')  # Coordenador responsável pelo usuário.

        # Valida se o login informado já existe no banco de dados.
        if Usuario.objects.filter(login_usuario=login_usuario).exists():
            # Caso o login já esteja em uso, exibe uma mensagem de erro e redireciona para a página de cadastro.
            messages.error(request, "Esse login já está em uso.")
            return redirect('cadastrar_usuario')

        # Cria uma nova instância do modelo Usuario com os dados fornecidos.
        usuario = Usuario(
            login_usuario=login_usuario,
            nome_usuario=nome_usuario,
            turno_usuario=turno_usuario,
            coordenador=coordenador
        )
        # Salva o novo usuário no banco de dados.
        usuario.save()

        # Adiciona uma mensagem de sucesso ao contexto.
        messages.success(request, "Usuário cadastrado com sucesso!")

        # Redireciona para a página inicial ou outra página especificada.
        return redirect('index')  # Substitua 'index' pela URL do redirecionamento desejado.

    # Para requisições do tipo GET, renderiza o template de cadastro de usuário.
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
    if request.method == 'POST':  # Verifica se a requisição é do tipo POST
        # Obtém os valores dos campos enviados pelo formulário
        numero_serie = request.POST.get('numeroSerialInput', '').strip()  # Número de série do equipamento
        marca = request.POST.get('marcaEquipamentoInput', '').strip()  # Marca do equipamento
        modelo = request.POST.get('modeloEquipamentoInput', '').strip()  # Modelo do equipamento
        
        # Validação dos campos obrigatórios
        if not numero_serie or not marca or not modelo:
            # Exibe uma mensagem de erro se algum campo obrigatório estiver vazio
            messages.error(request, "Todos os campos são obrigatórios.")
        else:
            # Cria e salva o novo equipamento no banco de dados
            Equipamento.objects.create(
                serial_number=numero_serie,  # Armazena o número de série
                marca=marca,  # Armazena a marca do equipamento
                modelo=modelo,  # Armazena o modelo do equipamento
                status='Disponível'  # Define o status inicial como 'Disponível'
            )
            # Exibe uma mensagem de sucesso após o cadastro
            messages.success(request, "Equipamento cadastrado com sucesso!")
            # Redireciona para a mesma página para limpar o formulário
            return redirect('cadastrar_equipamento')

    # Para requisições do tipo GET ou em caso de erro, renderiza o template de cadastro
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
    equipamentos = None  # Inicializa para evitar erro no template caso nenhum equipamento seja encontrado
    erro = None  # Variável para armazenar uma mensagem de erro, se necessário

    # Verifica se o parâmetro 'sn' (serial number) foi enviado via GET
    sn = request.GET.get('sn')  # Obtém o valor de 'sn' dos parâmetros de consulta

    if sn:  # Se um número de série foi fornecido
        # Realiza a busca por equipamentos que contenham o número de série fornecido
        equipamentos = Equipamento.objects.filter(serial_number__icontains=sn)
        
        # Caso nenhum equipamento seja encontrado, define uma mensagem de erro
        if not equipamentos:
            erro = "Nenhum equipamento encontrado com esse número de série."
    else:
        # Define uma mensagem de erro caso nenhum número de série seja fornecido
        erro = "Por favor, insira um número de série para realizar a busca."

    # Renderiza o template 'buscar_equipamento.html' com os dados dos equipamentos ou a mensagem de erro
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
    (ou seja, equipamentos com o status 'Retirado') para serem exibidos em uma tabela no template.
    Além disso, utiliza paginação para limitar o número de itens exibidos por página.

    Args:
        request (HttpRequest): Objeto que contém os dados da solicitação HTTP.

    Returns:
        HttpResponse:
            - Renderiza o template 'listar_equipamentos.html' com a lista paginada de equipamentos em operação.
    """
    # Filtra os equipamentos com o status "Retirado", indicando que estão em operação
    equipamentos_em_operacao = Equipamento.objects.filter(status='Retirado')

    # Configura a paginação para exibir 10 equipamentos por página (pode ajustar o valor conforme necessário)
    paginator = Paginator(equipamentos_em_operacao, 10)

    # Obtém o número da página atual a partir do parâmetro 'page' na URL
    page_number = request.GET.get('page')  # Retorna None caso o parâmetro não esteja presente
    equipamentos_page = paginator.get_page(page_number)  # Obtém a página atual dos equipamentos

    # Renderiza o template 'listar_equipamentos.html' passando os dados paginados
    return render(request, 'listar_equipamentos.html', {'equipamentos': equipamentos_page})


@login_required
def retirar_equipamento(request, equipamento_id):
    """
    Realiza a retirada de um equipamento pelo usuário.

    Esta função permite que um usuário retire um equipamento, alterando o seu status para 'Retirado' 
    e registrando a transação no banco de dados. Caso o equipamento esteja disponível, o status é 
    atualizado e uma nova transação é criada. Caso contrário, uma mensagem de erro é exibida.

    Args:
        request (HttpRequest): 
            Objeto que contém os dados da solicitação HTTP, incluindo os dados enviados pelo formulário.
        equipamento_id (int): 
            O ID do equipamento a ser retirado.

    Returns:
        HttpResponseRedirect: 
            - Redireciona para a página inicial ('index') após o sucesso ou falha da operação.
            - Renderiza o template 'retirar_equipamento.html' em caso de requisição GET.

    Fluxo de Execução:
        1. **Obtém o Equipamento:**
           - Busca o equipamento pelo `equipamento_id`. Se não for encontrado, retorna uma página 404.

        2. **Validação do Método HTTP:**
           - Se o método for `POST`, processa a retirada do equipamento.
           - Caso contrário, renderiza o formulário de retirada.

        3. **Validações na Retirada:**
           - Verifica se o login do usuário fornecido está registrado no sistema.
           - Certifica-se de que o equipamento está disponível para retirada.
        
        4. **Atualização do Equipamento e Registro de Transação:**
           - Atualiza o status do equipamento para 'Retirado'.
           - Cria um registro de transação no banco de dados, associando o equipamento ao usuário.

        5. **Mensagens de Feedback:**
           - Exibe mensagens de sucesso ou erro dependendo do estado do equipamento ou da validação.

    Variáveis Locais:
        - equipamento (Equipamento): Instância do equipamento associado ao ID fornecido.
        - login_usuario (str): Login do usuário fornecido no formulário.
        - usuario (Usuario): Instância do usuário obtida pela função `buscar_usuario`.
        - login_registrado (str): Nome de usuário da conta autenticada que realizou a operação.

    Exceções:
        - Retorna uma página 404 se o equipamento não for encontrado.

    Templates:
        - 'retirar_equipamento.html': Exibido em caso de requisição GET ou erro de validação.

    Exemplo de Uso:
        - Um técnico autenticado acessa o formulário, insere o login do usuário responsável e confirma a retirada.
        - Após sucesso, o equipamento é marcado como 'Retirado' e uma transação é registrada.
    """
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)
    
    if request.method == 'POST':
        # Obtém o login do usuário do formulário
        login_usuario = request.POST.get('usuario_login')
        usuario = buscar_usuario(login_usuario)
        login_registrado = request.user.username

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
                login_registrado=login_registrado,
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
    e registrando a transação de devolução no banco de dados. A devolução só é permitida se o usuário que 
    está tentando devolvê-lo for o mesmo que realizou a retirada.

    Args:
        request (HttpRequest): 
            O objeto de requisição que contém os dados enviados pelo formulário.
        equipamento_id (int): 
            O ID do equipamento a ser devolvido.

    Returns:
        HttpResponseRedirect: 
            - Redireciona para a página inicial ('index') após sucesso ou falha na operação.
            - Renderiza o template 'devolver_equipamento.html' em caso de requisição GET.

    Fluxo de Execução:
        1. **Obtém o Equipamento:**
           - Busca o equipamento pelo `equipamento_id`. Se não for encontrado, retorna uma página 404.

        2. **Validação do Método HTTP:**
           - Se o método for `POST`, processa a devolução do equipamento.
           - Caso contrário, renderiza o formulário de devolução.

        3. **Validações na Devolução:**
           - Verifica se o login do usuário fornecido está registrado no sistema.
           - Certifica-se de que o usuário tentando devolver é o mesmo que realizou a retirada.

        4. **Atualização do Equipamento e Registro de Transação:**
           - Atualiza o status do equipamento para 'Disponível'.
           - Cria um registro de transação no banco de dados, associando o equipamento ao usuário.

        5. **Mensagens de Feedback:**
           - Exibe mensagens de sucesso ou erro dependendo da validação do usuário e do estado do equipamento.

    Variáveis Locais:
        - equipamento (Equipamento): Instância do equipamento associado ao ID fornecido.
        - login_usuario (str): Login do usuário fornecido no formulário.
        - usuario (Usuario): Instância do usuário obtida pela função `buscar_usuario`.
        - login_registrado (str): Nome de usuário da conta autenticada que realizou a operação.
        - transacao_retirada (RegistroTransacao): Última transação de retirada associada ao equipamento.

    Exceções:
        - Retorna uma página 404 se o equipamento não for encontrado.

    Templates:
        - 'devolver_equipamento.html': Exibido em caso de requisição GET ou erro de validação.

    Exemplo de Uso:
        - Um técnico acessa o formulário, insere o login do usuário responsável e confirma a devolução.
        - Após sucesso, o equipamento é marcado como 'Disponível' e uma transação de devolução é registrada.
    """
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)

    if request.method == 'POST':
        login_usuario = request.POST.get('usuario_login')
        usuario = buscar_usuario(login_usuario)
        login_registrado = request.user.username

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
                login_registrado=login_registrado,
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
    """
    Gera dados para um gráfico de porcentagem de retiradas por modelo de equipamento.

    Esta função consulta o banco de dados para calcular a quantidade de retiradas de equipamentos,
    agrupadas por modelo. Os dados são formatados para serem utilizados em gráficos, como aqueles
    criados com bibliotecas de visualização de dados.

    Args:
        Nenhum argumento é necessário, pois os dados são obtidos diretamente do banco de dados.

    Returns:
        str:
            Uma string JSON contendo:
            - "categories": Uma lista de modelos de equipamentos retirados.
            - "series": Uma lista de porcentagens que representa a proporção de retiradas de cada modelo.

    Fluxo de Execução:
        1. **Consulta ao Banco de Dados:**
           - Filtra as transações do tipo "Retirada".
           - Conta o número total de retiradas.

        2. **Agrupamento por Modelo:**
           - Agrupa as retiradas pelo campo `equipamento__modelo`.
           - Conta o número de retiradas para cada modelo.

        3. **Cálculo da Porcentagem:**
           - Calcula a porcentagem de retiradas para cada modelo com base no total de retiradas.

        4. **Formatação para Gráficos:**
           - Organiza os modelos como categorias ("categories").
           - Insere as porcentagens em uma lista ("series").

    Exemplo de Saída:
        Se houver os seguintes registros:
            - Modelo A: 50 retiradas.
            - Modelo B: 30 retiradas.
            - Modelo C: 20 retiradas.
        O JSON retornado será:
        ```json
        {
            "categories": ["Modelo A", "Modelo B", "Modelo C"],
            "series": [50.0, 30.0, 20.0]
        }
        ```

    Notas:
        - A porcentagem é arredondada para duas casas decimais.
        - Se não houver retiradas no banco de dados, as listas retornadas serão vazias.

    Requisitos:
        - O modelo `RegistroTransacao` deve ter os seguintes campos:
          - `tipo` (str): Indica o tipo da transação (ex.: "Retirada").
          - `equipamento__modelo` (str): O modelo do equipamento associado à transação.

    Dependências:
        - `RegistroTransacao` (modelo do Django).
        - `F` e `Count` (utilitários do Django ORM).
        - `json.dumps` para converter o dicionário em uma string JSON.

    """
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
    """
    Gera dados para um gráfico que exibe o número de equipamentos retirados por turno ao longo da semana.

    Esta função filtra os registros de retirada, identifica o dia da semana e agrupa os dados pelo turno
    do usuário associado. Os resultados são organizados no formato esperado por bibliotecas de gráficos
    como Chart.js.

    Args:
        Nenhum argumento é necessário, pois os dados são obtidos diretamente do banco de dados.

    Returns:
        str:
            Uma string JSON contendo:
            - "labels": Lista de nomes dos dias da semana ("Dom", "Seg", ..., "Sab").
            - "datasets": Lista de dicionários, onde cada dicionário representa um turno e contém:
              - "label": Nome do turno ("Manhã", "Tarde", "Noite").
              - "data": Número de retiradas por dia da semana para o turno correspondente.
              - "borderColor": Cor do gráfico para o turno.
              - "fill": Booleano indicando se a área abaixo da linha deve ser preenchida.

    Fluxo de Execução:
        1. **Filtragem e Anotação:**
           - Filtra registros no modelo `RegistroTransacao` para considerar apenas retiradas.
           - Anota o dia da semana (como número) com base no campo `timestamp`.

        2. **Preparação de Dados por Turno:**
           - Itera pelos registros para organizar os dados por dia da semana e turno.
           - Usa os logins de usuários para buscar seus respectivos turnos no modelo `Usuario`.
           - Cria um dicionário que associa cada dia da semana aos totais de retiradas para cada turno.

        3. **Formatação para Chart.js:**
           - Define rótulos ("labels") com os dias da semana.
           - Cria conjuntos de dados ("datasets") para cada turno, preenchendo os valores por dia.

    Exemplo de Saída:
        Se houver as seguintes retiradas:
            - Segunda-feira: 5 retiradas no turno "Manhã", 3 no turno "Tarde".
            - Terça-feira: 4 retiradas no turno "Noite".
        O JSON retornado será:
        ```json
        {
            "labels": ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"],
            "datasets": [
                {
                    "label": "Manhã",
                    "data": [0, 5, 0, 0, 0, 0, 0],
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "fill": false
                },
                {
                    "label": "Tarde",
                    "data": [0, 3, 0, 0, 0, 0, 0],
                    "borderColor": "rgba(153, 102, 255, 1)",
                    "fill": false
                },
                {
                    "label": "Noite",
                    "data": [0, 0, 4, 0, 0, 0, 0],
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "fill": false
                }
            ]
        }
        ```

    Notas:
        - Os dias da semana são representados como números: 1 (domingo) a 7 (sábado).
        - As cores dos turnos são definidas estaticamente e podem ser ajustadas conforme necessário.
        - Se um usuário não for encontrado no modelo `Usuario`, o registro correspondente é ignorado.

    Requisitos:
        - O modelo `RegistroTransacao` deve ter os seguintes campos:
          - `tipo` (str): Indica o tipo da transação (ex.: "Retirada").
          - `timestamp` (datetime): Data e hora da transação.
          - `usuario_login` (str): Login do usuário associado à transação.
        - O modelo `Usuario` deve ter os seguintes campos:
          - `login_usuario` (str): Login do usuário.
          - `turno_usuario` (str): Turno do usuário ("T1", "T2", "T3").

    Dependências:
        - `RegistroTransacao` e `Usuario` (modelos do Django).
        - `ExtractWeekDay` e `Count` (utilitários do Django ORM).
        - `json.dumps` para converter o dicionário em uma string JSON.

    """
    # Filtrar registros apenas de retirada e anotar o dia da semana
    registros = RegistroTransacao.objects.filter(
        tipo='Retirada'  # Considerar apenas retiradas
    ).annotate(
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


def dashboard_view_pda():
    """
    Gera dados para um gráfico de distribuição de equipamentos por status.

    Esta função consulta o banco de dados para contar a quantidade de equipamentos 
    em diferentes estados: "Em operação", "Disponível" e "Manutenção". Os dados são 
    formatados para serem utilizados em gráficos de visualização, como pie charts ou bar charts.

    Args:
        Nenhum argumento é necessário, pois os dados são obtidos diretamente do banco de dados.

    Returns:
        str:
            Uma string JSON contendo:
            - "categories": Uma lista com os status de equipamentos ("Em operação", "Disponível", "Manutenção").
            - "series": Uma lista com os totais de equipamentos para cada status.

    Fluxo de Execução:
        1. **Consulta ao Banco de Dados:**
           - Conta o total de equipamentos com status "Retirado" (considerados "Em operação").
           - Conta o total de equipamentos com status "Disponível".
           - Conta o total de equipamentos com status "Manutenção".

        2. **Formatação para Gráficos:**
           - Organiza os status como categorias ("categories").
           - Insere os totais correspondentes em uma lista ("series").

    Exemplo de Saída:
        Se houver os seguintes registros no banco:
            - "Em operação": 50 equipamentos.
            - "Disponível": 30 equipamentos.
            - "Manutenção": 20 equipamentos.
        O JSON retornado será:
        ```json
        {
            "categories": ["Em operação", "Disponível", "Manutenção"],
            "series": [50, 30, 20]
        }
        ```

    Notas:
        - Os nomes das categorias são estáticos e correspondem diretamente aos status dos equipamentos.
        - Se não houver equipamentos cadastrados, as contagens serão 0.

    Requisitos:
        - O modelo `Equipamento` deve ter um campo `status` (str) que armazene o estado do equipamento.

    Dependências:
        - `Equipamento` (modelo do Django).
        - `json.dumps` para converter o dicionário em uma string JSON.
    """
    # Consulta ao banco de dados: contagem de retiradas por modelo de equipamento
    total_em_operacao = Equipamento.objects.filter(status="Retirado").count()
    total_disponivel = Equipamento.objects.filter(status="Disponível").count()
    total_manutencao = Equipamento.objects.filter(status="Manutenção").count()

    # Dados para o gráfico
    data = {
        "categories": ["Em operação", "Disponível", "Manutenção"],
        "series": [total_em_operacao, total_disponivel, total_manutencao],
    }

    return json.dumps(data)


def dashboard_info_view():
    """
    Gera informações gerais para a dashboard do sistema, incluindo a quantidade de equipamentos 
    em diferentes estados e a contagem de alertas de entrega.

    Esta função realiza a consulta ao banco de dados para contar a quantidade de equipamentos em 
    três status principais ("Em operação", "Disponível", "Manutenção") e também verifica os 
    equipamentos retirados que ultrapassaram o tempo de operação esperado, gerando um alerta de 
    entrega para aqueles que excederam o limite de tempo.

    Args:
        Nenhum argumento é necessário, pois os dados são obtidos diretamente do banco de dados.

    Returns:
        str:
            Uma string JSON contendo:
            - "total_em_operacao": O total de equipamentos que estão "Retirados" e em operação.
            - "total_disponivel": O total de equipamentos que estão "Disponíveis".
            - "total_manutencao": O total de equipamentos que estão em "Manutenção".
            - "total_alerta_entrega": O total de alertas de entrega gerados, ou seja, equipamentos 
              que estão "Retirados" há mais de 10 horas sem devolução.

    Fluxo de Execução:
        1. **Consulta ao Banco de Dados:**
           - Conta o total de equipamentos com status "Retirado" (em operação).
           - Conta o total de equipamentos com status "Disponível".
           - Conta o total de equipamentos com status "Manutenção".
        
        2. **Cálculo de Alertas:**
           - Para cada equipamento retirado, verifica o tempo desde a última retirada.
           - Se o tempo decorrido for superior a 10 horas, é gerado um alerta de entrega.
        
        3. **Organização de Dados para a Dashboard:**
           - Organiza as contagens e alertas em um dicionário que será retornado como um JSON.

    Exemplo de Saída:
        Se houver 50 equipamentos "Em operação", 30 "Disponíveis", 20 "Em Manutenção" e 5 
        equipamentos com alertas de entrega, o JSON retornado será:
        ```json
        {
            "total_em_operacao": 50,
            "total_disponivel": 30,
            "total_manutencao": 20,
            "total_alerta_entrega": 5
        }
        ```

    Notas:
        - O cálculo do alerta de entrega é baseado na comparação do tempo desde a última retirada. 
          Equipamentos que estão "Retirados" por mais de 10 horas geram um alerta.
        - A verificação do tempo de retirada considera o fuso horário atual.

    Requisitos:
        - O modelo `Equipamento` deve ter um campo `status` (str) que armazene o estado do equipamento.
        - O modelo `RegistroTransacao` deve ter uma relação com `Equipamento` e armazenar o campo `timestamp`.
        - O campo `timestamp` no modelo `RegistroTransacao` deve ser do tipo `DateTimeField` para calcular o tempo decorrido.

    Dependências:
        - `Equipamento` (modelo do Django).
        - `RegistroTransacao` (modelo do Django).
        - `timezone.now()` para obter o horário atual.
        - `timedelta` para calcular a diferença de tempo.
    """
    # Consulta ao banco de dados: contagem de retiradas por modelo de equipamento
    total_em_operacao = Equipamento.objects.filter(status="Retirado").count()
    total_disponivel = Equipamento.objects.filter(status="Disponível").count()
    total_manutencao = Equipamento.objects.filter(status="Manutenção").count()

    # Inicializa o contador de alertas
    total_alerta_entrega = 0

    # Verifica equipamentos retirados e calcula o tempo desde a retirada
    retirados = Equipamento.objects.filter(status="Retirado")
    for equipamento in retirados:
        # Verifica se o equipamento está em operação e obtém a última vez que foi retirado
        ultima_retirada = RegistroTransacao.objects.filter(equipamento=equipamento).aggregate(max_timestamp=Max('timestamp'))['max_timestamp']
        
        if ultima_retirada:
            tempo_decorrido = timezone.now() - ultima_retirada  # Calcula o tempo desde a retirada
            if tempo_decorrido > timedelta(hours=10):
                total_alerta_entrega += 1

    # Dados da dashboard
    data = {
        "total_em_operacao": total_em_operacao,
        "total_disponivel": total_disponivel,
        "total_manutencao": total_manutencao,
        "total_alerta_entrega": total_alerta_entrega,
    }

    return json.dumps(data)