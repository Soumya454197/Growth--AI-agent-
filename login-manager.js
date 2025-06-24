// Enhanced Login Manager for Growth Chat App

class LoginManager {
    constructor() {
        this.user = null;
        this.isAuthenticated = false;
        this.autoLoginAttempted = false;
        this.init();
    }

    async init() {
        // Try auto-login on page load
        await this.attemptAutoLogin();
        this.setupAuthStateListener();
    }

    async attemptAutoLogin() {
        if (this.autoLoginAttempted) return;
        this.autoLoginAttempted = true;

        try {
            const response = await fetch('/api/auth/auto-login', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.setUser(data.user);
                    console.log('Auto-login successful:', data.user.username);
                    
                    // Redirect to main app if on login page
                    if (window.location.pathname.includes('login')) {
                        window.location.href = '/';
                    }
                    return true;
                }
            }
        } catch (error) {
            console.log('Auto-login failed:', error.message);
        }

        return false;
    }

    setUser(user) {
        this.user = user;
        this.isAuthenticated = true;
        this.updateUI();
        this.saveUserToStorage(user);
    }

    clearUser() {
        this.user = null;
        this.isAuthenticated = false;
        this.updateUI();
        this.clearUserFromStorage();
    }

    saveUserToStorage(user) {
        // Save non-sensitive user info to localStorage for UI persistence
        localStorage.setItem('user_info', JSON.stringify({
            username: user.username,
            email: user.email,
            id: user.id
        }));
    }

    clearUserFromStorage() {
        localStorage.removeItem('user_info');
    }

    getUserFromStorage() {
        try {
            const userInfo = localStorage.getItem('user_info');
            return userInfo ? JSON.parse(userInfo) : null;
        } catch {
            return null;
        }
    }

    updateUI() {
        // Update UI elements based on auth state
        const authElements = document.querySelectorAll('[data-auth-state]');
        authElements.forEach(element => {
            const authState = element.getAttribute('data-auth-state');
            if (authState === 'authenticated') {
                element.style.display = this.isAuthenticated ? 'block' : 'none';
            } else if (authState === 'unauthenticated') {
                element.style.display = this.isAuthenticated ? 'none' : 'block';
            }
        });

        // Update user info displays
        const userElements = document.querySelectorAll('[data-user-info]');
        userElements.forEach(element => {
            const infoType = element.getAttribute('data-user-info');
            if (this.user && this.user[infoType]) {
                element.textContent = this.user[infoType];
            }
        });
    }

    setupAuthStateListener() {
        // Listen for auth state changes across tabs
        window.addEventListener('storage', (e) => {
            if (e.key === 'user_info') {
                if (e.newValue) {
                    const user = JSON.parse(e.newValue);
                    this.setUser(user);
                } else {
                    this.clearUser();
                }
            }
        });
    }

    async login(email, password, rememberMe = false) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    email: email,
                    password: password,
                    rememberMe: rememberMe
                })
            });

            const data = await response.json();

            if (data.success) {
                this.setUser(data.user);
                return { success: true, message: data.message, user: data.user };
            } else {
                return { success: false, message: data.message };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, message: 'Connection error. Please try again.' };
        }
    }

    async signup(email, username, password) {
        try {
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    email: email,
                    username: username,
                    password: password
                })
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Signup error:', error);
            return { success: false, message: 'Connection error. Please try again.' };
        }
    }

    async logout() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.clearUser();
            // Don't redirect to login page, just update UI
            console.log('User logged out successfully');
        }
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/check', {
                method: 'GET',
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.authenticated) {
                    this.setUser(data.user);
                    return true;
                }
            }
        } catch (error) {
            console.error('Auth check error:', error);
        }

        this.clearUser();
        return false;
    }
}

// Initialize global login manager
const loginManager = new LoginManager();

// Export for use in other scripts
window.loginManager = loginManager;
