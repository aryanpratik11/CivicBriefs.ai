// frontend/script.js - fixed, complete version

// --- DOM elements ---
const genBtn = document.getElementById('genBtn');
const downloadBtn = document.getElementById('downloadBtn');
const downloadResultBtn = document.getElementById('downloadResultBtn');
const testArea = document.getElementById('testArea');
const resultArea = document.getElementById('resultArea');

// result page elements (may not exist on test page)
const scorePercentEl = document.getElementById('scorePercent');
const accuracyListEl = document.getElementById('accuracyList');
const testIdEl = document.getElementById('testId');

let currentTest = { test_id: null, questions: [] };
let submitting = false;

// ----------------- Generate test -----------------
if (genBtn) {
  genBtn.addEventListener('click', async () => {
    const subject = document.getElementById('subject').value;
    const num = document.getElementById('num').value || 10;
    testArea.innerHTML = '<p>Loading questions…</p>';
    resultArea && (resultArea.style.display = 'none');

    try {
      const res = await fetch(`/generate-test?subject=${encodeURIComponent(subject)}&num=${encodeURIComponent(num)}`);
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      currentTest = data;
      renderTest(data);
      downloadBtn && (downloadBtn.style.display = 'inline-block');
      // store test id for later (optional)
      sessionStorage.setItem('currentTestId', data.test_id);
    } catch (err) {
      testArea.innerHTML = `<p style="color:red">Error generating test: ${err}</p>`;
      console.error("Generate test error:", err);
    }
  });
}

// ----------------- Render test -----------------
function renderTest(data) {
  testArea.innerHTML = '';
  currentTest = currentTest || {};
  currentTest.test_id = data.test_id;
  currentTest.questions = data.questions || [];

  const wrapper = document.createElement('div');
  const header = document.createElement('h2');
  header.textContent = `Test — ${data.test_id}`;
  wrapper.appendChild(header);

  data.questions.forEach((q, idx) => {
    const card = document.createElement('div');
    card.className = 'question-block';           // used by submitTest to find blocks
    card.setAttribute('data-qid', q.question_id); // store question id

    const qText = document.createElement('div');
    qText.innerHTML = `<strong>Q${idx+1}:</strong> ${q.question}`;
    card.appendChild(qText);

    const opts = document.createElement('div');
    opts.className = 'options';

    // build radio options
    for (const key of Object.keys(q.options || {})) {
      const label = document.createElement('label');
      label.className = 'option';
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = `q_${q.question_id}`;
      radio.value = key;
      label.appendChild(radio);
      label.appendChild(document.createTextNode(` ${key}. ${q.options[key]}`));
      opts.appendChild(label);
    }

    card.appendChild(opts);
    wrapper.appendChild(card);
  });

  // Submit button
  const submitBtn = document.createElement('button');
  submitBtn.textContent = 'Submit Test';
  submitBtn.className = 'primary';
  submitBtn.addEventListener('click', submitTest);
  wrapper.appendChild(submitBtn);

  testArea.appendChild(wrapper);
}

// ----------------- Submit test -----------------
async function submitTest() {
  if (submitting) return;
  submitting = true;

  try {
    // collect answers
    const blocks = document.querySelectorAll('.question-block');
    const responses = [];
    blocks.forEach(b => {
      const qid = b.getAttribute('data-qid');
      const sel = b.querySelector('input[type="radio"]:checked');
      const ans = sel ? sel.value : null;
      responses.push({
        question_id: qid,
        user_answer: ans || '',
        time_taken: 0
      });
    });

    const payload = {
      user_id: "U_45",                     // replace with real user id when available
      test_id: currentTest.test_id || sessionStorage.getItem('currentTestId') || ("T_" + Date.now()),
      responses: responses
    };

    // send to backend (single POST)
    const res = await fetch('/submit-test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Submit failed: ${res.status} ${text}`);
    }

    const data = await res.json();
    console.log("Submit response:", data);

    // store last test id and redirect to result page with test_id
    const tid = data.test_id || payload.test_id;
    sessionStorage.setItem('last_test_id', tid);
    window.location.href = `/result.html?test_id=${encodeURIComponent(tid)}`;

  } catch (err) {
    console.error("submitTest error:", err);
    alert("Submit failed: " + err.message);
  } finally {
    submitting = false;
  }
}

