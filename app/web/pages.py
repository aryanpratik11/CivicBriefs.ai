"""Static HTML snippets served by FastAPI for lightweight UI flows."""

PORTAL_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>CivicBriefs Portal</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #0b1120;
            --panel: #111a2f;
            --muted: #94a3b8;
            --accent: #38bdf8;
            --accent-dark: #0ea5e9;
            --error: #f87171;
            --success: #34d399;
            --border: rgba(148, 163, 184, 0.2);
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            min-height: 100vh;
            background: radial-gradient(circle at top, #1f2937 0%, #020617 70%);
            color: white;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 32px 16px;
        }

        .shell {
            width: min(1100px, 100%);
            display: grid;
            gap: 24px;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            align-items: stretch;
        }

        .hero {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.6), rgba(8, 47, 73, 0.9));
            border-radius: 28px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }

        .hero::after {
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.35), transparent 55%);
            pointer-events: none;
        }

        .hero h1 {
            margin: 0 0 16px;
            font-size: clamp(32px, 4vw, 44px);
            line-height: 1.1;
        }

        .hero p {
            margin: 0 0 18px;
            max-width: 420px;
            color: rgba(255,255,255,0.85);
            font-size: 16px;
        }

        .panel {
            background: var(--panel);
            border-radius: 24px;
            padding: 32px;
            border: 1px solid var(--border);
            box-shadow: 0 25px 45px rgba(2, 6, 23, 0.45);
        }

        .tabs {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
        }

        .tab-btn {
            flex: 1;
            border-radius: 999px;
            border: 1px solid var(--border);
            padding: 12px 18px;
            color: var(--muted);
            background: transparent;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .tab-btn.active {
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            border-color: transparent;
            color: #0f172a;
        }

        form {
            display: none;
            flex-direction: column;
            gap: 16px;
        }

        form.active { display: flex; }

        label {
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 14px;
            color: var(--muted);
        }

        input {
            padding: 12px 14px;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: rgba(15, 23, 42, 0.5);
            color: white;
            font-size: 15px;
        }

        input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.25);
        }

        button.primary {
            border: none;
            border-radius: 14px;
            padding: 14px 18px;
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            color: #0f172a;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: transform 0.15s ease;
        }

        button.primary:disabled { opacity: 0.6; cursor: not-allowed; }

        button.primary:hover:not(:disabled) { transform: translateY(-1px); }

        .status {
            min-height: 20px;
            font-size: 13px;
            color: var(--muted);
        }

        .status.error { color: var(--error); }
        .status.success { color: var(--success); }

        ul {
            padding-left: 16px;
            color: rgba(15, 23, 42, 0.85);
            font-weight: 500;
        }

        @media (max-width: 720px) {
            body { padding: 24px 16px; }
            .hero, .panel { padding: 28px; }
        }
    </style>
