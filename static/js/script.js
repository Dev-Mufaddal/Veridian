/* ======================================
   MAIN JAVASCRIPT FILE - Flask Auth Project
   ====================================== */

// Function to validate email format on the client side
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+₹/;
    return emailRegex.test(email);
}

// Function to validate password strength
function validatePasswordStrength(password) {
    let strength = 0;
    
    // Check password length
    if (password.length >= 6) strength++;
    if (password.length >= 10) strength++;
    
    // Check for uppercase letters
    if (/[A-Z]/.test(password)) strength++;
    
    // Check for lowercase letters
    if (/[a-z]/.test(password)) strength++;
    
    // Check for numbers
    if (/[0-9]/.test(password)) strength++;
    
    // Check for special characters
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    return strength;
}

// Function to show password strength indicator (optional enhancement)
function updatePasswordStrength(passwordInput) {
    const strength = validatePasswordStrength(passwordInput.value);
    let message = '';
    let color = '';
    
    if (passwordInput.value === '') {
        message = '';
    } else if (strength < 2) {
        message = 'Weak password';
        color = '#f44336';
    } else if (strength < 4) {
        message = 'Fair password';
        color = '#ff9800';
    } else if (strength < 6) {
        message = 'Good password';
        color = '#4CAF50';
    } else {
        message = 'Strong password';
        color = '#2196F3';
    }
    
    return { message, color };
}

// Initialize page on load
document.addEventListener('DOMContentLoaded', function() {
    console.log('✓ Flask Auth Application Loaded');
    
    // Auto-hide alerts after 5 seconds (optional)
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// Form submission validation
function validateForm(event) {
    // You can add additional client-side validation here if needed
    // The server already validates everything, but client-side validation
    // provides better user experience
}

// Console message for developers
console.log('%c Flask Auth Project ', 'background: #4CAF50; color: white; font-size: 16px; padding: 10px;');
console.log('This is a simple Flask authentication system with:');
console.log('✓ User Registration');
console.log('✓ User Login');
console.log('✓ Session Management');
console.log('✓ Secure Password Hashing');
console.log('✓ MySQL Database');
