// Growth Auth Application
class GrowthAuth {
    constructor() {
        this.isDarkMode = this.loadTheme();
        this.isLogin = true;
        this.isLoading = false;
        
        this.initializeElements();
        this.attachEventListeners();
        this.applyTheme();
    }

    initializeElements() {
        // Theme elements
        this.themeToggle = document.getElementById('themeToggle');
        this.themeIcon = document.getElementById('themeIcon');
        
        // Form toggle elements
        this.loginToggle = document.getElementById('loginToggle');
        this.signupToggle = document.getElementById('signupToggle');
        this.authTitle = document.getElementById('authTitle');
        this.authSubtitle = document.getElementById('authSubtitle');
        
        // Form elements
        this.loginForm = document.getElementById('loginForm');
        this.signupForm = document.getElementById('signupForm');
        
        // Message elements
        this.successMessage = document.getElementById('successMessage');
        this.errorMessage = document.getElementById('errorMessage');
        this.successText = document.getElementById('successText');
        this.errorText = document.getElementById('errorText');
        
        // Login form elements
        this.loginEmail = document.getElementById('loginEmail');
        this.loginPassword = document.getElementById('loginPassword');
        this.loginPasswordToggle = document.getElementById('loginPasswordToggle');
        this.rememberMe = document.getElementById('rememberMe');
        this.loginSubmit = document.getElementById('loginSubmit');
        this.forgotPassword = document.getElementById('forgotPassword');
        
        // Signup form elements
        this.signupEmail = document.getElementById('signupEmail');
        this.signupUsername = document.getElementById('signupUsername');
        this.signupPassword = document.getElementById('signupPassword');
        this.confirmPassword = document.getElementById('confirmPassword');
        this.signupPasswordToggle = document.getElementById('signupPasswordToggle');
        this.confirmPasswordToggle = document.getElementById('confirmPasswordToggle');
        this.agreeTerms = document.getElementById('agreeTerms');
        this.signupSubmit = document.getElementById('signupSubmit');
        
        // Error elements
        this.loginEmailError = document.getElementById('loginEmailError');
        this.loginPasswordError = document.getElementById('loginPasswordError');
        this.signupEmailError = document.getElementById('signupEmailError');
        this.signupUsernameError = document.getElementById('signupUsernameError');
        this.signupPasswordError = document.getElementById('signupPasswordError');
        this.confirmPasswordError = document.getElementById('confirmPasswordError');
        this.agreeTermsError = document.getElementById('agreeTermsError');
    }

    attachEventListeners() {
        // Theme toggle
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Form toggles
        this.loginToggle.addEventListener('click', () => this.switchToLogin());
        this.signupToggle.addEventListener('click', () => this.switchToSignup());
        
        // Password toggles
        this.loginPasswordToggle.addEventListener('click', () => this.togglePassword('loginPassword', this.loginPasswordToggle));
        this.signupPasswordToggle.addEventListener('click', () => this.togglePassword('signupPassword', this.signupPasswordToggle));
        this.confirmPasswordToggle.addEventListener('click', () => this.togglePassword('confirmPassword', this.confirmPasswordToggle));
        
        // Form submissions
        this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        this.signupForm.addEventListener('submit', (e) => this.handleSignup(e));
        
        // Forgot password
        this.forgotPassword.addEventListener('click', () => this.handleForgotPassword());
        
        // Real-time validation
        this.loginEmail.addEventListener('blur', () => this.validateLoginEmail());
        this.loginPassword.addEventListener('blur', () => this.validateLoginPassword());
        this.signupEmail.addEventListener('blur', () => this.validateSignupEmail());
        this.signupUsername.addEventListener('blur', () => this.validateSignupUsername());
        this.signupPassword.addEventListener('blur', () => this.validateSignupPassword());
        this.confirmPassword.addEventListener('blur', () => this.validateConfirmPassword());
        
        // Clear errors on input
        this.loginEmail.addEventListener('input', () => this.clearError('loginEmailError', this.loginEmail));
        this.loginPassword.addEventListener('input', () => this.clearError('loginPasswordError', this.loginPassword));
        this.signupEmail.addEventListener('input', () => this.clearError('signupEmailError', this.signupEmail));
        this.signupUsername.addEventListener('input', () => this.clearError('signupUsernameError', this.signupUsername));
        this.signupPassword.addEventListener('input', () => this.clearError('signupPasswordError', this.signupPassword));
        this.confirmPassword.addEventListener('input', () => this.clearError('confirmPasswordError', this.confirmPassword));
        this.agreeTerms.addEventListener('change', () => this.clearError('agreeTermsError', this.agreeTerms.parentElement));
    }