</head>
<body>
    <div class=\"shell\">
        <section class=\"hero\">
            <h1>Plan civil prep with one dashboard</h1>
            <p>Track daily capsules, trigger adaptive mock tests, and monitor progress in a single fast view. Start by creating a secure portal account.</p>
            <ul>
                <li>Centralise UPSC daily briefings</li>
                <li>Auto-generate adaptive study plans</li>
                <li>Resume exactly where you stopped</li>
            </ul>
        </section>

        <section class=\"panel\">
            <div class=\"tabs\">
                <button class=\"tab-btn active\" data-tab=\"login\">Login</button>
                <button class=\"tab-btn\" data-tab=\"signup\">Sign up</button>
            </div>

            <form id=\"loginForm\" class=\"active\">
                <label>Email
                    <input type=\"email\" id=\"loginEmail\" placeholder=\"you@example.com\" required />
                </label>
                <label>Password
                    <input type=\"password\" id=\"loginPassword\" placeholder=\"********\" required minlength=\"6\" />
                </label>
                <div class=\"status\" data-status=\"login\"></div>
                <button class=\"primary\" type=\"submit\">Access dashboard</button>
            </form>

            <form id=\"signupForm\">
                <label>Full name
                    <input type=\"text\" id=\"signupName\" placeholder=\"Aditi Sharma\" required minlength=\"2\" />
                </label>
                <label>Email
                    <input type=\"email\" id=\"signupEmail\" placeholder=\"you@example.com\" required />
                </label>
                <label>Phone number (optional)
                    <input type=\"tel\" id=\"signupPhone\" placeholder=\"+91 98xxxxxx\" />
                </label>
                <label>Password
                    <input type=\"password\" id=\"signupPassword\" placeholder=\"Strong password\" required minlength=\"6\" />
                </label>
                <div class=\"status\" data-status=\"signup\"></div>
                <button class=\"primary\" type=\"submit\">Create account</button>
            </form>
        </section>
    </div>

    <script>
    (function () {
        const existingToken = localStorage.getItem('cb_token');
        if (existingToken) {
            window.location.href = '/dashboard';
            return;
        }

        const tabButtons = document.querySelectorAll('.tab-btn');
        const forms = {
            login: document.getElementById('loginForm'),
            signup: document.getElementById('signupForm'),
        };

        function setActiveTab(tab) {
            tabButtons.forEach((btn) => {
                btn.classList.toggle('active', btn.dataset.tab === tab);
            });
            Object.entries(forms).forEach(([key, form]) => {
                form.classList.toggle('active', key === tab);
            });
        }

        tabButtons.forEach((btn) => {
            btn.addEventListener('click', () => setActiveTab(btn.dataset.tab));
        });

        function setStatus(scope, message, tone) {
            const el = document.querySelector(`[data-status="${scope}"]`);
            if (!el) return;
            el.textContent = message || '';
            el.className = 'status' + (tone ? ` ${tone}` : '');
        }

        async function handleAuth(url, payload, scope, button) {
            setStatus(scope, 'Working...', '');
            button.disabled = true;
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Request failed');
                }
                localStorage.setItem('cb_token', data.token);
                localStorage.setItem('cb_user', JSON.stringify(data.user));
                setStatus(scope, 'Success. Redirecting...', 'success');
                window.location.href = '/dashboard';
            } catch (err) {
                setStatus(scope, err.message || 'Unable to complete request', 'error');
            } finally {
                button.disabled = false;
            }
        }

        forms.login.addEventListener('submit', (event) => {
            event.preventDefault();
            const payload = {
                email: document.getElementById('loginEmail').value,
                password: document.getElementById('loginPassword').value,
            };
            handleAuth('/auth/login', payload, 'login', event.submitter);
        });

        forms.signup.addEventListener('submit', (event) => {
            event.preventDefault();
            const payload = {
                name: document.getElementById('signupName').value,
                email: document.getElementById('signupEmail').value,
                phone_number: document.getElementById('signupPhone').value || null,
                password: document.getElementById('signupPassword').value,
            };
            handleAuth('/auth/signup', payload, 'signup', event.submitter);
        });
    })();
    </script>
