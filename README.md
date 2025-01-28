# Check IT

Controle e gerenciamento de entrada e saída de equipamentos de maneira eficiente, com métricas e insights para operação.

---

## 🎯 Objetivo do Projeto

Este projeto foi desenvolvido para gerenciar a entrada e saída de PDAs (coletores de dados) e rádios durante os turnos de uma operação (manhã, tarde e noite).

O sistema fornece:
- **Controle de usuários** para monitorar os responsáveis pelos equipamentos.
- **Painel interativo** com métricas e insights sobre o uso dos dispositivos.
- **Otimização operacional**, reduzindo falhas no controle de equipamentos.

---

## ⚙️ Funcionalidades

- 📋 **Controle de Equipamentos**: Registro de retirada e devolução vinculados ao turno e ao usuário.
- 🔐 **Gestão de Usuários**: Permissões diferenciadas para administradores e operadores.
- 📊 **Dashboard Interativo**: Exibição de métricas e insights com gráficos gerados pelo Chart.js.
- ✅ **Histórico Completo**: Logs de operações para auditorias futuras.

---

## 🛠️ Tecnologias Utilizadas

<p align="center">
  <img src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python" />
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green" alt="Django" />
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
  <img src="https://img.shields.io/badge/JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E" alt="JavaScript" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
  <img src="https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap" />
  <img src="https://img.shields.io/badge/Chart%20js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white" alt="Chart.js" />
</p>

---

## 🚀 Configuração do Projeto

Siga os passos abaixo para executar o projeto localmente:

1. **Clone o Repositório**
    ```bash
    git clone https://github.com/usuario/repo-check-it.git
    cd repo-check-it
    ```

2. Instale o Python Certifique-se de ter o Python 3.10+ instalado.

3. Configure o Ambiente Virtual
    ```bash
    pip install virtualenv
    virtualenv venv
    venv\Scripts\activate
    ```

4. Instale as Dependências
    ```bash
    pip install -r requirements.txt
    ```

5. Configure o Banco de Dados Aplique as migrações para criar as tabelas no banco de dados:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

6. Crie um Superusuário
    ```bash
    python manage.py createsuperuser
    ```

- Informe o nome de usuário, e-mail e senha.
⚠️ Nota: O superusuário é responsável por gerenciar o sistema. Não compartilhe essas credenciais.

7. Inicie o Servidor
    ```bash
    python manage.py runserver
    ```

Acesse http://127.0.0.1:8000 no navegador.


## 📂 Estrutura de Pastas

```plaintext
├── check_it/                # Diretório do projeto
│   ├── check/               # Aplicação principal
│   │   ├── models/          # Configuração de tabelas
│   │   ├── urls/            # Configuração de rotas
│   │   ├── views/           # Funções
│   ├── setup/               # Configuração do projeto
│   │   ├── static/          # Arquivos estáticos (CSS, JS)
│   │   ├── settings/        # Configurações do projeto
│   ├── templates/           # Arquivos HTML para renderização
│   ├── db.sqlite3           # Banco de dados local
│   └── manage.py            # Comando principal do Django
```

## 👤 Autor

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/GustavoCarriel">
        <img src="https://avatars.githubusercontent.com/u/99743313?v=4" width="100px;" alt="Gustavo Carriel"/>
        <br />
        <sub><b>Gustavo Carriel</b></sub>
      </a>
      <br />
      <a href="mailto:gucarriel@hotmail.com" title="E-mail">✉️ Email</a>
      <a href="https://www.linkedin.com/in/gustavocarriel/" title="LinkedIn">🔗 Linkedin</a>
    </td>
  </tr>
</table>


## 📝 Melhorias Futuras

- Implementar autenticação via QR Code para retirada e devolução de equipamentos.
- Migrar para um banco de dados mais escalável (PostgreSQL).
- Adicionar notificações por e-mail para devoluções pendentes.
