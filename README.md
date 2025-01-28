
# Check IT

Este projeto consiste em um sistema de controle de entrada e saída de equipamentos, focado especialmente em PDAs (coletor de dados) e rádios. O sistema permite monitorar os usuários e gerenciar os equipamentos de maneira eficiente, oferecendo métricas precisas e insights valiosos para o acompanhamento em uma dashboard interativa.


## Technologias Utilizadas

<p style="text-align: center;">
    <img src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python" />
    <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green" alt="Django" />
    <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
    <img src="https://img.shields.io/badge/JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E" alt="JavaScript" />
    <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
    <img src="https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap" />
    <img src="https://img.shields.io/badge/Chart%20js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white" alt="Chart.js" />
</p>


## Autores

- [@GustavoCarriel](https://github.com/GustavoCarriel)



## Primeiros Passos

1. Baixe e instale o Python

2. Instale um ambiente virtual
```bash
    pip install virtualenv
```
3. Crie um ambiente virtual
```bash
    virtualenv venv
```
4. Ative o ambiente virtual
```bash
    venv\Scripts\activate
```
5. Instale as dependencias necessária para o sistema
```bash
  pip install -r requirements.txt
```
6. Crie um super usuario
```bash
    python manage.py createsuperuser
```
- Informe o usuario
- Informe o email
- Informe a senha

⚠️ **Atenção:** Este superusuário é o usuário master e não deve ser compartilhado com ninguém, pois é o usuário responsável por gerenciar este sistema.

7. Iniciar o sistema
```bash
    python manage.py runserver
```
8. Devido as alterações no modelo sera nescessario criar aplicações e aplicar.
```bash
    python manage.py makemigrations
    python manage.py migrate
```
