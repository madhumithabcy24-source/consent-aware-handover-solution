// Client-side interactions for Youth Helpline Handover System

document.addEventListener("DOMContentLoaded", function() {
    // Auto-dismiss flash messages after 5 seconds
    const flashAlerts = document.querySelectorAll('.flash-alert');
    flashAlerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(function() { alert.remove(); }, 500);
        }, 5000);
    });
});
