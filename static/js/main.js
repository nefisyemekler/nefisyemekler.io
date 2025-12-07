// Placeholder for future JavaScript functionality
console.log('Nefis Yemekler - Ready!');

// Categories Modal Functions
function openCategoriesModal(event) {
    if (event) event.preventDefault();
    const modal = document.getElementById('categoriesModal');
    if (modal) {
        modal.classList.add('active');
        console.log('Categories modal opened');
    }
}

function closeCategoriesModal() {
    const modal = document.getElementById('categoriesModal');
    if (modal) {
        modal.classList.remove('active');
        console.log('Categories modal closed');
    }
}

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Categories modal close button
    const categoriesClose = document.querySelector('.categories-close');
    const categoriesModal = document.getElementById('categoriesModal');

    if (categoriesClose) {
        categoriesClose.addEventListener('click', function() {
            closeCategoriesModal();
        });
    }

    // Close modal when clicking outside
    if (categoriesModal) {
        categoriesModal.addEventListener('click', function(e) {
            if (e.target === categoriesModal) {
                closeCategoriesModal();
            }
        });
    }

    // Set active nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-item-inner');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.background = 'var(--navbar-bg-light)';
            link.style.color = '#fff';
        }
    });

    console.log('Categories modal setup complete');
});

// Dark Mode Toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const icon = document.getElementById('darkModeIcon');
    if (document.body.classList.contains('dark-mode')) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        localStorage.setItem('darkMode', 'enabled');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Check dark mode on page load
document.addEventListener('DOMContentLoaded', function() {
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        const icon = document.getElementById('darkModeIcon');
        if (icon) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        }
    }
});

// Preview image before upload
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('imagePreview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// Confirm delete actions
function confirmDelete(message) {
    return confirm(message || 'Bu işlemi geri alamazsınız. Emin misiniz?');
}