</body>
</html>
"""


DASHBOARD_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>CivicBriefs Dashboard</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f5f7fb;
            --panel: #ffffff;
            --muted: #6b7280;
            --accent: #2563eb;
            --border: #e5e7eb;
            --shadow: rgba(15, 23, 42, 0.08);
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            background: var(--bg);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: #0f172a;
        }

        header {
            padding: 28px clamp(16px, 6vw, 64px) 10px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }

        header h1 {
            margin: 0;
            font-size: clamp(28px, 4vw, 36px);
        }

        header p {
            margin: 6px 0 0;
            color: var(--muted);
        }

        .logout {
            border: 1px solid var(--border);
            background: white;
            border-radius: 999px;
            padding: 10px 18px;
            cursor: pointer;
            font-weight: 600;
        }

        main {
            padding: 0 clamp(16px, 6vw, 64px) 40px;
            display: grid;
            gap: 20px;
        }

        .grid {
            display: grid;
            gap: 20px;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        }

        .card {
            background: var(--panel);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid var(--border);
            box-shadow: 0 30px 60px var(--shadow);
        }

        .news-card {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .chip-group {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 4px;
            border-radius: 999px;
            background: #f1f5f9;
            flex-wrap: wrap;
        }

        .chip {
            border: none;
            background: transparent;
            color: var(--muted);
            font-weight: 600;
            border-radius: 999px;
            padding: 8px 16px;
            cursor: pointer;
            transition: background 0.2s ease, color 0.2s ease;
        }

        .chip.active {
            background: var(--accent);
            color: #fff;
            box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25);
        }

        .news-status {
            font-size: 14px;
            color: var(--muted);
        }

        .news-list {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .news-section {
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px;
            background: white;
        }

        .news-section__header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .news-articles {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .news-item {
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px;
            background: #fdfefe;
        }

        .news-item__head {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 8px;
        }

        .news-item__head h5 {
            margin: 0;
            font-size: 16px;
        }

        .news-item__head p {
            margin: 4px 0 0;
            font-size: 13px;
            color: var(--muted);
        }

        .news-item__head a {
            color: var(--accent);
            font-weight: 600;
            text-decoration: none;
            font-size: 13px;
        }

        .news-points {
            margin: 0 0 10px;
            padding-left: 18px;
            color: #0f172a;
            font-size: 14px;
        }

        .news-meta {
            font-size: 12px;
            color: var(--muted);
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        @media (min-width: 720px) {
            .news-meta {
                flex-direction: row;
                justify-content: space-between;
            }
        }

        .news-empty {
            margin: 0;
            color: var(--muted);
            font-style: italic;
        }

        .news-link-disabled {
            font-size: 13px;
            color: var(--muted);
            font-weight: 600;
        }

        .card h3 {
            margin: 0 0 12px;
            font-size: 20px;
        }

        .metric {
            font-size: 34px;
            font-weight: 700;
            margin: 8px 0;
        }

        .tag {
            display: inline-flex;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            background: rgba(37, 99, 235, 0.1);
            color: var(--accent);
            font-weight: 600;
        }

        .list {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .list li {
            display: flex;
            justify-content: space-between;
            font-size: 15px;
            color: var(--muted);
        }

        .btn,
        a.btn {
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 12px 16px;
            border-radius: 12px;
            background: var(--accent);
            color: white;
            font-weight: 600;
            margin-top: 18px;
            border: none;
            cursor: pointer;
            transition: opacity 0.2s ease;
        }

        .btn:disabled,
        a.btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }

        #status {
            text-align: center;
            color: var(--muted);
            padding: 10px;
        }

        .card--capsules {
            padding: 24px;
        }

        .capsule-header {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
        }

        .capsule-header h3 {
            margin: 4px 0;
        }

        .capsule-tabs {
            background: rgba(37, 99, 235, 0.08);
        }

        .capsule-wrapper {
            display: grid;
            grid-template-columns: minmax(220px, 320px) 1fr;
            gap: 18px;
        }

        .capsule-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 520px;
            overflow-y: auto;
            padding-right: 4px;
        }

        .capsule-card {
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 14px;
            background: #f8fafc;
            display: flex;
            flex-direction: column;
            gap: 6px;
            cursor: pointer;
            text-align: left;
            font: inherit;
            transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
        }

        .capsule-card strong {
            font-size: 16px;
        }

        .capsule-card small {
            color: var(--muted);
        }

        .capsule-card.active {
            border-color: var(--accent);
            background: rgba(37, 99, 235, 0.08);
            box-shadow: 0 15px 35px rgba(15, 23, 42, 0.12);
        }

        .capsule-detail {
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 18px;
            background: #fff;
            display: flex;
            flex-direction: column;
            gap: 18px;
            min-height: 320px;
        }

        .capsule-detail__meta {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
        }

        .capsule-detail__eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 12px;
            color: var(--muted);
            margin: 0;
        }

        .capsule-detail__stats {
            display: flex;
            gap: 12px;
            font-size: 13px;
            color: var(--muted);
        }

        .capsule-detail__coverage {
            margin: 0;
            color: var(--muted);
            font-size: 14px;
        }

        .capsule-detail__sections {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .capsule-section {
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px;
            background: #f9fafb;
        }

        .capsule-section h4 {
            margin: 0 0 8px;
        }

        .capsule-article {
            border: 1px solid rgba(37, 99, 235, 0.15);
            border-radius: 12px;
            padding: 12px;
            background: #fff;
            margin-bottom: 10px;
        }

        .capsule-article:last-child {
            margin-bottom: 0;
        }

        .capsule-article__head {
            display: flex;
            justify-content: space-between;
            gap: 8px;
            align-items: flex-start;
            margin-bottom: 8px;
        }

        .capsule-article__head h5 {
            margin: 0;
            font-size: 15px;
        }

        .capsule-article__head a {
            font-size: 13px;
            color: var(--accent);
            text-decoration: none;
            font-weight: 600;
        }

        .capsule-points {
            margin: 0 0 8px;
            padding-left: 20px;
            color: #0f172a;
            font-size: 14px;
        }

        .capsule-meta-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            font-size: 12px;
            color: var(--muted);
        }

        .capsule-meta-tags span {
            background: rgba(15, 23, 42, 0.04);
            padding: 4px 8px;
            border-radius: 999px;
        }

        .capsule-placeholder {
            margin: 0;
            color: var(--muted);
            font-style: italic;
        }

        @media (max-width: 960px) {
            .capsule-wrapper {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header>
        <div>
            <h1 id=\"welcomeTitle\">Dashboard</h1>
            <p id=\"welcomeSub\">Loading your workspace...</p>
        </div>
        <button class=\"logout\" id=\"logoutBtn\">Log out</button>
    </header>

    <div id=\"status\">Authenticating session...</div>

    <main id=\"content\" style=\"display:none;\">
        <section class=\"grid\" id=\"metricGrid\"></section>
        <section class=\"grid\">
            <article class=\"card\">
                <h3>Focus for this week</h3>
                <ul class=\"list\" id=\"focusList\"></ul>
                <a class=\"btn\" href=\"/agents/planner/ui\" target=\"_blank\">Open Planner Lab</a>
            </article>
            <article class=\"card\">
                <h3>Recent activity</h3>
                <ul class=\"list\" id=\"activityList\"></ul>
            </article>
            <article class="card">
                <h3>Daily news capsule</h3>
                <p style="color:var(--muted);margin:0 0 12px;">Get the top civic headlines delivered to your inbox every morning.</p>
                <button class="btn" id="subscribeBtn" type="button" disabled>Preparing...</button>
                <p class="news-status" id="subscribeStatus" aria-live="polite"></p>
            </article>
        </section>
        <section class="card card--capsules" id="capsuleBoard">
            <div class="capsule-header">
                <div>
                    <p class="capsule-detail__eyebrow">News capsules</p>
                    <h3>Browse daily, weekly, and monthly briefs</h3>
                    <p style="margin:4px 0 0;color:var(--muted);">Tap a window, pick any day, and read the curated capsule.</p>
                </div>
                <div class="chip-group capsule-tabs">
                    <button class="chip active" type="button" data-capsule-range="daily">Daily</button>
                    <button class="chip" type="button" data-capsule-range="weekly">Weekly</button>
                    <button class="chip" type="button" data-capsule-range="monthly">Monthly</button>
                </div>
            </div>
            <div class="capsule-wrapper">
                <div class="capsule-list" id="capsuleList">
                    <p class="capsule-placeholder">Choose a window above to load capsules.</p>
                </div>
                <div class="capsule-detail" id="capsuleDetail">
                    <p class="capsule-placeholder">Select a capsule to read its summary.</p>
                </div>
            </div>
            <p class="news-status" id="capsuleStatus" aria-live="polite">Waiting for selection...</p>
        </section>
    </main>

    <script>
    (function () {
        const statusEl = document.getElementById('status');
        const contentEl = document.getElementById('content');
        const logoutBtn = document.getElementById('logoutBtn');
        const metricGrid = document.getElementById('metricGrid');
        const focusList = document.getElementById('focusList');
        const activityList = document.getElementById('activityList');
        const welcomeTitle = document.getElementById('welcomeTitle');
        const welcomeSub = document.getElementById('welcomeSub');
        const subscribeBtn = document.getElementById('subscribeBtn');
        const subscribeStatus = document.getElementById('subscribeStatus');
        const capsuleTabs = document.querySelectorAll('[data-capsule-range]');
        const capsuleList = document.getElementById('capsuleList');
        const capsuleDetail = document.getElementById('capsuleDetail');
        const capsuleStatus = document.getElementById('capsuleStatus');

        const capsuleState = {
            activeRange: 'daily',
            capsules: [],
            selectedDate: null,
            initialized: false,
            isLoading: false,
        };
        const dateFormatOptions = { day: 'numeric', month: 'short', year: 'numeric' };

        let currentUser = null;

        const token = localStorage.getItem('cb_token');
        if (!token) {
            window.location.href = '/';
            return;
        }

        function clearSession() {
            localStorage.removeItem('cb_token');
            localStorage.removeItem('cb_user');
        }

        logoutBtn.addEventListener('click', async () => {
            try {
                await fetch('/auth/logout', {
                    method: 'POST',
                    headers: { Authorization: `Bearer ${token}` },
                });
            } catch (err) {
                // ignore
            } finally {
                clearSession();
                window.location.href = '/';
            }
        });

        function renderMetrics(user) {
            const metrics = [
                { label: 'Daily capsules read', value: 12, trend: '+3% vs avg' },
                { label: 'Adaptive tests taken', value: 4, trend: '1 pending review' },
                { label: 'Revision streak', value: '6 days', trend: 'Keep it going' },
                { label: 'Upcoming reminders', value: 2, trend: 'Planner synced' },
            ];
            metricGrid.innerHTML = '';
            metrics.forEach((metric) => {
                const card = document.createElement('article');
                card.className = 'card';
                card.innerHTML = `<div class="tag">${metric.label}</div><div class="metric">${metric.value}</div><p style="color:var(--muted);margin:0;">${metric.trend}</p>`;
                metricGrid.appendChild(card);
            });
        }

        function renderFocus(user) {
            const presets = [
                'Revise polity NCERT summary before 8 PM',
                'Attempt 15-question mock on modern history',
                'Summarise one Hindu editorial into your notes',
            ];
            focusList.innerHTML = '';
            presets.forEach((item) => {
                const li = document.createElement('li');
                li.innerHTML = `<span>${item}</span><span class="tag" style="background:rgba(16,185,129,0.15);color:#047857;">Scheduled</span>`;
                focusList.appendChild(li);
            });
        }

        function formatScore(value) {
            const num = Number(value);
            if (!Number.isFinite(num)) {
                return null;
            }
            if (Math.abs(num - Math.round(num)) < 0.05) {
                return `${Math.round(num)}%`;
            }
            return `${num.toFixed(1)}%`;
        }

        function buildActivityDetail(report) {
            const parts = [];
            const sectionTexts = Array.isArray(report.sections)
                ? report.sections
                      .filter((section) => section && typeof section.label === 'string')
                      .slice(0, 2)
                      .map((section) => {
                          const sectionScore = formatScore(section.accuracy);
                          return sectionScore ? `${section.label}: ${sectionScore}` : section.label;
                      })
                : [];
            if (sectionTexts.length) {
                parts.push(sectionTexts.join(' | '));
            }
            const totalCorrect = Number(report.total_correct);
            const totalQuestions = Number(report.total_questions);
            if (Number.isFinite(totalCorrect) && Number.isFinite(totalQuestions) && totalQuestions > 0) {
                parts.push(`${totalCorrect}/${totalQuestions} correct`);
            }
            return parts.join(' • ') || 'Section-wise breakdown unavailable.';
        }

        function renderActivityPlaceholder(message) {
            if (!activityList) {
                return;
            }
            activityList.innerHTML = '';
            const li = document.createElement('li');
            const label = document.createElement('span');
            label.textContent = message;
            const timeTag = document.createElement('span');
            timeTag.textContent = '';
            li.appendChild(label);
            li.appendChild(timeTag);
            activityList.appendChild(li);
        }

        function renderActivityEntry(report) {
            if (!activityList) {
                return;
            }
            activityList.innerHTML = '';
            if (!report) {
                renderActivityPlaceholder('No mock attempts recorded yet.');
                return;
            }
            const entry = document.createElement('li');
            const label = document.createElement('span');
            const heading = formatScore(report.overall_accuracy)
                ? `Mock result • ${formatScore(report.overall_accuracy)}`
                : 'Mock result';
            const detail = document.createElement('small');
            detail.textContent = buildActivityDetail(report);
            label.textContent = heading;
            label.appendChild(document.createElement('br'));
            label.appendChild(detail);

            const timeTag = document.createElement('span');
            timeTag.textContent = formatActivityDate(report.date);
            entry.appendChild(label);
            entry.appendChild(timeTag);
            activityList.appendChild(entry);

            if (report.feedback_summary) {
                const feedbackItem = document.createElement('li');
                const feedbackLabel = document.createElement('span');
                const feedbackDetail = document.createElement('small');
                feedbackLabel.textContent = 'Feedback';
                feedbackLabel.appendChild(document.createElement('br'));
                feedbackDetail.textContent = report.feedback_summary;
                feedbackLabel.appendChild(feedbackDetail);
                const spacer = document.createElement('span');
                spacer.textContent = '';
                feedbackItem.appendChild(feedbackLabel);
                feedbackItem.appendChild(spacer);
                activityList.appendChild(feedbackItem);
            }
        }

        function formatActivityDate(value) {
            if (!value) {
                return '—';
            }
            const parsed = new Date(value);
            if (Number.isNaN(parsed.getTime())) {
                return value;
            }
            const now = new Date();
            const diffMs = now.getTime() - parsed.getTime();
            if (diffMs < 0) {
                return parsed.toLocaleDateString(undefined, dateFormatOptions);
            }
            const diffMinutes = Math.floor(diffMs / 60000);
            if (diffMinutes < 1) {
                return 'just now';
            }
            if (diffMinutes < 60) {
                return `${diffMinutes} min${diffMinutes === 1 ? '' : 's'} ago`;
            }
            const diffHours = Math.floor(diffMinutes / 60);
            if (diffHours < 24) {
                return `${diffHours} hr${diffHours === 1 ? '' : 's'} ago`;
            }
            return parsed.toLocaleDateString(undefined, dateFormatOptions);
        }

        async function loadRecentActivity() {
            if (!activityList) {
                return;
            }
            renderActivityPlaceholder('Loading your latest mock result...');
            try {
                const res = await fetch('/agents/planner/report/latest', {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (res.status === 404) {
                    renderActivityEntry(null);
                    return;
                }
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Unable to load activity');
                }
                renderActivityEntry(data.report);
            } catch (err) {
                console.error(err);
                renderActivityPlaceholder('Unable to load latest report right now.');
            }
        }

        async function subscribeToCapsule() {
            if (!subscribeBtn || !currentUser) {
                return;
            }

            subscribeBtn.disabled = true;
            subscribeBtn.textContent = 'Subscribing...';
            if (subscribeStatus) {
                subscribeStatus.style.color = 'var(--muted)';
                subscribeStatus.textContent = 'Adding you to the list...';
            }

            try {
                const res = await fetch('/auth/subscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name: currentUser.name, email: currentUser.email }),
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Unable to subscribe right now.');
                }
                if (subscribeStatus) {
                    subscribeStatus.style.color = '#047857';
                    subscribeStatus.textContent = data.message || 'Subscribed!';
                }
                subscribeBtn.textContent = 'Subscribed';
            } catch (err) {
                if (subscribeStatus) {
                    subscribeStatus.style.color = '#dc2626';
                    subscribeStatus.textContent = err.message || 'Failed to subscribe. Try again later.';
                }
                subscribeBtn.disabled = false;
                subscribeBtn.textContent = 'Subscribe to daily capsule';
            }
        }

        if (subscribeBtn) {
            subscribeBtn.addEventListener('click', subscribeToCapsule);
        }

        capsuleTabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                const range = tab.dataset.capsuleRange;
                if (!range || capsuleState.isLoading || capsuleState.activeRange === range) {
                    return;
                }
                setActiveCapsuleTab(range);
                fetchCapsules(range);
            });
        });

        function setActiveCapsuleTab(range) {
            capsuleState.activeRange = range;
            capsuleTabs.forEach((tab) => {
                tab.classList.toggle('active', tab.dataset.capsuleRange === range);
            });
        }

        function toggleCapsuleTabs(disabled) {
            capsuleTabs.forEach((tab) => {
                tab.disabled = disabled;
            });
        }

        function initializeCapsuleBoard() {
            if (capsuleState.initialized || !capsuleList || !capsuleStatus) {
                return;
            }
            capsuleState.initialized = true;
            setActiveCapsuleTab(capsuleState.activeRange);
            fetchCapsules(capsuleState.activeRange);
        }

        async function fetchCapsules(range) {
            if (!capsuleList || !capsuleDetail || !capsuleStatus) {
                return;
            }
            capsuleState.isLoading = true;
            toggleCapsuleTabs(true);
            capsuleState.capsules = [];
            capsuleState.selectedDate = null;
            capsuleList.innerHTML = `<p class="capsule-placeholder">Loading ${range} capsules...</p>`;
            capsuleDetail.innerHTML = '<p class="capsule-placeholder">Loading capsule details...</p>';
            capsuleStatus.textContent = 'Fetching capsules...';
            try {
                const res = await fetch(`/news/capsules?window=${range}`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Unable to fetch capsules.');
                }
                capsuleState.capsules = Array.isArray(data.capsules) ? data.capsules : [];
                if (!capsuleState.capsules.length) {
                    capsuleStatus.textContent = 'No capsules available for this window yet.';
                    capsuleList.innerHTML = '<p class="capsule-placeholder">Generate a capsule and check back soon.</p>';
                    capsuleDetail.innerHTML = '<p class="capsule-placeholder">No capsule selected.</p>';
                    return;
                }
                capsuleStatus.textContent = `Showing ${capsuleState.capsules.length} ${range} capsule${capsuleState.capsules.length > 1 ? 's' : ''} - ${formatWindowRange(data.window)}`;
                renderCapsuleList();
                selectCapsule(capsuleState.capsules[0].date);
            } catch (err) {
                capsuleStatus.textContent = err.message || 'Failed to load capsules.';
                capsuleList.innerHTML = '<p class="capsule-placeholder">Unable to load capsules right now.</p>';
                capsuleDetail.innerHTML = '<p class="capsule-placeholder">Try reloading in a moment.</p>';
            } finally {
                capsuleState.isLoading = false;
                toggleCapsuleTabs(false);
            }
        }

        function renderCapsuleList() {
            if (!capsuleList) {
                return;
            }
            capsuleList.innerHTML = '';
            capsuleState.capsules.forEach((capsule) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'capsule-card' + (capsuleState.selectedDate === capsule.date ? ' active' : '');
                const weekdayText = escapeHtml(capsule.weekday || '');
                const dateText = escapeHtml(formatDateLabel(capsule.date));
                const briefsText = escapeHtml(`${(capsule.totals && capsule.totals.articles) || 0} briefs`);
                const coverageText = escapeHtml(deriveCoverageLabel(capsule));
                btn.innerHTML = `
                    <small>${weekdayText}</small>
                    <strong>${dateText}</strong>
                    <small>${briefsText}</small>
                    <p style="margin:4px 0 0;">${coverageText}</p>
                `;
                btn.addEventListener('click', () => selectCapsule(capsule.date));
                capsuleList.appendChild(btn);
            });
        }

        function selectCapsule(date) {
            const capsule = capsuleState.capsules.find((item) => item.date === date);
            if (!capsule) {
                return;
            }
            capsuleState.selectedDate = date;
            renderCapsuleList();
            renderCapsuleDetail(capsule);
        }

        function renderCapsuleDetail(capsule) {
            if (!capsuleDetail) {
                return;
            }
            capsuleDetail.innerHTML = '';
            const header = document.createElement('div');
            header.className = 'capsule-detail__meta';
            const weekday = escapeHtml(capsule.weekday || '');
            const dateText = escapeHtml(formatDateLabel(capsule.date));
            const articleCount = escapeHtml(((capsule.totals && capsule.totals.articles) || 0).toString());
            const categoryCount = escapeHtml(((capsule.totals && capsule.totals.categories) || 0).toString());
            header.innerHTML = `
                <div>
                    <p class="capsule-detail__eyebrow">${weekday}</p>
                    <h4 style="margin:4px 0;">${dateText}</h4>
                </div>
                <div class="capsule-detail__stats">
                    <span>${articleCount} articles</span>
                    <span>${categoryCount} categories</span>
                </div>
            `;
            capsuleDetail.appendChild(header);

            const coverageLine = document.createElement('p');
            coverageLine.className = 'capsule-detail__coverage';
            coverageLine.textContent = deriveCoverageDetail(capsule);
            capsuleDetail.appendChild(coverageLine);

            const sectionGroup = document.createElement('div');
            sectionGroup.className = 'capsule-detail__sections';
            const sections = Array.isArray(capsule.sections) ? capsule.sections : [];
            if (!sections.length) {
                sectionGroup.innerHTML = '<p class="capsule-placeholder">No category breakdown yet.</p>';
            } else {
                sections.forEach((section) => {
                    const sectionEl = document.createElement('section');
                    sectionEl.className = 'capsule-section';
                    const label = escapeHtml(section.label || 'General');
                    const total = escapeHtml((section.total_articles || 0).toString());
                    sectionEl.innerHTML = `<h4>${label}<span style="color:var(--muted);font-weight:400;margin-left:8px;">${total} articles</span></h4>`;
                    const articles = Array.isArray(section.articles) ? section.articles : [];
                    if (!articles.length) {
                        const empty = document.createElement('p');
                        empty.className = 'capsule-placeholder';
                        empty.textContent = 'No articles available for this section.';
                        sectionEl.appendChild(empty);
                    } else {
                        articles.forEach((article) => {
                            sectionEl.appendChild(buildCapsuleArticle(article));
                        });
                    }
                    sectionGroup.appendChild(sectionEl);
                });
            }
            capsuleDetail.appendChild(sectionGroup);
        }

        function buildCapsuleArticle(article) {
            const wrapper = document.createElement('article');
            wrapper.className = 'capsule-article';
            const head = document.createElement('div');
            head.className = 'capsule-article__head';
            const textWrap = document.createElement('div');
            const sourceLabel = article.source || 'Unknown source';
            const safeTitle = escapeHtml(article.title || 'Untitled brief');
            const safeSource = escapeHtml(sourceLabel);
            textWrap.innerHTML = `<h5>${safeTitle}</h5><p style="margin:4px 0 0;color:var(--muted);">${safeSource}</p>`;
            head.appendChild(textWrap);
            if (article.url) {
                const link = document.createElement('a');
                link.href = article.url;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = 'Open link';
                head.appendChild(link);
            } else {
                const span = document.createElement('span');
                span.className = 'news-link-disabled';
                span.textContent = 'No link available';
                head.appendChild(span);
            }
            wrapper.appendChild(head);

            wrapper.appendChild(buildBulletList(article.summary_points));

            const metaTags = document.createElement('div');
            metaTags.className = 'capsule-meta-tags';
            const pyqLabel = escapeHtml(firstValue(article.pyq_points));
            const syllabusLabel = escapeHtml(firstValue(article.syllabus_points));
            metaTags.innerHTML = `<span>PYQ: ${pyqLabel}</span><span>Syllabus: ${syllabusLabel}</span>`;
            wrapper.appendChild(metaTags);
            return wrapper;
        }

        function buildBulletList(points) {
            const list = document.createElement('ul');
            list.className = 'capsule-points';
            const safePoints = Array.isArray(points) ? points : [];
            if (!safePoints.length) {
                const li = document.createElement('li');
                li.textContent = 'Summary coming soon.';
                list.appendChild(li);
                return list;
            }
            safePoints.slice(0, 3).forEach((point) => {
                const li = document.createElement('li');
                li.textContent = point;
                list.appendChild(li);
            });
            if (safePoints.length > 3) {
                const more = document.createElement('li');
                more.textContent = `+${safePoints.length - 3} more points`;
                more.style.color = 'var(--muted)';
                list.appendChild(more);
            }
            return list;
        }

        function firstValue(items) {
            if (!Array.isArray(items) || !items.length) {
                return 'None';
            }
            return items[0];
        }

        function deriveCoverageLabel(capsule) {
            const coverage = capsule && capsule.totals && Array.isArray(capsule.totals.coverage)
                ? capsule.totals.coverage
                : [];
            if (!coverage.length) {
                return 'Coverage TBD';
            }
            return coverage.slice(0, 2).map((item) => item.category || 'General').join(' | ');
        }

        function deriveCoverageDetail(capsule) {
            const coverage = capsule && capsule.totals && Array.isArray(capsule.totals.coverage)
                ? capsule.totals.coverage
                : [];
            if (!coverage.length) {
                return 'Coverage snapshot not available yet.';
            }
            return coverage.slice(0, 3).map((item) => `${item.category} (${item.count})`).join(' | ');
        }

        const HTML_ESCAPE_ENTITIES = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
        };

        function escapeHtml(value) {
            if (value === undefined || value === null) {
                return '';
            }
            return String(value).replace(/[&<>"']/g, (char) => HTML_ESCAPE_ENTITIES[char] || char);
        }

        function formatDateLabel(value) {
            if (!value) {
                return '';
            }
            const parsed = new Date(value);
            if (Number.isNaN(parsed.getTime())) {
                return value;
            }
            return parsed.toLocaleDateString(undefined, dateFormatOptions);
        }

        function formatWindowRange(meta) {
            if (!meta || !meta.start || !meta.end) {
                return '';
            }
            const start = formatDateLabel(meta.start);
            const end = formatDateLabel(meta.end);
            return start === end ? start : `${start} - ${end}`;
        }

        async function hydrate() {
            try {
                const res = await fetch('/auth/session', {
                    headers: { Authorization: `Bearer ${token}` },
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Session invalid');
                }
                const user = data.user;
                currentUser = user;
                welcomeTitle.textContent = `Hi, ${user.name}`;
                welcomeSub.textContent = 'Here is your prep snapshot for today.';
                renderMetrics(user);
                renderFocus(user);
                loadRecentActivity();
                if (subscribeBtn) {
                    subscribeBtn.disabled = false;
                    subscribeBtn.textContent = 'Subscribe to daily capsule';
                }
                initializeCapsuleBoard();
                statusEl.style.display = 'none';
                contentEl.style.display = 'grid';
            } catch (err) {
                statusEl.textContent = 'Session expired. Please log in again.';
                clearSession();
                setTimeout(() => window.location.href = '/', 1500);
            }
        }

        hydrate();
    })();
    </script>
</body>
</html>
"""


def render_portal_page() -> str:
    return PORTAL_HTML


def render_dashboard_page() -> str:
    return DASHBOARD_HTML