// ----------------- Load test result (result.html) -----------------
async function loadTestResult(testId) {
  // show test id
  if (testIdEl) testIdEl.innerText = `Test ID: ${testId}`;

  // 1) Fetch per-test summary (score)
  let scorePercent = 0;
  try {
    const sres = await fetch(`/get-test-summary/${encodeURIComponent(testId)}`);
    if (sres.ok) {
      const sd = await sres.json();
      scorePercent = sd.score_percent || 0;
    } else {
      console.warn('get-test-summary returned', sres.status);
    }
  } catch (e) {
    console.warn('get-test-summary error', e);
  }
  if (scorePercentEl) scorePercentEl.innerText = `${scorePercent}%`;

  // 2) Fetch per-test performance (subject-wise) if endpoint available
  let perf = {};
  try {
    const pres = await fetch(`/performance-by-test/${encodeURIComponent(testId)}`);
    if (pres.ok) {
      const pd = await pres.json();
      perf = pd.performance || {};
    } else {
      // fallback to cumulative/per-user performance
      const ures = await fetch(`/user-performance/U_45`);
      if (ures.ok) {
        const ud = await ures.json();
        perf = ud.performance || {};
      }
    }
  } catch (e) {
    console.warn('performance fetch error', e);
  }

  // render subject accuracy
  if (accuracyListEl) {
    accuracyListEl.innerHTML = '';
    for (const subject of Object.keys(perf)) {
      const acc = perf[subject];
      let level = 'strong';
      if (acc < 40) level = 'weak';
      else if (acc < 70) level = 'moderate';
      accuracyListEl.innerHTML += `
        <div class="accuracy-item">
          <strong>${subject} — ${acc}%</strong> <span class="badge ${level}">${level === 'weak' ? 'Weak' : level==='moderate' ? 'Average' : 'Strong'}</span>
          <div class="accuracy-bar"><div class="accuracy-fill" style="width:${acc}%"></div></div>
        </div>
      `;
    }
  }
}

// small helper used by old pages
async function loadLastResultForUser(userId) {
  const tid = sessionStorage.getItem('last_test_id');
  if (tid) {
    window.location.href = `/result.html?test_id=${encodeURIComponent(tid)}`;
  } else {
    // try to fetch last test from DB (optional improvement)
    console.log('No last_test_id in sessionStorage');
  }
}

// ----------------- Utility: PDF buttons -----------------
if (downloadBtn) {
  downloadBtn.addEventListener('click', () => {
    const element = document.querySelector('.container');
    html2pdf().from(element).save(`Test-${currentTest.test_id || 'unknown'}.pdf`);
  });
}
if (downloadResultBtn) {
  downloadResultBtn.addEventListener('click', () => {
    const element = document.querySelector('.container');
    html2pdf().from(element).save(`Result-${currentTest.test_id || 'unknown'}.pdf`);
  });
}

// ----------------- Auto-run on result page -----------------
(function autoInit() {
  // If result.html is open and has query param test_id, call loadTestResult
  try {
    const params = new URLSearchParams(window.location.search);
    const tid = params.get('test_id');
    if (tid && (typeof loadTestResult === 'function')) {
      loadTestResult(tid);
    }
  } catch(e) { /* ignore */ }
})();



// ----------------- Personalized Planner -----------------
const plannerBtn = document.getElementById("plannerBtn");
const plannerOutput = document.getElementById("plannerOutput");

if (plannerBtn) {
    plannerBtn.addEventListener("click", async () => {
        plannerOutput.innerHTML = "Generating planner...";
        plannerOutput.style.display = "block";

        const params = new URLSearchParams(window.location.search);
        const testId = params.get("test_id");

        // get accuracy of ONLY THIS TEST
        let resPerf = await fetch(`/performance-by-test/${testId}`);
        let perfData = await resPerf.json();
        let performance = perfData.performance || {};

        const res = await fetch("/generate-planner", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ performance })
        });

        const data = await res.json();
        const plan = data.plan;

        plannerOutput.innerHTML = `
            <h3>Your Personalized UPSC Study Planner</h3>

            <h4>Weak Subjects</h4>
            <ul>${plan.weak_subjects.map(s => `<li>${s}</li>`).join("")}</ul>

            <h4>Moderate Subjects</h4>
            <ul>${plan.moderate_subjects.map(s => `<li>${s}</li>`).join("")}</ul>

            <h4>Strong Subjects</h4>
            <ul>${plan.strong_subjects.map(s => `<li>${s}</li>`).join("")}</ul>

            <h4>7-Day Micro Plan</h4>
            <ul>${plan["7_day_plan"].map(i => `<li>${i}</li>`).join("")}</ul>

            <h4>30-Day Plan</h4>
            <ul>${plan["30_day_plan"].map(i => `<li>${i}</li>`).join("")}</ul>
        `;
    });
}
