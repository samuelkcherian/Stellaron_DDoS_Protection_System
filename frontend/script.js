document.addEventListener('DOMContentLoaded', () => {
    // --- Auth Check & Logout ---
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    const userName = localStorage.getItem('userName');
    const appContainer = document.querySelector('.app-container');
    if (!isLoggedIn) {
        if (!window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('register.html')) {
            window.location.href = 'login.html';
        }
    } else {
        if (appContainer) {
            appContainer.classList.remove('hidden');
            const userNameElement = document.getElementById('user-profile-name');
            if (userNameElement && userName) {
                userNameElement.textContent = userName;
            }
        }
    }
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('userName');
            window.location.href = 'login.html';
        });
    }

    // --- API and Element References ---
    const API_BASE_URL = "http://localhost:5001";
    const settingsForm = document.getElementById('settings-form');
    const blockedIpsList = document.getElementById('blocked-ips-list');
    const trafficLog = document.getElementById('traffic-log');
    const alertsTableBody = document.getElementById('alerts-table-body');
    const chartCanvas = document.getElementById('trafficChart')?.getContext('2d');
    const alertsTypeChartCanvas = document.getElementById('alertsTypeChart')?.getContext('2d');
    const topAttackersBody = document.getElementById('top-attackers-body');
    let trafficChart, alertsTypeChart;

    if (chartCanvas) {
        trafficChart = new Chart(chartCanvas, {
            type: 'line', data: { labels: [], datasets: [{ label: 'Requests/Interval', data: [], borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.2)', borderWidth: 2, fill: true, tension: 0.4 }] },
            options: { scales: { y: { beginAtZero: true, ticks: { color: '#9ca3af' }, grid: { color: '#374151' } }, x: { ticks: { color: '#9ca3af' }, grid: { color: '#374151' } } }, plugins: { legend: { labels: { color: '#f9fafb' } } } }
        });
    }
    if (alertsTypeChartCanvas) {
        alertsTypeChart = new Chart(alertsTypeChartCanvas, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{ data: [], backgroundColor: ['#ef4444', '#f97316', '#3b82f6', '#991b1b', '#10b981'], borderColor: '#1f2937' }]
            },
            options: { responsive: true, plugins: { legend: { position: 'top', labels: { color: '#f9fafb' } } } }
        });
    }

    // --- Data Fetching Functions ---
    async function updateAlertsPanel() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/alerts`);
            const alerts = await response.json();
            alertsTableBody.innerHTML = '';
            if (alerts.length > 0) {
                alerts.forEach(alert => {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>${alert.timestamp}</td><td><span class="alert-level level-${alert.level}">${alert.level}</span></td><td>${alert.type}</td><td>${alert.details}</td>`;
                    alertsTableBody.appendChild(row);
                });
            } else {
                alertsTableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No alerts to display.</td></tr>';
            }
        } catch (error) { console.error("Failed to update alerts:", error); }
    }
    async function updateDashboardPanel() {
        try {
            const blockedIpsResponse = await fetch(`${API_BASE_URL}/api/blocked_ips`);
            const blockedIps = await blockedIpsResponse.json();
            blockedIpsList.innerHTML = '';
            if (blockedIps.length > 0) {
                blockedIps.forEach(ip => { const li = document.createElement('li'); li.textContent = ip; blockedIpsList.appendChild(li); });
            } else { blockedIpsList.innerHTML = '<li>None</li>'; }
            const trafficLogResponse = await fetch(`${API_BASE_URL}/api/live_traffic`);
            const traffic = await trafficLogResponse.json();
            trafficLog.textContent = traffic.join('\n');
            trafficLog.scrollTop = trafficLog.scrollHeight;
            const summaryResponse = await fetch(`${API_BASE_URL}/api/traffic_summary`);
            const summary = await summaryResponse.json();
            if (trafficChart) {
                trafficChart.data.labels = summary.labels;
                trafficChart.data.datasets[0].data = summary.data;
                trafficChart.update('none');
            }
        } catch (error) { console.error("Failed to update dashboard:", error); if (trafficLog) trafficLog.textContent = "Error connecting to the API..."; }
    }
    async function updateSettingsPanel() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/settings`);
            const settings = await response.json();
            document.getElementById('request-limit').value = settings.REQUEST_LIMIT;
            document.getElementById('time-window').value = settings.TIME_WINDOW;
            document.getElementById('global-request-limit').value = settings.GLOBAL_REQUEST_LIMIT;
            document.getElementById('unblock-duration').value = settings.UNBLOCK_DURATION;
        } catch (error) { console.error("Failed to load settings:", error); }
    }
    async function updateReportingPanel() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/reporting_summary`);
            const summary = await response.json();
            const alertLabels = Object.keys(summary.alerts_by_type);
            const alertData = Object.values(summary.alerts_by_type);
            if (alertsTypeChart) {
                alertsTypeChart.data.labels = alertLabels;
                alertsTypeChart.data.datasets[0].data = alertData;
                alertsTypeChart.update();
            }
            topAttackersBody.innerHTML = '';
            if (summary.top_attackers.length > 0) {
                summary.top_attackers.forEach(attacker => {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>${attacker.ip}</td><td>${attacker.count}</td>`;
                    topAttackersBody.appendChild(row);
                });
            } else {
                topAttackersBody.innerHTML = '<tr><td colspan="2" style="text-align:center;">No attacker data yet.</td></tr>';
            }
        } catch (error) { console.error("Failed to load reporting summary:", error); }
    }

    // --- Navigation Logic ---
    const pageTitle = document.getElementById('page-title');
    const navLinks = document.querySelectorAll('.nav-link');
    const contentPanels = document.querySelectorAll('.panel');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            contentPanels.forEach(p => p.classList.remove('active'));
            link.classList.add('active');
            const targetId = link.getAttribute('href').substring(1);
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.add('active');
                pageTitle.textContent = link.querySelector('span').textContent;
                if (targetId === 'dashboard') updateDashboardPanel();
                else if (targetId === 'alerts') updateAlertsPanel();
                else if (targetId === 'settings') updateSettingsPanel();
                else if (targetId === 'reporting') updateReportingPanel();
            }
        });
    });

    // --- Settings Form Submission ---
    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const newSettings = {
                REQUEST_LIMIT: document.getElementById('request-limit').value,
                TIME_WINDOW: document.getElementById('time-window').value,
                GLOBAL_REQUEST_LIMIT: document.getElementById('global-request-limit').value,
                UNBLOCK_DURATION: document.getElementById('unblock-duration').value,
            };
            try {
                const response = await fetch(`${API_BASE_URL}/api/settings`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newSettings)
                });
                if (response.ok) { alert('Settings saved successfully!'); } else { alert('Failed to save settings.'); }
            } catch (error) { console.error("Error saving settings:", error); alert('An error occurred while saving settings.'); }
        });
    }

    // --- Main Update Loop ---
    function mainUpdateLoop() {
        const activePanel = document.querySelector('.panel.active');
        if (!activePanel) return;
        if (activePanel.id === 'dashboard') updateDashboardPanel();
        if (activePanel.id === 'alerts') updateAlertsPanel();
    }
    setInterval(mainUpdateLoop, 2000);

    // Initial load for the default panel
    if (isLoggedIn) {
        updateDashboardPanel();
    }
});
