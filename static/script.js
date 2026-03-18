document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const loginSection = document.getElementById('authSection');
    const profileSection = document.getElementById('userProfile');
    const loginPrompt = document.getElementById('loginPrompt');
    const dashboard = document.getElementById('dashboard');
    const reportContainer = document.getElementById('reportContainer');
    
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    const usernameInput = document.getElementById('usernameInput');
    const sectorInput = document.getElementById('sectorInput');
    const welcomeText = document.getElementById('welcomeText');
    const sessionStats = document.getElementById('sessionStats');
    
    const analyzeLoader = document.getElementById('analyzeLoader');
    const btnText = document.querySelector('.btn-text');
    const reportSector = document.getElementById('reportSector');
    const reportMeta = document.getElementById('reportMeta');
    const markdownOutput = document.getElementById('markdownOutput');

    // App State
    let token = localStorage.getItem('trade_api_token') || null;
    let username = localStorage.getItem('trade_api_user') || null;

    // Initialize UI based on auth state
    function init() {
        if (token) {
            showDashboard();
            fetchSessionStats();
        } else {
            showLogin();
        }
    }

    // Toggle Views
    function showDashboard() {
        loginSection.style.display = 'none';
        loginPrompt.style.display = 'none';
        profileSection.style.display = 'flex';
        dashboard.style.display = 'block';
        welcomeText.textContent = `Connected as @${username}`;
        reportContainer.style.display = 'none';
    }

    function showLogin() {
        loginSection.style.display = 'flex';
        loginPrompt.style.display = 'flex';
        profileSection.style.display = 'none';
        dashboard.style.display = 'none';
        reportContainer.style.display = 'none';
        usernameInput.value = '';
    }

    // API Calls
    async function handleLogin() {
        const user = usernameInput.value.trim();
        if (!user) return alert('Username is required');

        try {
            const res = await fetch('/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user })
            });
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.error || JSON.stringify(data.detail));

            token = data.access_token;
            username = user;
            localStorage.setItem('trade_api_token', token);
            localStorage.setItem('trade_api_user', username);
            
            showDashboard();
            fetchSessionStats();
        } catch (err) {
            alert('Login failed: ' + err.message);
        }
    }

    function handleLogout() {
        token = null;
        username = null;
        localStorage.removeItem('trade_api_token');
        localStorage.removeItem('trade_api_user');
        showLogin();
    }

    async function fetchSessionStats() {
        try {
            const res = await fetch('/session', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            
            if (!res.ok) {
                if(res.status === 401) handleLogout();
                return;
            }

            sessionStats.innerHTML = `
                <div class="stat-badge"><span>Requests:</span> ${data.requests_made}</div>
                <div class="stat-badge"><span>Sectors:</span> ${data.sectors_queried.length}</div>
                <div class="stat-badge"><span>Rate Limit Remaining:</span> ${data.rate_limit_remaining}</div>
            `;
        } catch (err) {
            console.error('Failed to fetch session stats:', err);
        }
    }

    async function generateReport() {
        const sector = sectorInput.value.trim();
        if (!sector) return alert('Please enter a sector');

        // UI Loading State
        analyzeBtn.disabled = true;
        btnText.textContent = 'Analyzing...';
        analyzeLoader.classList.remove('hidden');
        reportContainer.style.display = 'none';

        try {
            const res = await fetch(`/analyze/${encodeURIComponent(sector)}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            
            if (!res.ok) {
                if(res.status === 401) { handleLogout(); throw new Error("Session expired. Please reconnect."); }
                throw new Error(data.error || JSON.stringify(data.detail));
            }

            // Render Report
            reportSector.textContent = (data.sector.charAt(0).toUpperCase() + data.sector.slice(1));
            reportMeta.innerHTML = `
                <span>⏱️ ${data.processing_time_seconds}s</span>
                <span>📰 ${data.sources_count} Sources</span>
                <span>📅 ${new Date(data.generated_at).toLocaleString()}</span>
            `;
            
            // Convert MD to HTML via marked.js
            markdownOutput.innerHTML = marked.parse(data.report);
            reportContainer.style.display = 'block';
            
            // Refresh stats
            fetchSessionStats();
            
            // Scroll to report smoothly
            reportContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
        } catch (err) {
            alert('Analysis failed: ' + err.message);
        } finally {
            // Restore UI state
            analyzeBtn.disabled = false;
            btnText.textContent = 'Generate Report';
            analyzeLoader.classList.add('hidden');
        }
    }

    // Event Listeners
    loginBtn.addEventListener('click', handleLogin);
    usernameInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleLogin(); });
    logoutBtn.addEventListener('click', handleLogout);
    analyzeBtn.addEventListener('click', generateReport);
    sectorInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') generateReport(); });

    // Startup
    init();
});
