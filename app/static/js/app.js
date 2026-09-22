document.addEventListener('DOMContentLoaded', function() {
  const userMenu = document.querySelector('.user-menu');
  const trigger = document.querySelector('.user-trigger');
  if (userMenu && trigger) {
    trigger.addEventListener('click', function(e) {
      e.stopPropagation();
      userMenu.classList.toggle('open');
    });
    document.addEventListener('click', function() {
      userMenu.classList.remove('open');
    });
  }

  const sidebar = document.querySelector('.sidebar');
  const menuToggle = document.querySelector('.menu-toggle');
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', function() {
      sidebar.classList.toggle('open');
    });
  }

  const passwordInput = document.querySelector('#password');
  const toggleButton = document.querySelector('.toggle-password');
  if (passwordInput && toggleButton) {
    toggleButton.addEventListener('click', function() {
      const hidden = passwordInput.type === 'password';
      passwordInput.type = hidden ? 'text' : 'password';
      toggleButton.innerHTML = hidden ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
    });
  }

  const toastList = document.querySelectorAll('.toast');
  toastList.forEach((toast) => {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 350);
    }, 2600);
  });
});
