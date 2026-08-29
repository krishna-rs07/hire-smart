// Hire Smart Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.app-sidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (sidebarToggle && sidebar && backdrop) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            backdrop.classList.toggle('show');
        });
        backdrop.addEventListener('click', function() {
            sidebar.classList.remove('open');
            backdrop.classList.remove('show');
        });
    }

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const files = e.target.files;
            const preview = document.getElementById('file-preview');
            if (preview) {
                preview.innerHTML = '';
                Array.from(files).forEach(function(file) {
                    const div = document.createElement('div');
                    div.className = 'd-flex align-items-center justify-content-between p-2 border rounded mb-2';
                    div.innerHTML = `
                        <div class="d-flex align-items-center">
                            <i class="fas fa-file-${getFileIcon(file.name)} text-primary me-2"></i>
                            <span>${file.name}</span>
                        </div>
                        <span class="text-muted small">${formatFileSize(file.size)}</span>
                    `;
                    preview.appendChild(div);
                });
            }
        });
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Skill tag filtering
    const skillFilters = document.querySelectorAll('.skill-filter');
    skillFilters.forEach(function(filter) {
        filter.addEventListener('click', function() {
            this.classList.toggle('active');
            filterCandidates();
        });
    });

    // Score circle animation
    animateScoreCircles();
});

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    if (['pdf'].includes(ext)) return 'pdf';
    if (['doc', 'docx'].includes(ext)) return 'word';
    return 'alt';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function filterCandidates() {
    // Implementation for candidate filtering
    const activeFilters = Array.from(document.querySelectorAll('.skill-filter.active')).map(el => el.dataset.skill);
    const rows = document.querySelectorAll('.candidate-row');

    rows.forEach(row => {
        const skills = row.dataset.skills ? row.dataset.skills.split(',') : [];
        const matches = activeFilters.length === 0 || activeFilters.some(f => skills.includes(f));
        row.style.display = matches ? '' : 'none';
    });
}

function animateScoreCircles() {
    const circles = document.querySelectorAll('.score-circle[data-score]');
    circles.forEach(circle => {
        const score = parseInt(circle.dataset.score, 10);
        let current = 0;
        const duration = 1000;
        const step = score / (duration / 16);

        const animate = () => {
            current += step;
            if (current >= score) {
                circle.textContent = score + '%';
            } else {
                circle.textContent = Math.round(current) + '%';
                requestAnimationFrame(animate);
            }
        };
        animate();
    });
}

// Utility functions
const HireSmart = {
    showLoading: function(btn) {
        btn.disabled = true;
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = '<span class="loading-spinner"></span> Processing...';
    },

    hideLoading: function(btn) {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalText || 'Submit';
    },

    toast: function(message, type = 'info') {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 70px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HireSmart;
}