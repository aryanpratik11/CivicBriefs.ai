# app/api/routes/agents.py
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from app.agents.news_agent import NewsAgent
from app.agents.planner_agent import PlannerAgent
from app.api.routes.auth import _current_user
from app.services.report_store import report_store


router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/news")
def run_news_agent():
    """
    Trigger the NewsAgent to fetch and embed UPSC-relevant news.
    """
    agent = NewsAgent(
        query="UPSC OR civil services OR current affairs OR Indian polity",
        fetch_limit=10
    )
    agent.run()
    return {"status": "success", "message": "NewsAgent executed successfully ✅"}


@router.post("/planner")
def generate_planner(payload: dict = Body(...)):
    """Generate a personalized UPSC planner from the provided performance JSON.

    Example request body:
    {
        "user_id": "U_45",
        "performance": {"History":52, "Polity":72, "Geography":35}
    }
    """
    perf = payload.get("performance") if isinstance(payload.get("performance"), dict) else payload

    if not isinstance(perf, dict):
        raise HTTPException(status_code=400, detail="performance must be a dict mapping subjects to scores")

    user_id = payload.get("user_id") if isinstance(payload, dict) else None
    user_email = None
    if isinstance(payload, dict):
        user_email = payload.get("user_email") or payload.get("email")

    planner = PlannerAgent()
    out = planner.generate(perf, user_id=user_id, user_email=user_email)
    return JSONResponse(content={"status": "success", "planner": out})


@router.get("/planner/test")
def create_planner_test(questions_per_section: int = 15):
    agent = PlannerAgent()
    try:
        test = agent.prepare_test(questions_per_section=questions_per_section)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return JSONResponse(content={"status": "success", "test": test})


