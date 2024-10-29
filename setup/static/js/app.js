const toggleButton = document.getElementById('toggle-btn');
const sidebar = document.getElementById('sidebar');
const hamburgerIcon = document.getElementById('hamburguer_sidebar');
const closeIcon = document.getElementById('close_sidebar');

function toggleSidebar() {
    // Alterna a classe 'close' da sidebar
    sidebar.classList.toggle('close');

    // Alterna a visibilidade dos ícones
    hamburgerIcon.classList.toggle('hidden');
    closeIcon.classList.toggle('hidden');

    closeAllSubMenus();
}

function closeAllSubMenus() {
    Array.from(sidebar.getElementsByClassName('show')).forEach((ul) => {
        ul.classList.remove('show');
        ul.previousElementSibling.classList.remove('rotate');
    });
}

// Inicia com a sidebar fechada e o ícone de hambúrguer
sidebar.classList.add('close');
hamburgerIcon.classList.remove('hidden');
closeIcon.classList.add('hidden');
