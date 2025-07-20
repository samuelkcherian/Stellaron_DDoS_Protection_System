document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const API_BASE_URL = "http://localhost:5001";

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = loginForm.email.value;
            const password = loginForm.password.value;

            // Corrected: Use backticks for the template literal
            const response = await fetch(`${API_BASE_URL}/api/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();
            if (response.ok) {
                // Login successful
                localStorage.setItem('isLoggedIn', 'true');
                localStorage.setItem('userName', result.name);
                window.location.href = 'index.html';
            } else {
                // Login failed
                // Corrected: Use backticks for the template literal
                alert(`Login Failed: ${result.message}`);
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = registerForm.name.value;
            const email = registerForm.email.value;
            const password = registerForm.password.value;

            // Corrected: Use backticks for the template literal
            const response = await fetch(`${API_BASE_URL}/api/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });

            const result = await response.json();
            if (response.ok) {
                // Registration successful
                alert('Registration successful! Please log in.');
                window.location.href = 'login.html';
            } else {
                // Registration failed
                // Corrected: Use backticks for the template literal
                alert(`Registration Failed: ${result.message}`);
            }
        });
    }
});