@router.post("/planner/test/submit")
def submit_planner_test(payload: dict = Body(...)):
    user_id = payload.get("user_id")
    answers = payload.get("answers")

    if not isinstance(answers, dict) or not answers:
        raise HTTPException(status_code=400, detail="answers must be a non-empty mapping of question_id to selected option")

    agent = PlannerAgent()

    try:
        result = agent.evaluate_test(user_id=user_id, answers=answers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return JSONResponse(content={"status": "success", "result": result})


@router.get("/planner/report/latest")
def latest_planner_report(context=Depends(_current_user)):
    user, _ = context
    latest = report_store.latest_for_user(user_id=user.get("id"), user_email=user.get("email"))
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No planner reports available yet.")
    return JSONResponse(content={"status": "success", "report": latest})


@router.get("/planner/ui", response_class=HTMLResponse)
def planner_ui():
    html = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>CivicBriefs Planner Workspace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            color-scheme: light;
            --bg: #f7f9fc;
            --panel: #ffffff;
            --accent: #2563eb;
            --accent-soft: rgba(37, 99, 235, 0.1);
            --text: #111827;
            --muted: #6b7280;
            --border: #e5e7eb;
            --error: #dc2626;
            --success: #16a34a;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #eef3ff 0%, #fef9f5 100%);
            color: var(--text);
        }

        .page {
            max-width: 1100px;
            margin: 0 auto;
            padding: 32px 20px 48px;
        }

        header {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 24px;
        }

        header h1 {
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 0;
        }

        header p {
            margin: 0;
            color: var(--muted);
            font-size: 15px;
            max-width: 720px;
        }

        .card {
            background: var(--panel);
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
            border: 1px solid var(--border);
            padding: 24px;
            margin-bottom: 24px;
        }

        .controls {
            display: grid;
            gap: 16px;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            margin-bottom: 12px;
        }

        label {
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-weight: 500;
            font-size: 14px;
            color: var(--muted);
        }

        input, select {
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid var(--border);
            font-size: 15px;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-soft);
        }

        button.primary {
            padding: 12px 18px;
            background: var(--accent);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s ease, box-shadow 0.2s ease;
        }

        button.primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.25);
        }

        button.secondary {
            padding: 12px 18px;
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: 12px;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
        }

        .section {
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .section h3 {
            margin: 0 0 12px;
            font-size: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .section h3 span {
            background: var(--accent-soft);
            color: var(--accent);
            border-radius: 8px;
            padding: 2px 12px;
            font-size: 13px;
            letter-spacing: 0.06em;
        }

        .question {
            border-radius: 12px;
            border: 1px solid var(--border);
            padding: 16px;
            margin-bottom: 14px;
            transition: border-color 0.2s ease;
        }

        .question h4 {
            margin: 0 0 8px;
            font-size: 16px;
            font-weight: 600;
        }

        .meta {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 12px;
            font-size: 13px;
            color: var(--muted);
        }

        .options {
            display: grid;
            gap: 10px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .option {
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 12px;
            cursor: pointer;
            transition: border-color 0.2s ease, background 0.2s ease;
            width: 100%;
        }

        .option input {
            margin: 0;
            cursor: pointer;
        }

        .option:hover {
            border-color: var(--accent);
            background: rgba(37, 99, 235, 0.05);
        }

        #statusBar {
            font-size: 14px;
            color: var(--muted);
            margin-top: 12px;
        }

        #statusBar.error {
            color: var(--error);
        }

        #statusBar.success {
            color: var(--success);
        }

        .report-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 18px;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: var(--accent-soft);
            color: var(--accent);
            border-radius: 999px;
            font-size: 13px;
            font-weight: 500;
        }

        .history {
            border-top: 1px solid var(--border);
            padding-top: 16px;
            margin-top: 16px;
        }

        .history-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px dashed var(--border);
            font-size: 14px;
        }

        .history-item:last-child {
            border-bottom: none;
        }

        .hidden {
            display: none;
        }

        canvas {
            max-width: 100%;
        }

        @media (max-width: 640px) {
            header h1 {
                font-size: 24px;
            }

            .card {
                padding: 20px;
            }

            .section {
                padding: 16px;
            }

            .options {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="page">
        <header>
            <h1>CivicBriefs Planner Lab</h1>
            <p>Launch an adaptive sectional mock, track accuracy in real time, and review personalised feedback with a study plan tailored to your latest attempt.</p>
        </header>

        <section class="card">
            <div class="controls">
                <label>
                    User identifier (email, phone or Mongo _id)
                    <input id="userId" placeholder="Optional" autocomplete="off" />
                </label>
                <label>
                    Questions per section
                    <select id="qCount">
                        <option value="10">10</option>
                        <option value="15" selected>15</option>
                        <option value="20">20</option>
                    </select>
                </label>
            </div>
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <button class="primary" id="startBtn">Start Fresh Test</button>
                <button class="secondary" id="resetBtn">Clear Answers</button>
            </div>
            <div id="statusBar"></div>
        </section>

        <section class="card" id="testCard" style="display:none;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <h2 style="margin:0; font-size:22px;">Mock Interface</h2>
                <div class="pill" id="progressPill">0% completed</div>
            </div>
            <div id="testArea"></div>
            <div style="display:flex; justify-content:flex-end; gap:12px; margin-top:20px;">
                <button class="secondary" id="reviewBtn">Review unanswered</button>
                <button class="primary" id="submitBtn">Submit Responses</button>
            </div>
        </section>

        <section class="card hidden" id="reportCard">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <h2 style="margin:0; font-size:22px;">Performance Insights</h2>
                <div class="pill" id="overallScore"></div>
            </div>
            <div class="report-grid" id="sectionGrid"></div>
            <div style="margin-top:24px;">
                <canvas id="progressChart" height="200"></canvas>
            </div>
            <div class="history" id="historyBlock"></div>
        </section>

        <section class="card hidden" id="planCard">
            <h2 style="margin:0 0 16px; font-size:22px;">Recommended Study Plan</h2>
            <div id="planContent" style="display:grid; gap:16px;"></div>
        </section>

        <section class="card hidden" id="jsonCard">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h2 style="margin:0; font-size:22px;">Raw Test Report (JSON)</h2>
                <button class="secondary" id="downloadJsonBtn" style="white-space:nowrap;">Download JSON</button>
            </div>
            <pre id="jsonContent" style="max-height:320px; overflow:auto; background:#0f172a; color:#e2e8f0; padding:16px; border-radius:12px; font-size:13px; line-height:1.45;"></pre>
        </section>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js" integrity="sha384-NrKB+u6Ts6AtkIhwPixiKTzgSKNblyhlk0Sohlgar9UHUBzai/sgnNNWWd291xqt" crossorigin="anonymous"></script>
    <script>
    (function () {
        const state = {
            test: null,
            answers: {},
            chart: null,
        };

        const els = {
            userId: document.getElementById('userId'),
            qCount: document.getElementById('qCount'),
            startBtn: document.getElementById('startBtn'),
            resetBtn: document.getElementById('resetBtn'),
            submitBtn: document.getElementById('submitBtn'),
            reviewBtn: document.getElementById('reviewBtn'),
            statusBar: document.getElementById('statusBar'),
            testCard: document.getElementById('testCard'),
            testArea: document.getElementById('testArea'),
            progressPill: document.getElementById('progressPill'),
            reportCard: document.getElementById('reportCard'),
            overallScore: document.getElementById('overallScore'),
            sectionGrid: document.getElementById('sectionGrid'),
            planCard: document.getElementById('planCard'),
            planContent: document.getElementById('planContent'),
            historyBlock: document.getElementById('historyBlock'),
            chartCanvas: document.getElementById('progressChart'),
            jsonCard: document.getElementById('jsonCard'),
            jsonContent: document.getElementById('jsonContent'),
            downloadJsonBtn: document.getElementById('downloadJsonBtn'),
        };

        function setStatus(message, tone = '') {
            els.statusBar.textContent = message;
            els.statusBar.className = tone ? tone : '';
        }

        function calcCompletion() {
            if (!state.test) {
                return 0;
            }
            const total = Object.values(state.test.sections).reduce((sum, section) => sum + section.questions.length, 0);
            const answered = Object.keys(state.answers).length;
            return Math.round((answered / total) * 100) || 0;
        }

        function updateProgress() {
            const pct = calcCompletion();
            els.progressPill.textContent = pct + '% completed';
        }

        function clearUI() {
            state.test = null;
            state.answers = {};
            els.testArea.innerHTML = '';
            els.reportCard.classList.add('hidden');
            els.planCard.classList.add('hidden');
            els.historyBlock.innerHTML = '';
            els.overallScore.textContent = '';
            els.jsonCard.classList.add('hidden');
            els.jsonContent.textContent = '';
            if (state.chart) {
                state.chart.destroy();
                state.chart = null;
            }
        }

        function renderTest() {
            if (!state.test) {
                els.testCard.style.display = 'none';
                return;
            }

            els.testCard.style.display = 'block';
            els.testArea.innerHTML = '';

            Object.values(state.test.sections).forEach((section) => {
                const wrapper = document.createElement('section');
                wrapper.className = 'section';

                const heading = document.createElement('h3');
                heading.innerHTML = section.label + ' <span>' + section.questions.length + ' Qs</span>';
                wrapper.appendChild(heading);

                section.questions.forEach((question, idx) => {
                    const block = document.createElement('article');
                    block.className = 'question';
                    block.dataset.questionId = question.question_id;

                    const title = document.createElement('h4');
                    title.textContent = (idx + 1) + '. ' + question.question;
                    block.appendChild(title);

                    const meta = document.createElement('div');
                    meta.className = 'meta';
                    meta.innerHTML = '<span>Topic: ' + (question.topic || 'NA') + '</span><span>Difficulty: ' + (question.difficulty || 'NA') + '</span>';
                    block.appendChild(meta);

                    const opts = document.createElement('div');
                    opts.className = 'options';

                    ['A', 'B', 'C', 'D'].forEach((key) => {
                        if (!question.options || !question.options[key]) {
                            return;
                        }
                        const option = document.createElement('label');
                        option.className = 'option';

                        const input = document.createElement('input');
                        input.type = 'radio';
                        input.name = question.question_id;
                        input.value = key;
                        input.checked = state.answers[question.question_id] === key;
                        input.addEventListener('change', () => {
                            state.answers[question.question_id] = key;
                            updateProgress();
                        });

                        const span = document.createElement('span');
                        span.textContent = key + '. ' + question.options[key];

                        option.appendChild(input);
                        option.appendChild(span);
                        opts.appendChild(option);
                    });

                    block.appendChild(opts);
                    els.testArea.appendChild(block);
                });

                els.testArea.appendChild(wrapper);
            });

            updateProgress();
        }

        async function startTest() {
            clearUI();
            setStatus('Loading questions...');
            const qCount = parseInt(els.qCount.value, 10) || 15;
            try {
                const res = await fetch('/agents/planner/test?questions_per_section=' + qCount);
                if (!res.ok) {
                    throw new Error('Unable to generate test');
                }
                const data = await res.json();
                state.test = data.test;
                renderTest();
                setStatus('Test ready. Best of luck!', 'success');
            } catch (err) {
                console.error(err);
                setStatus(err.message || 'Failed to load test', 'error');
                els.testCard.style.display = 'none';
            }
        }

        function reviewUnanswered() {
            if (!state.test) {
                return;
            }
            const cards = Array.from(els.testArea.querySelectorAll('.question'));
            let firstUnanswered = null;
            cards.forEach((card) => {
                const qid = card.dataset.questionId;
                if (!state.answers[qid]) {
                    card.style.borderColor = '#f97316';
                    if (!firstUnanswered) {
                        firstUnanswered = card;
                    }
                } else {
                    card.style.borderColor = 'var(--border)';
                }
            });
            if (firstUnanswered) {
                firstUnanswered.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }

        function renderHistory(history) {
            if (!history.available) {
                els.historyBlock.innerHTML = '<p style="margin:0; color: var(--muted);">No prior attempts found for this user.</p>';
                return;
            }

            const fragment = document.createDocumentFragment();
            const title = document.createElement('h3');
            title.style.margin = '0 0 12px';
            title.textContent = 'Recent attempts';
            fragment.appendChild(title);

            history.entries.forEach((entry) => {
                const row = document.createElement('div');
                row.className = 'history-item';

                const date = document.createElement('span');
                const formatted = new Date(entry.date).toLocaleString();
                date.textContent = formatted;

                const scores = document.createElement('span');
                const parts = Object.keys(entry.sections || {}).map((key) => key + ': ' + entry.sections[key] + '%');
                scores.textContent = parts.join(' | ');

                row.appendChild(date);
                row.appendChild(scores);
                fragment.appendChild(row);
            });

            els.historyBlock.innerHTML = '';
            els.historyBlock.appendChild(fragment);
        }

        function renderSections(sectionReport) {
            els.sectionGrid.innerHTML = '';
            Object.values(sectionReport).forEach((section) => {
                const block = document.createElement('div');
                block.style.border = '1px solid var(--border)';
                block.style.borderRadius = '12px';
                block.style.padding = '16px';
                block.innerHTML = '<h4 style="margin:0 0 8px; font-size:18px;">' + section.label + '</h4>' +
                    '<p style="margin:0 0 6px; color: var(--muted);">Accuracy: <strong>' + section.accuracy + '%</strong></p>' +
                    '<p style="margin:0; color: var(--muted);">Correct ' + section.correct + ' / ' + section.total + '</p>';

                if (section.incorrect_questions && section.incorrect_questions.length) {
                    const review = document.createElement('details');
                    const summary = document.createElement('summary');
                    summary.textContent = 'Review incorrect questions (' + section.incorrect_questions.length + ')';
                    review.appendChild(summary);

                    section.incorrect_questions.forEach((item) => {
                        const para = document.createElement('p');
                        para.style.margin = '6px 0';
                        para.style.fontSize = '13px';
                        para.textContent = item.question;
                        review.appendChild(para);
                    });
                    block.appendChild(review);
                }

                els.sectionGrid.appendChild(block);
            });
        }

        function renderChart(sectionReport) {
            const labels = [];
            const scores = [];
            Object.values(sectionReport).forEach((section) => {
                labels.push(section.label);
                scores.push(section.accuracy);
            });

            if (state.chart) {
                state.chart.destroy();
            }

            state.chart = new Chart(els.chartCanvas, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Accuracy %',
                        data: scores,
                        borderRadius: 8,
                        backgroundColor: labels.map((label) => {
                            if (label === 'Polity' || label === 'Economy') {
                                return 'rgba(37, 99, 235, 0.6)';
                            }
                            return 'rgba(59, 130, 246, 0.45)';
                        }),
                    }],
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                        },
                    },
                    plugins: {
                        legend: {
                            display: false,
                        },
                    },
                },
            });
        }

        function renderPlan(plan, weeklySchedule) {
            els.planContent.innerHTML = '';

            const classification = document.createElement('div');
            classification.style.border = '1px solid var(--border)';
            classification.style.borderRadius = '12px';
            classification.style.padding = '16px';
            classification.innerHTML = '<h3 style="margin:0 0 8px; font-size:18px;">Classification</h3>';
            const list = document.createElement('ul');
            list.style.paddingLeft = '18px';
            Object.entries(plan.classification || {}).forEach(([subject, tag]) => {
                const li = document.createElement('li');
                li.textContent = subject + ': ' + tag;
                list.appendChild(li);
            });
            classification.appendChild(list);
            els.planContent.appendChild(classification);

            const sevenDay = document.createElement('div');
            sevenDay.style.border = '1px solid var(--border)';
            sevenDay.style.borderRadius = '12px';
            sevenDay.style.padding = '16px';
            sevenDay.innerHTML = '<h3 style="margin:0 0 8px; font-size:18px;">7 Day Focus</h3>';
            const sevenList = document.createElement('ul');
            sevenList.style.paddingLeft = '18px';
            (plan['7_day_plan'] || []).forEach((item) => {
                const li = document.createElement('li');
                li.textContent = item.day + ': ' + item.plan;
                sevenList.appendChild(li);
            });
            sevenDay.appendChild(sevenList);
            els.planContent.appendChild(sevenDay);

            const month = document.createElement('div');
            month.style.border = '1px solid var(--border)';
            month.style.borderRadius = '12px';
            month.style.padding = '16px';
            month.innerHTML = '<h3 style="margin:0 0 8px; font-size:18px;">30 Day Roadmap</h3>';
            const monthList = document.createElement('ul');
            monthList.style.paddingLeft = '18px';
            Object.entries(plan['30_day_plan'] || {}).forEach(([week, planText]) => {
                const li = document.createElement('li');
                li.textContent = week + ': ' + planText;
                monthList.appendChild(li);
            });
            month.appendChild(monthList);
            els.planContent.appendChild(month);

            const summary = document.createElement('div');
            summary.style.border = '1px solid var(--border)';
            summary.style.borderRadius = '12px';
            summary.style.padding = '16px';
            summary.innerHTML = '<h3 style="margin:0 0 8px; font-size:18px;">Daily Routine & PYQ Strategy</h3>' +
                '<p style="margin:0 0 6px;">Daily Plan: MCQs ' + (plan.daily_plan ? plan.daily_plan.mcq_per_day : '-') + ', revision ' + (plan.daily_plan ? plan.daily_plan.revision_minutes : '-') + ' minutes.</p>' +
                '<p style="margin:0;">Strategy: ' + (plan.pyq_strategy || 'Focus on latest PYQs') + '</p>';
            els.planContent.appendChild(summary);

            if (weeklySchedule && (weeklySchedule.schedule_text || weeklySchedule.summary)) {
                const schedule = document.createElement('div');
                schedule.style.border = '1px solid var(--border)';
                schedule.style.borderRadius = '12px';
                schedule.style.padding = '16px';

                const title = document.createElement('h3');
                title.style.margin = '0 0 8px';
                title.style.fontSize = '18px';
                title.textContent = 'LLM Weekly Schedule';
                schedule.appendChild(title);

                if (weeklySchedule.summary) {
                    const summaryLine = document.createElement('p');
                    summaryLine.style.margin = '0 0 10px';
                    summaryLine.style.color = 'var(--muted)';
                    summaryLine.textContent = weeklySchedule.summary;
                    schedule.appendChild(summaryLine);
                }

                const scheduleBody = document.createElement('div');
                scheduleBody.style.whiteSpace = 'pre-line';
                scheduleBody.style.fontFamily = "'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace";
                scheduleBody.style.fontSize = '14px';
                scheduleBody.style.lineHeight = '1.45';
                scheduleBody.textContent = weeklySchedule.schedule_text || 'Schedule not available.';
                schedule.appendChild(scheduleBody);

                if (weeklySchedule.allocations) {
                    const allocTitle = document.createElement('p');
                    allocTitle.style.margin = '12px 0 4px';
                    allocTitle.style.fontWeight = '600';
                    allocTitle.textContent = 'Weekly hour allocations:';
                    schedule.appendChild(allocTitle);

                    const allocList = document.createElement('ul');
                    allocList.style.margin = '0';
                    allocList.style.paddingLeft = '18px';
                    Object.entries(weeklySchedule.allocations).forEach(([subject, hours]) => {
                        const li = document.createElement('li');
                        li.textContent = subject + ': ' + hours + ' hrs';
                        allocList.appendChild(li);
                    });
                    schedule.appendChild(allocList);
                }

                els.planContent.appendChild(schedule);
            }
        }

        function handleReport(data) {
            els.reportCard.classList.remove('hidden');
            els.planCard.classList.remove('hidden');

            els.overallScore.textContent = 'Overall accuracy ' + data.test_summary.overall_accuracy + '%';
            renderSections(data.section_report);
            renderChart(data.section_report);
            renderHistory(data.history);
            renderPlan(data.study_plan, data.weekly_schedule);
            renderJson(data);
        }

        function renderJson(data) {
            if (!data) {
                els.jsonCard.classList.add('hidden');
                return;
            }

            const serialized = JSON.stringify(data, null, 2);
            els.jsonContent.textContent = serialized;
            els.jsonCard.classList.remove('hidden');

            if (els.downloadJsonBtn) {
                els.downloadJsonBtn.onclick = () => {
                    const blob = new Blob([serialized], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const anchor = document.createElement('a');
                    anchor.href = url;
                    anchor.download = 'planner-test-report.json';
                    document.body.appendChild(anchor);
                    anchor.click();
                    document.body.removeChild(anchor);
                    URL.revokeObjectURL(url);
                };
            }
        }

        async function submitTest() {
            if (!state.test) {
                return;
            }

            const totalQuestions = Object.values(state.test.sections).reduce((sum, section) => sum + section.questions.length, 0);
            const answered = Object.keys(state.answers).length;
            if (answered < totalQuestions) {
                const proceed = confirm('You still have unanswered questions. Submit anyway?');
                if (!proceed) {
                    return;
                }
            }

            setStatus('Submitting attempt...');

            const payload = {
                user_id: els.userId.value || null,
                answers: state.answers,
            };

            try {
                const res = await fetch('/agents/planner/test/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Submission failed');
                }

                handleReport(data.result);
                setStatus('Attempt recorded. Review the insights below.', 'success');
            } catch (err) {
                console.error(err);
                setStatus(err.message || 'Could not submit attempt', 'error');
            }
        }

        els.startBtn.addEventListener('click', startTest);
        els.resetBtn.addEventListener('click', () => {
            state.answers = {};
            if (state.test) {
                renderTest();
            }
            setStatus('Selections cleared.');
        });
        els.submitBtn.addEventListener('click', submitTest);
        els.reviewBtn.addEventListener('click', reviewUnanswered);
    })();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)
