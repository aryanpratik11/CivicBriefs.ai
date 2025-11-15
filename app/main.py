# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api.routes.agents import router as agents_router

app = FastAPI(title="CivicBriefs.AI", version="0.1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the News Agent router
app.include_router(agents_router)

@app.get("/", response_class=HTMLResponse)
def home():
    html = """
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>CivicBriefs Hub</title>
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
    <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap\" rel=\"stylesheet\">
    <style>
        :root {
            color-scheme: light;
            --bg: #f5f7fb;
            --surface: rgba(255, 255, 255, 0.9);
            --accent: #1f6feb;
            --accent-soft: rgba(31, 111, 235, 0.12);
            --text: #101828;
            --muted: #6b7280;
            --border: rgba(15, 23, 42, 0.08);
            --success: #16a34a;
            --error: #dc2626;
            --shadow: 0 24px 48px rgba(30, 41, 59, 0.12);
        }

        *, *::before, *::after {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: radial-gradient(circle at 20% 20%, rgba(79, 70, 229, 0.12), transparent 40%),
                        radial-gradient(circle at 80% 10%, rgba(14, 116, 144, 0.15), transparent 45%),
                        var(--bg);
            color: var(--text);
        }

        .noise {
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" preserveAspectRatio=\"none\" viewBox=\"0 0 200 200\"><filter id=\"n\"><feTurbulence type=\"fractalNoise\" baseFrequency=\"2.4\" numOctaves=\"3\" stitchTiles=\"stitch\"/></filter><rect width=\"100%\" height=\"100%\" filter=\"url(%23n)\" opacity=\"0.035\"/></svg>');
            z-index: 0;
        }

        .page {
            position: relative;
            z-index: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 48px 20px 64px;
        }

        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 36px;
        }

        header h1 {
            font-size: 30px;
            margin: 0;
            letter-spacing: -0.02em;
        }

        header p {
            margin: 6px 0 0;
            color: var(--muted);
            font-size: 15px;
        }

        .hero {
            display: grid;
            gap: 24px;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        }

        .card {
            background: var(--surface);
            border-radius: 22px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            padding: 32px;
            backdrop-filter: blur(12px);
        }

        .auth-tabs {
            display: inline-flex;
            padding: 6px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.6);
            border: 1px solid var(--border);
            margin-bottom: 24px;
        }

        .auth-tabs button {
            border: none;
            background: none;
            padding: 10px 22px;
            border-radius: 999px;
            font-weight: 600;
            color: var(--muted);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .auth-tabs button.active {
            background: var(--accent);
            color: #ffffff;
            box-shadow: 0 12px 24px rgba(31, 111, 235, 0.25);
        }

        form {
            display: grid;
            gap: 16px;
        }

        label {
            display: grid;
            gap: 6px;
            font-weight: 500;
            font-size: 14px;
            color: var(--muted);
        }

        input {
            padding: 12px 14px;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: rgba(255, 255, 255, 0.9);
            font-size: 15px;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-soft);
        }

        .actions {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 6px;
        }

        button.primary {
            padding: 12px 18px;
            border-radius: 12px;
            border: none;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #ffffff;
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            transition: transform 0.1s ease, box-shadow 0.2s ease;
        }

        button.primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 32px rgba(37, 99, 235, 0.25);
        }

        .muted-link {
            color: var(--muted);
            font-size: 14px;
            text-align: center;
        }

        .error {
            color: var(--error);
            font-size: 13px;
            min-height: 18px;
        }

        .success {
            color: var(--success);
            font-size: 13px;
            min-height: 18px;
        }

        .hidden {
            display: none !important;
        }

        .dashboard {
            display: grid;
            gap: 24px;
        }

        .welcome-card {
            background: linear-gradient(135deg, rgba(31, 111, 235, 0.12), transparent 60%);
            border-radius: 18px;
            padding: 28px;
            border: 1px solid var(--border);
        }

        .welcome-card h2 {
            margin: 0 0 12px;
            font-size: 24px;
        }

        .quick-stats {
            display: grid;
            gap: 16px;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        }

        .stat {
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 18px;
            background: rgba(255, 255, 255, 0.75);
        }

        .stat span {
            display: block;
            color: var(--muted);
            font-size: 13px;
        }

        .stat strong {
            font-size: 22px;
            display: block;
            margin-top: 6px;
        }

        .grid {
            display: grid;
            gap: 20px;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        }

        .tile {
            border-radius: 18px;
            border: 1px solid var(--border);
            padding: 22px;
            background: rgba(255, 255, 255, 0.85);
            display: flex;
            flex-direction: column;
            gap: 12px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .tile:hover {
            transform: translateY(-4px);
            box-shadow: 0 18px 38px rgba(15, 23, 42, 0.12);
        }

        .tile h3 {
            margin: 0;
            font-size: 20px;
        }

        .tile p {
            margin: 0;
            color: var(--muted);
            font-size: 14px;
            line-height: 1.5;
        }

        .tile button {
            align-self: flex-start;
            margin-top: auto;
            padding: 10px 18px;
            border-radius: 10px;
            border: none;
            background: var(--accent);
            color: #ffffff;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s ease;
        }

        .tile button:hover {
            opacity: 0.9;
        }

        .nav {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .profile-chip {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid var(--border);
            font-size: 14px;
            color: var(--muted);
        }

        .logout {
            border: none;
            background: none;
            color: var(--accent);
            font-size: 14px;
            cursor: pointer;
            padding: 6px 10px;
        }

        @media (max-width: 640px) {
            header {
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }
            .card {
                padding: 24px;
            }
            .tile h3 {
                font-size: 18px;
            }
        }
    </style>
</head>
<body>
    <div class=\"noise\"></div>
    <div class=\"page\">
        <header>
            <div>
                <h1>CivicBriefs Hub</h1>
                <p>Curated UPSC intelligence, adaptive tests, and personalised planning.</p>
            </div>
            <div class=\"nav\" id=\"navBar\"></div>
        </header>

        <div class=\"hero\">
            <section class=\"card\" id=\"authCard\">
                <div class=\"auth-tabs\">
                    <button class=\"active\" id=\"loginTab\">Log in</button>
                    <button id=\"signupTab\">Sign up</button>
                </div>

                <form id=\"loginForm\">
                    <label>
                        Email address
                        <input type=\"email\" name=\"email\" placeholder=\"you@example.com\" required />
                    </label>
                    <label>
                        Password
                        <input type=\"password\" name=\"password\" placeholder=\"Enter your password\" required />
                    </label>
                    <div class=\"actions\">
                        <button type=\"submit\" class=\"primary\">Access dashboard</button>
                        <span class=\"muted-link\">Forgot password? <a href=\"#\">Reset</a></span>
                    </div>
                    <div class=\"error\" id=\"loginError\"></div>
                </form>

                <form id=\"signupForm\" class=\"hidden\">
                    <label>
                        Name
                        <input type=\"text\" name=\"name\" placeholder=\"Full name\" required />
                    </label>
                    <label>
                        Email address
                        <input type=\"email\" name=\"email\" placeholder=\"you@example.com\" required />
                    </label>
                    <label>
                        Phone number
                        <input type=\"tel\" name=\"phone\" placeholder=\"+91 99999 99999\" required />
                    </label>
                    <label>
                        Password
                        <input type=\"password\" name=\"password\" placeholder=\"Create a strong password\" required />
                    </label>
                    <div class=\"actions\">
                        <button type=\"submit\" class=\"primary\">Create account</button>
                    </div>
                    <div class=\"success\" id=\"signupSuccess\"></div>
                </form>
            </section>

            <section class=\"card hidden\" id=\"dashboardCard\">
                <div class=\"dashboard\">
                    <div class=\"welcome-card\">
                        <h2 id=\"welcomeTitle\">Welcome back</h2>
                        <p id=\"welcomeSubtitle\">Stay informed with the latest briefs and convert insights into smarter attempts.</p>
                        <div class=\"quick-stats\">
                            <div class=\"stat\">
                                <span>Reading streak</span>
                                <strong id=\"statReading\">0 days</strong>
                            </div>
                            <div class=\"stat\">
                                <span>Mock accuracy</span>
                                <strong id=\"statAccuracy\">-- %</strong>
                            </div>
                            <div class=\"stat\">
                                <span>Upcoming test</span>
                                <strong id=\"statNextTest\">Schedule now</strong>
                            </div>
                        </div>
                    </div>

                    <div class=\"grid\">
                        <article class=\"tile\">
                            <h3>Today's briefings</h3>
                            <p>Handpicked UPSC current affairs distilled into actionable takeaways. Updated daily at 8 AM IST.</p>
                            <button onclick=\"window.location='/agents/news'\">Refresh feed</button>
                        </article>
                        <article class=\"tile\">
                            <h3>Weekly digest</h3>
                            <p>Seven-day narrative with editorial notes, PYQ mapping, and mind-map prompts.</p>
                            <button>Open digest</button>
                        </article>
                        <article class=\"tile\">
                            <h3>Monthly dossier</h3>
                            <p>Comprehensive coverage across polity, economy, enviro-sci, and IR with downloadable PDF pack.</p>
                            <button>Download dossier</button>
                        </article>
                        <article class=\"tile\">
                            <h3>Adaptive mock lab</h3>
                            <p>Generate a sectional test, evaluate performance, and unlock a tailored study plan instantly.</p>
                            <button onclick=\"window.location='/agents/planner/ui'\">Launch mock</button>
                        </article>
                    </div>
                </div>
            </section>
        </div>
    </div>

    <script>
    (function () {
        const loginTab = document.getElementById('loginTab');
        const signupTab = document.getElementById('signupTab');
        const loginForm = document.getElementById('loginForm');
        const signupForm = document.getElementById('signupForm');
        const authCard = document.getElementById('authCard');
        const dashboardCard = document.getElementById('dashboardCard');
        const navBar = document.getElementById('navBar');
        const loginError = document.getElementById('loginError');
        const signupSuccess = document.getElementById('signupSuccess');
        const welcomeTitle = document.getElementById('welcomeTitle');
        const statReading = document.getElementById('statReading');
        const statAccuracy = document.getElementById('statAccuracy');
        const statNextTest = document.getElementById('statNextTest');

        function toggleTab(tab) {
            if (tab === 'login') {
                loginTab.classList.add('active');
                signupTab.classList.remove('active');
                loginForm.classList.remove('hidden');
                signupForm.classList.add('hidden');
            } else {
                signupTab.classList.add('active');
                loginTab.classList.remove('active');
                signupForm.classList.remove('hidden');
                loginForm.classList.add('hidden');
            }
            loginError.textContent = '';
            signupSuccess.textContent = '';
            signupSuccess.className = 'success';
        }

        function saveProfile(profile) {
            localStorage.setItem('cb_profile', JSON.stringify(profile));
        }

        function loadProfile() {
            try {
                const raw = localStorage.getItem('cb_profile');
                return raw ? JSON.parse(raw) : null;
            } catch (err) {
                console.error(err);
                return null;
            }
        }

        function showDashboard(profile) {
            if (!profile) {
                return;
            }
            authCard.classList.add('hidden');
            dashboardCard.classList.remove('hidden');
            welcomeTitle.textContent = 'Welcome back, ' + profile.name;
            statReading.textContent = (profile.readingStreak || 3) + ' days';
            statAccuracy.textContent = profile.mockAccuracy ? profile.mockAccuracy + ' %' : 'Add attempt';
            statNextTest.textContent = profile.nextTest || 'Mock pending';

            navBar.innerHTML = '';
            const chip = document.createElement('span');
            chip.className = 'profile-chip';
            chip.textContent = profile.email;

            const logoutBtn = document.createElement('button');
            logoutBtn.className = 'logout';
            logoutBtn.textContent = 'Log out';
            logoutBtn.addEventListener('click', () => {
                localStorage.removeItem('cb_profile');
                dashboardCard.classList.add('hidden');
                authCard.classList.remove('hidden');
                navBar.innerHTML = '';
                toggleTab('login');
            });

            navBar.appendChild(chip);
            navBar.appendChild(logoutBtn);
        }

        loginTab.addEventListener('click', () => toggleTab('login'));
        signupTab.addEventListener('click', () => toggleTab('signup'));

        loginForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const formData = new FormData(loginForm);
            const email = String(formData.get('email') || '').trim().toLowerCase();
            const password = String(formData.get('password') || '').trim();

            if (!email || !password) {
                loginError.textContent = 'Please fill in your credentials.';
                return;
            }

            const profile = loadProfile();
            if (profile && profile.email === email) {
                showDashboard(profile);
            } else {
                loginError.textContent = 'Account not found. Sign up to get started.';
            }
        });

        signupForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const formData = new FormData(signupForm);
            const name = String(formData.get('name') || '').trim();
            const email = String(formData.get('email') || '').trim().toLowerCase();
            const phone = String(formData.get('phone') || '').trim();
            const password = String(formData.get('password') || '').trim();

            if (!name || !email || !phone || !password) {
                signupSuccess.textContent = '';
                signupSuccess.className = 'error';
                signupSuccess.textContent = 'Complete all fields to continue.';
                return;
            }

            const profile = {
                name,
                email,
                phone,
                mockAccuracy: '--',
                readingStreak: 1,
                nextTest: 'Plan a mock',
            };
            saveProfile(profile);
            signupSuccess.className = 'success';
            signupSuccess.textContent = 'Account created. Switch to log in to continue.';
            setTimeout(() => toggleTab('login'), 1500);
        });

        const existingProfile = loadProfile();
        if (existingProfile) {
            showDashboard(existingProfile);
        }
    })();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)