    // Theme Management
    toggleTheme() {
        this.isDarkMode = !this.isDarkMode;
        this.applyTheme();
        this.saveTheme();
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.isDarkMode ? 'dark' : 'light');
        this.themeIcon.className = this.isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
    }

    loadTheme() {
        const saved = localStorage.getItem('growthTheme');
        if (saved) {
            return saved === 'dark';
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    saveTheme() {
        localStorage.setItem('growthTheme', this.isDarkMode ? 'dark' : 'light');
    }

    // Form Switching
    switchToLogin() {
        if (this.isLogin) return;
        
        this.isLogin = true;
        this.updateFormToggle();
        this.showForm('login');
        this.clearMessages();
        this.clearAllErrors();
        this.signupForm.reset();
    }

    switchToSignup() {
        if (!this.isLogin) return;
        
        this.isLogin = false;
        this.updateFormToggle();
        this.showForm('signup');
        this.clearMessages();
        this.clearAllErrors();
        this.loginForm.reset();
    }

    updateFormToggle() {
        if (this.isLogin) {
            this.loginToggle.classList.add('active');
            this.signupToggle.classList.remove('active');
            this.authTitle.textContent = 'Welcome Back';
            this.authSubtitle.textContent = 'Sign in to your account to continue';
        } else {
            this.signupToggle.classList.add('active');
            this.loginToggle.classList.remove('active');
            this.authTitle.textContent = 'Create Account';
            this.authSubtitle.textContent = 'Sign up to get started with Growth';
        }
    }

    showForm(type) {
        if (type === 'login') {
            this.loginForm.style.display = 'block';
            this.signupForm.style.display = 'none';
        } else {
            this.loginForm.style.display = 'none';
            this.signupForm.style.display = 'block';
        }
    }

    // Password Toggle
    togglePassword(inputId, toggleBtn) {
        const input = document.getElementById(inputId);
        const icon = toggleBtn.querySelector('i');
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            input.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }

    // Validation
    validateLoginEmail() {
        const email = this.loginEmail.value.trim();
        if (!email) {
            this.showError('loginEmailError', 'Email or username is required', this.loginEmail);
            return false;
        }
        this.clearError('loginEmailError', this.loginEmail);
        return true;
    }

    validateLoginPassword() {
        const password = this.loginPassword.value;
        if (!password) {
            this.showError('loginPasswordError', 'Password is required', this.loginPassword);
            return false;
        }
        this.clearError('loginPasswordError', this.loginPassword);
        return true;
    }

    validateSignupEmail() {
        const email = this.signupEmail.value.trim();
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!email) {
            this.showError('signupEmailError', 'Email address is required', this.signupEmail);
            return false;
        }
        if (!emailPattern.test(email)) {
            this.showError('signupEmailError', 'Please enter a valid email address', this.signupEmail);
            return false;
        }
        this.clearError('signupEmailError', this.signupEmail);
        return true;
    }

    validateSignupUsername() {
        const username = this.signupUsername.value.trim();
        const usernamePattern = /^[a-zA-Z0-9_]+$/;
        
        if (!username) {
            this.showError('signupUsernameError', 'Username is required', this.signupUsername);
            return false;
        }
        if (username.length < 3) {
            this.showError('signupUsernameError', 'Username must be at least 3 characters', this.signupUsername);
            return false;
        }
        if (!usernamePattern.test(username)) {
            this.showError('signupUsernameError', 'Username can only contain letters, numbers, and underscores', this.signupUsername);
            return false;
        }
        this.clearError('signupUsernameError', this.signupUsername);
        return true;
    }

    validateSignupPassword() {
        const password = this.signupPassword.value;
        const hasLower = /[a-z]/.test(password);
        const hasUpper = /[A-Z]/.test(password);
        const hasNumber = /\d/.test(password);
        
        if (!password) {
            this.showError('signupPasswordError', 'Password is required', this.signupPassword);
            return false;
        }
        if (password.length < 8) {
            this.showError('signupPasswordError', 'Password must be at least 8 characters', this.signupPassword);
            return false;
        }
        if (!hasLower || !hasUpper || !hasNumber) {
            this.showError('signupPasswordError', 'Password must contain uppercase, lowercase, and number', this.signupPassword);
            return false;
        }
        this.clearError('signupPasswordError', this.signupPassword);
        return true;
    }

    validateConfirmPassword() {
        const password = this.signupPassword.value;
        const confirmPassword = this.confirmPassword.value;
        
        if (!confirmPassword) {
            this.showError('confirmPasswordError', 'Please confirm your password', this.confirmPassword);
            return false;
        }
        if (password !== confirmPassword) {
            this.showError('confirmPasswordError', 'Passwords do not match', this.confirmPassword);
            return false;
        }
        this.clearError('confirmPasswordError', this.confirmPassword);
        return true;
    }

    validateTerms() {
        if (!this.agreeTerms.checked) {
            this.showError('agreeTermsError', 'Please agree to the Terms of Service and Privacy Policy', this.agreeTerms.parentElement);
            return false;
        }
        this.clearError('agreeTermsError', this.agreeTerms.parentElement);
        return true;
    }

    // Error Display
    showError(errorId, message, inputElement) {
        const errorElement = document.getElementById(errorId);
        errorElement.textContent = message;
        inputElement.classList.add('error');
    }

    clearError(errorId, inputElement) {
        const errorElement = document.getElementById(errorId);
        errorElement.textContent = '';
        inputElement.classList.remove('error');
    }

    clearAllErrors() {
        const errorElements = document.querySelectorAll('.error-text');
        const inputElements = document.querySelectorAll('.form-input');
        
        errorElements.forEach(el => el.textContent = '');
        inputElements.forEach(el => el.classList.remove('error'));
    }

    // Message Display
    showSuccessMessage(message) {
        this.successText.textContent = message;
        this.successMessage.style.display = 'flex';
        this.errorMessage.style.display = 'none';
    }

    showErrorMessage(message) {
        this.errorText.textContent = message;
        this.errorMessage.style.display = 'flex';
        this.successMessage.style.display = 'none';
    }

    clearMessages() {
        this.successMessage.style.display = 'none';
        this.errorMessage.style.display = 'none';
    }

    // Loading State
    setLoading(button, isLoading) {
        if (isLoading) {
            button.classList.add('loading');
            button.disabled = true;
            this.isLoading = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            this.isLoading = false;
        }
    }

    // Form Handlers
    async handleLogin(e) {
        e.preventDefault();
        
        if (this.isLoading) return;
        
        this.clearMessages();
        
        // Validate form
        const isEmailValid = this.validateLoginEmail();
        const isPasswordValid = this.validateLoginPassword();
        
        if (!isEmailValid || !isPasswordValid) {
            return;
        }
        
        this.setLoading(this.loginSubmit, true);
        
        try {
            const formData = {
                email: this.loginEmail.value.trim(),
                password: this.loginPassword.value,
                rememberMe: this.rememberMe.checked
            };
            
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(formData),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage('Login successful! Redirecting to chat...');

                // If opened in popup, notify parent window
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'AUTH_SUCCESS',
                        user: data.user
                    }, window.location.origin);
                    setTimeout(() => {
                        window.close();
                    }, 1500);
                } else {
                    // If opened directly, redirect to main page
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1500);
                }
            } else {
                this.showErrorMessage(data.message || 'Login failed. Please try again.');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showErrorMessage('Network error. Please check your connection and try again.');
        } finally {
            this.setLoading(this.loginSubmit, false);
        }
    }

    async handleSignup(e) {
        e.preventDefault();
        
        if (this.isLoading) return;
        
        this.clearMessages();
        
        // Validate form
        const isEmailValid = this.validateSignupEmail();
        const isUsernameValid = this.validateSignupUsername();
        const isPasswordValid = this.validateSignupPassword();
        const isConfirmPasswordValid = this.validateConfirmPassword();
        const isTermsValid = this.validateTerms();
        
        if (!isEmailValid || !isUsernameValid || !isPasswordValid || !isConfirmPasswordValid || !isTermsValid) {
            return;
        }
        
        this.setLoading(this.signupSubmit, true);
        
        try {
            const formData = {
                email: this.signupEmail.value.trim(),
                username: this.signupUsername.value.trim(),
                password: this.signupPassword.value
            };
            
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(formData),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage('Account created successfully! You can now sign in.');
                setTimeout(() => {
                    this.switchToLogin();
                }, 1500);
            } else {
                this.showErrorMessage(data.message || 'Registration failed. Please try again.');
            }
        } catch (error) {
            console.error('Signup error:', error);
            this.showErrorMessage('Network error. Please check your connection and try again.');
        } finally {
            this.setLoading(this.signupSubmit, false);
        }
    }

    handleForgotPassword() {
        alert('Forgot password functionality will be available soon.');
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new GrowthAuth();
});