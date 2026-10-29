document.addEventListener('DOMContentLoaded', function () {
  const userMenu = document.querySelector('.user-menu');
  const trigger = document.querySelector('.user-trigger');
  if (userMenu && trigger) {
    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      const isOpen = userMenu.classList.toggle('open');
      trigger.setAttribute('aria-expanded', String(isOpen));
    });
    document.addEventListener('click', function () {
      userMenu.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        userMenu.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.focus();
      }
    });
  }

  const sidebar = document.querySelector('.sidebar');
  const menuToggle = document.querySelector('.menu-toggle');
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });
  }

  const passwordInput = document.querySelector('#password');
  const toggleButton = document.querySelector('.toggle-password');
  if (passwordInput && toggleButton) {
    toggleButton.addEventListener('click', function () {
      const hidden = passwordInput.type === 'password';
      passwordInput.type = hidden ? 'text' : 'password';
      toggleButton.innerHTML = hidden
        ? '<i class="bi bi-eye-slash"></i>'
        : '<i class="bi bi-eye"></i>';
    });
  }

  document.querySelectorAll('.toast').forEach((toast) => {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 350);
    }, 3000);
  });

  document.querySelectorAll('[data-confirm]').forEach((form) => {
    form.addEventListener('submit', function (event) {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  document.querySelectorAll('[data-loading-target]').forEach((button) => {
    button.closest('form')?.addEventListener('submit', function () {
      button.disabled = true;
      button.classList.add('is-loading');
    });
  });

  // Live edit modal for assets: the table button loads the current row data.
  const modal = document.getElementById('editAssetModal');
  const editForm = document.getElementById('editAssetForm');
  if (modal && editForm) {
    const fields = {
      code: document.getElementById('edit_asset_code'),
      name: document.getElementById('edit_name'),
      category: document.getElementById('edit_category_id'),
      department: document.getElementById('edit_department_id'),
      user: document.getElementById('edit_user_name'),
      purchase: document.getElementById('edit_purchase_date'),
      usefulLife: document.getElementById('edit_useful_life_years'),
      value: document.getElementById('edit_value'),
      status: document.getElementById('edit_status'),
      location: document.getElementById('edit_location'),
      notes: document.getElementById('edit_notes')
    };

    const openModal = (button) => {
      fields.code.value = button.dataset.code || '';
      fields.name.value = button.dataset.name || '';
      fields.category.value = button.dataset.category || '';
      fields.department.value = button.dataset.department || '';
      fields.user.value = button.dataset.user || '';
      fields.purchase.value = button.dataset.purchase || '';
      fields.usefulLife.value = button.dataset.usefulLife || '';
      fields.value.value = button.dataset.value || '0';
      fields.status.value = button.dataset.status || 'active';
      fields.location.value = button.dataset.location || '';
      fields.notes.value = button.dataset.notes || '';
      editForm.action = `/assets/${button.dataset.id}/edit`;
      modal.classList.add('open');
      modal.setAttribute('aria-hidden', 'false');
      fields.code.focus();
      document.body.classList.add('modal-open');
    };

    const closeModal = () => {
      modal.classList.remove('open');
      modal.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
    };

    document.querySelectorAll('[data-edit-asset]').forEach((button) => {
      button.addEventListener('click', () => openModal(button));
    });
    const editId = new URLSearchParams(window.location.search).get('edit_id');
    const requestedEditButton = editId
      ? document.querySelector(`[data-edit-asset][data-id="${CSS.escape(editId)}"]`)
      : null;
    if (requestedEditButton) openModal(requestedEditButton);

    modal.querySelectorAll('[data-close-modal]').forEach((button) => {
      button.addEventListener('click', closeModal);
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && modal.classList.contains('open')) closeModal();
    });
  }

  // Clicking "Thêm tài sản" from the sidebar focuses the real form instead of doing nothing.
  document.querySelectorAll('a[href$="#asset-form"]').forEach((link) => {
    link.addEventListener('click', function () {
      setTimeout(() => document.getElementById('asset_code')?.focus(), 250);
    });
  });
});
