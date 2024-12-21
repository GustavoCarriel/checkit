from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from .models import Equipamento, RegistroTransacao, Usuario
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt



@login_required
def index(request):
    """
    View para exibir a página inicial.

    Args:
        request (HttpRequest): Objeto que contém os dados da solicitação HTTP.

    Returns:
        HttpResponse: Resposta renderizando o template 'index.html'.
    """
    return render(request, 'index.html')



def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Verifica se o usuário é superusuário
            # if user.is_superuser:
            #     print("Superusuário detectado - Redirecionando para admin.")
            #     return redirect('admin:index')  # Redireciona para o admin se for superusuário
            
            # Verifica se o usuário pertence a um grupo específico
            if user.groups.filter(name='GrupoEspecifico').exists():
                print(f"Usuário no grupo 'GrupoEspecifico' - Redirecionando para index.")
                return redirect('index')  # Redireciona para a página inicial ou uma página específica para o grupo
            
            # Caso o usuário não seja superusuário nem pertença ao grupo
            next_url = request.GET.get('next', '')  # Se houver um parâmetro 'next' no URL, redireciona para essa página
            if next_url:
                print(f"Redirecionando para o URL 'next': {next_url}")
                return HttpResponseRedirect(next_url)  # Garantir redirecionamento para o valor de 'next'
            else:
                print("Redirecionando para a página inicial.")
                return redirect('index')  # Redireciona para a página inicial como fallback
        else:
            print("Formulário inválido.")
            messages.error(request, "Login ou senha inválidos. Tente novamente.")
    else:
        form = AuthenticationForm()

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



@login_required
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
        login_usuario = request.POST.get('usuario_login')
        usuario = buscar_usuario(login_usuario)

        if not usuario:
            messages.error(request, "Por favor, insira o login do usuário.")
            return redirect('retirar_equipamento', equipamento_id=equipamento_id)
        
        if equipamento.status == 'Disponível':
            # Atualiza o status do equipamento para "Retirado"
            equipamento.status = 'Retirado'
            # Cria o registro de transação para a retirada
            transacao = RegistroTransacao(
                equipamento=equipamento,
                usuario_login=usuario.login_usuario,
                tipo='Retirada',
                timestamp=timezone.now()
            )
            # Salva as alterações no banco de dados
            equipamento.save()
            transacao.save()
            return redirect('index')
        else:
            messages.error(request, "Equipamento não está disponível.")
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
