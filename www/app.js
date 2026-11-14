'use strict';

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function readJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) { return fallback; }
}
function writeJSON(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {}
}
const pad2 = n => String(n).padStart(2, '0');

function localDateKey(d = new Date()) {
  return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
}
function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

let toastTimer = null;
function toast(msg) {
  const el = $('#toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

let PLACES = [];
let placesReady = null;

const FIELD_ALIASES = {
  name:     ['name', 'title', 'label', 'facility'],
  type:     ['type', 'category', 'amenity', 'kind', 'facility_type'],
  district: ['district', 'region', 'area', 'city', 'town'],
  address:  ['address', 'street', 'addr', 'location'],
  lat:      ['lat', 'latitude', 'y'],
  lng:      ['lng', 'lon', 'long', 'longitude', 'x'],
  open:     ['open', 'opens', 'opening', 'open_time', 'opening_time', 'opening_hours', 'hours'],
  close:    ['close', 'closes', 'closing', 'close_time', 'closing_time'],
  days:     ['days', 'weekdays', 'open_days'],
  phone:    ['phone', 'tel', 'telephone', 'contact', 'mobile']
};

function pick(obj, keys) {
  for (let i = 0; i < keys.length; i++) {
    const v = obj[keys[i]];
    if (v !== undefined && v !== null && v !== '') return v;
  }
  return undefined;
}

function normTime(v, fallback) {
  if (v === undefined || v === null || v === '') return fallback;
  const m = String(v).match(/(\d{1,2})[:.h]?(\d{2})?/);
  if (!m) return fallback;
  const h = parseInt(m[1], 10);
  let mm = m[2] ? parseInt(m[2], 10) : 0;
  if (!isFinite(h) || h > 23) return fallback;
  if (!isFinite(mm) || mm > 59) mm = 0;
  return pad2(h) + ':' + pad2(mm);
}

function inferType(raw) {
  const s = String(raw || '').toLowerCase();
  if (s.includes('pharm')) return 'Pharmacy';
  if (s.includes('health') && s.includes('cent')) return 'Health Centre';
  if (s.includes('hosp')) return 'Hospital';
  if (s.includes('clinic')) return 'Clinic';
  if (s.includes('doctor') || s.includes('dispensar')) return 'Clinic';
  return 'Facility';
}

function typeIcon(type) {
  switch (type) {
    case 'Hospital': return '🏥';
    case 'Clinic': return '🩺';
    case 'Pharmacy': return '💊';
    case 'Health Centre': return '🏪';
    default: return '📍';
  }
}

function normalisePlace(raw, i) {
  if (!raw || typeof raw !== 'object') return null;

  let src = raw;

  if (raw.geometry && Array.isArray(raw.geometry.coordinates)) {
    src = Object.assign({}, raw.properties || {}, {
      longitude: raw.geometry.coordinates[0],
      latitude: raw.geometry.coordinates[1]
    });
  }

  if (raw.tags && typeof raw.tags === 'object') {
    src = Object.assign({}, raw.tags, src);
    delete src.tags;
  }

  if (raw.center && typeof raw.center === 'object') {
    if (src.lat === undefined) src.lat = raw.center.lat;
    if (src.lon === undefined) src.lon = raw.center.lon;
  }

  const lat = Number(pick(src, FIELD_ALIASES.lat));
  const lng = Number(pick(src, FIELD_ALIASES.lng));
  if (!isFinite(lat) || !isFinite(lng)) return null;
  if (Math.abs(lat) > 90 || Math.abs(lng) > 180) return null;

  let openRaw = pick(src, FIELD_ALIASES.open);
  let closeRaw = pick(src, FIELD_ALIASES.close);

  if (closeRaw === undefined && typeof openRaw === 'string') {
    const m = openRaw.match(/(\d{1,2}[:.h]?\d{0,2})\s*[-–—to]+\s*(\d{1,2}[:.h]?\d{0,2})/i);
    if (m) { openRaw = m[1]; closeRaw = m[2]; }
  }

  const rawName = pick(src, FIELD_ALIASES.name);

  return {
    id: 'p' + i,
    name: String(rawName || 'Facility ' + (i + 1)).trim(),
    type: inferType(pick(src, FIELD_ALIASES.type)),
    district: String(pick(src, FIELD_ALIASES.district) || '—').trim(),
    address: String(pick(src, FIELD_ALIASES.address) || '—').trim(),
    lat: lat,
    lng: lng,
    open: normTime(openRaw, '08:00'),
    close: normTime(closeRaw, '16:00'),
    days: String(pick(src, FIELD_ALIASES.days) || 'Mon–Fri').trim(),
    phone: String(pick(src, FIELD_ALIASES.phone) || '—').trim()
  };
}

async function loadPlaces() {
  if (placesReady) return placesReady;

  placesReady = (async () => {
    try {
      const res = await fetch('map_data.json', { cache: 'no-cache' });
      if (!res.ok) throw new Error('HTTP ' + res.status);

      const data = await res.json();
      const arr = Array.isArray(data) ? data
        : data && Array.isArray(data.places) ? data.places
        : data && Array.isArray(data.results) ? data.results
        : data && Array.isArray(data.features) ? data.features
        : data && Array.isArray(data.facilities) ? data.facilities
        : [];

      const out = [];
      let skipped = 0;

      arr.forEach((raw, i) => {
        const p = normalisePlace(raw, i);
        if (p) out.push(p); else skipped++;
      });

      PLACES = out;
      console.log(
        'map_data.json: ' + out.length + ' facilities loaded' +
        (skipped ? ' (' + skipped + ' skipped — no coordinates)' : '')
      );
      document.dispatchEvent(new CustomEvent('dayweave:placesready'));
      return out;
    } catch (err) {
      console.error('Could not load map_data.json:', err);
      PLACES = [];
      return [];
    }
  })();

  return placesReady;
}

const TABS = ['health', 'meds', 'appts', 'map', 'routines', 'workout', 'coach'];

function switchTab(tab) {
  if (TABS.indexOf(tab) === -1) tab = 'health';

  $$('.tab-page').forEach(function (p) {
    p.classList.toggle('active', p.id === 'page-' + tab);
  });
  $$('.nav-btn').forEach(function (b) {
    b.classList.toggle('active', b.dataset.tab === tab);
  });
  document.body.dataset.tab = tab;
  window.scrollTo(0, 0);

  if (tab === 'map') {
    setTimeout(function () {
      document.dispatchEvent(new CustomEvent('dayweave:mapshow'));
    }, 40);
  }
  if (tab === 'appts') {
    const sel = $('#apptPlace');
    if (sel && sel.options.length === 0) fillPlaceSelect();
  }
}

const HEALTH_KEY = 'dayweave.health';
let healthChart = null;

function healthEntries() {
  const list = readJSON(HEALTH_KEY, []);
  return Array.isArray(list) ? list : [];
}
function todayHealth() {
  const k = localDateKey();
  return healthEntries().filter(function (e) { return e.date === k; })[0] || null;
}
function fillHealthInputs() {
  const e = todayHealth();
  if (!e) return;
  if (e.weight != null && $('#hWeight')) $('#hWeight').value = e.weight;
  if (e.water != null && $('#hWater')) $('#hWater').value = e.water;
  if (e.sleep != null && $('#hSleep')) $('#hSleep').value = e.sleep;
  if (e.steps != null && $('#hSteps')) $('#hSteps').value = e.steps;
}

function saveHealth() {
  const k = localDateKey();
  const num = function (id) {
    const el = $(id);
    if (!el) return null;
    const v = el.value.trim();
    if (v === '') return null;
    const n = Number(v);
    return isFinite(n) ? n : null;
  };

  const entry = {
    date: k,
    weight: num('#hWeight'),
    water: num('#hWater'),
    sleep: num('#hSleep'),
    steps: num('#hSteps')
  };

  if (entry.weight === null && entry.water === null && entry.sleep === null && entry.steps === null) {
    const s = $('#hStatus');
    if (s) s.textContent = 'Fill at least one field first.';
    return;
  }

  const list = healthEntries().filter(function (e) { return e.date !== k; });
  list.push(entry);
  list.sort(function (a, b) { return a.date < b.date ? -1 : 1; });
  writeJSON(HEALTH_KEY, list.slice(-90));

  const s = $('#hStatus');
  if (s) s.textContent = 'Saved for ' + k + '.';
  toast('Health logged');
  renderHealth();
}

function renderHealth() {
  const canvas = $('#healthChart');
  const empty = $('#chartEmpty');
  if (!canvas) return;

  const entries = healthEntries()
    .slice()
    .sort(function (a, b) { return a.date < b.date ? -1 : 1; })
    .slice(-7);

  if (!entries.length) {
    if (empty) empty.hidden = false;
    canvas.hidden = true;
    if (healthChart) { healthChart.destroy(); healthChart = null; }
    return;
  }
  if (empty) empty.hidden = true;
  canvas.hidden = false;
  if (typeof Chart === 'undefined') return;

  const labels = entries.map(function (e) { return e.date.slice(5); });
  const datasets = [
    {
      label: 'Weight (kg)',
      data: entries.map(function (e) { return e.weight; }),
      borderColor: '#38BDF8',
      backgroundColor: 'rgba(56,189,248,.15)',
      tension: 0.35, spanGaps: true, yAxisID: 'y', pointRadius: 3
    },
    {
      label: 'Sleep (h)',
      data: entries.map(function (e) { return e.sleep; }),
      borderColor: '#A78BFA',
      backgroundColor: 'rgba(167,139,250,.15)',
      tension: 0.35, spanGaps: true, yAxisID: 'y1', pointRadius: 3
    }
  ];

  if (healthChart) {
    healthChart.data.labels = labels;
    healthChart.data.datasets = datasets;
    healthChart.update();
    return;
  }

  healthChart = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: '#CBD5E1', boxWidth: 12, font: { size: 11 } } }
      },
      scales: {
        x: { ticks: { color: '#94A3B8' }, grid: { color: 'rgba(148,163,184,.12)' } },
        y: {
          position: 'left',
          ticks: { color: '#38BDF8' },
          grid: { color: 'rgba(148,163,184,.12)' }
        },
        y1: {
          position: 'right',
          ticks: { color: '#A78BFA' },
          grid: { drawOnChartArea: false }
        }
      }
    }
  });
}

let breathRunning = false;
let breathToken = 0;

function sleepMs(ms) {
  return new Promise(function (r) { setTimeout(r, ms); });
}

async function breathingLoop(token) {
  const label = $('#breathLabel');
  const circle = $('#breathCircle');
  if (!label || !circle) return;

  while (breathRunning && token === breathToken) {
    label.textContent = 'Breathe in';
    circle.style.transitionDuration = '4000ms';
    circle.style.transform = 'scale(1.35)';
    await sleepMs(4000);
    if (!breathRunning || token !== breathToken) break;

    label.textContent = 'Hold';
    await sleepMs(7000);
    if (!breathRunning || token !== breathToken) break;

    label.textContent = 'Breathe out';
    circle.style.transitionDuration = '8000ms';
    circle.style.transform = 'scale(1)';
    await sleepMs(8000);
  }
}

function toggleBreathing() {
  const btn = $('#breathBtn');
  const label = $('#breathLabel');
  const circle = $('#breathCircle');

  if (breathRunning) {
    breathRunning = false;
    breathToken++;
    if (btn) btn.textContent = 'Start breathing';
    if (label) label.textContent = 'Ready';
    if (circle) { circle.style.transitionDuration = '600ms'; circle.style.transform = 'scale(1)'; }
    return;
  }

  breathRunning = true;
  breathToken++;
  if (btn) btn.textContent = 'Stop';
  breathingLoop(breathToken);
}

const APPT_KEY = 'dayweave.appts';

function fillPlaceSelect() {
  const sel = $('#apptPlace');
  if (!sel) return;

  const current = sel.value;
  sel.innerHTML = '';

  if (!PLACES.length) {
    const o = document.createElement('option');
    o.value = '';
    o.textContent = 'No facilities loaded';
    sel.appendChild(o);
    return;
  }

  const groups = {};
  PLACES.forEach(function (p) {
    const t = p.type || 'Facility';
    if (!groups[t]) groups[t] = [];
    groups[t].push(p);
  });

  Object.keys(groups).sort().forEach(function (t) {
    const og = document.createElement('optgroup');
    og.label = t;
    groups[t].forEach(function (p) {
      const o = document.createElement('option');
      o.value = p.id;
      o.textContent = p.name + (p.district && p.district !== '—' ? ' — ' + p.district : '');
      og.appendChild(o);
    });
    sel.appendChild(og);
  });

  if (current) sel.value = current;
}

function saveAppointment(e) {
  if (e) e.preventDefault();

  const msg = $('#apptMsg');
  const placeId = $('#apptPlace') ? $('#apptPlace').value : '';
  const date = $('#apptDate') ? $('#apptDate').value : '';
  const time = $('#apptTime') ? $('#apptTime').value : '';

  const place = PLACES.filter(function (p) { return p.id === placeId; })[0];

  if (!place) { if (msg) msg.textContent = 'Choose a facility first.'; return; }
  if (!date || !time) { if (msg) msg.textContent = 'Pick a date and a time.'; return; }

  const list = readJSON(APPT_KEY, []);
  list.push({
    id: uid(),
    placeId: place.id,
    placeName: place.name,
    district: place.district,
    phone: place.phone,
    address: place.address,
    date: date,
    time: time,
    reason: $('#apptReason') ? $('#apptReason').value.trim() : '',
    created: Date.now()
  });
  list.sort(function (a, b) { return (a.date + a.time) < (b.date + b.time) ? -1 : 1; });
  writeJSON(APPT_KEY, list);

  if (msg) msg.textContent = 'Booked at ' + place.name + ' on ' + date + ' at ' + time + '.';
  if ($('#apptReason')) $('#apptReason').value = '';
  toast('Appointment booked');
  renderAppointments();
}

function renderAppointments() {
  const list = $('#apptList');
  const empty = $('#apptEmpty');
  if (!list) return;

  const appts = readJSON(APPT_KEY, []);
  list.innerHTML = '';

  appts.forEach(function (a) {
    const li = document.createElement('li');

    const left = document.createElement('div');
    const strong = document.createElement('strong');
    strong.textContent = a.placeName;
    const l1 = document.createElement('span');
    l1.className = 'muted small';
    l1.textContent = a.date + ' at ' + a.time + (a.reason ? ' · ' + a.reason : '');
    const l2 = document.createElement('span');
    l2.className = 'muted small';
    const bits = [];
    if (a.district && a.district !== '—') bits.push(a.district);
    if (a.phone && a.phone !== '—') bits.push(a.phone);
    l2.textContent = bits.join(' · ');
    left.appendChild(strong);
    left.appendChild(l1);
    left.appendChild(l2);

    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'btn ghost tiny';
    del.textContent = 'Cancel';
    del.addEventListener('click', function () {
      const next = readJSON(APPT_KEY, []).filter(function (x) { return x.id !== a.id; });
      writeJSON(APPT_KEY, next);
      renderAppointments();
      toast('Appointment cancelled');
    });

    li.appendChild(left);
    li.appendChild(del);
    list.appendChild(li);
  });

  if (empty) empty.hidden = appts.length > 0;
}

const ROUTINE_KEY = 'dayweave.routines';
let routineState = { date: localDateKey(), items: [] };

function loadRoutines() {
  const today = localDateKey();
  const saved = readJSON(ROUTINE_KEY, null);

  if (saved && Array.isArray(saved.items)) {
    routineState = { date: saved.date || today, items: saved.items };
    if (routineState.date !== today) {
      routineState.date = today;
      routineState.items.forEach(function (it) { it.done = false; });
      saveRoutines();
    }
    return;
  }

  routineState = {
    date: today,
    items: [
      { id: uid(), text: 'Drink 2L of water', done: false },
      { id: uid(), text: 'Walk 20 minutes', done: false },
      { id: uid(), text: 'Sleep before 23:00', done: false }
    ]
  };
  saveRoutines();
}

function saveRoutines() {
  writeJSON(ROUTINE_KEY, routineState);
}

function addRoutine(e) {
  if (e) e.preventDefault();
  const input = $('#routineInput');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;

  routineState.items.push({ id: uid(), text: text, done: false });
  saveRoutines();
  input.value = '';
  renderRoutines();
}

function renderRoutines() {
  const list = $('#routineList');
  const empty = $('#routineEmpty');
  const prog = $('#routineProgress');
  const bar = $('#routineBar');
  if (!list) return;

  list.innerHTML = '';

  routineState.items.forEach(function (it) {
    const li = document.createElement('li');

    const left = document.createElement('div');
    const lbl = document.createElement('label');
    lbl.className = 'routine-item';
    lbl.style.cssText = 'display:flex;gap:10px;align-items:center;margin:0;color:inherit;font-size:.94rem;';

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = !!it.done;
    cb.style.cssText = 'width:20px;height:20px;margin:0;accent-color:#22D3A7;flex:0 0 20px;';
    cb.addEventListener('change', function () {
      it.done = cb.checked;
      saveRoutines();
      renderRoutines();
    });

    const span = document.createElement('span');
    span.textContent = it.text;
    if (it.done) span.style.cssText = 'text-decoration:line-through;color:#64748B;';

    lbl.appendChild(cb);
    lbl.appendChild(span);
    left.appendChild(lbl);

    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'btn ghost tiny';
    del.textContent = '✕';
    del.addEventListener('click', function () {
      routineState.items = routineState.items.filter(function (x) { return x.id !== it.id; });
      saveRoutines();
      renderRoutines();
    });

    li.appendChild(left);
    li.appendChild(del);
    list.appendChild(li);
  });

  const total = routineState.items.length;
  const done = routineState.items.filter(function (x) { return x.done; }).length;

  if (prog) prog.textContent = total ? done + ' of ' + total + ' done today' : '';
  if (bar) bar.style.width = total ? Math.round((done / total) * 100) + '%' : '0%';
  if (empty) empty.hidden = total > 0;
}

function resetRoutines() {
  routineState.items.forEach(function (it) { it.done = false; });
  routineState.date = localDateKey();
  saveRoutines();
  renderRoutines();
  toast('Ticks reset');
}

const GROQ_KEY = 'dayweave.groqKey';
const CHAT_KEY = 'dayweave.chat';
const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const GROQ_MODEL = 'openai/gpt-oss-20b';

const SYSTEM_PROMPT =
  'You are DayWeave Coach, a friendly health and wellbeing assistant for people living in Mauritius. ' +
  'Rules: Reply in plain text only, never use markdown symbols like ** or #. ' +
  'Keep every answer under 120 words. ' +
  'Never diagnose a condition and never state a medicine dosage. ' +
  'Suggest food and habits that are easy to find in Mauritius: dholl, rice, fish, chicken, rougaille, local vegetables, seasonal fruit. ' +
  'If the user mentions chest pain, difficulty breathing, fainting, or a high fever in a child, tell them to go to the nearest hospital or call 114 immediately. ' +
  'Be encouraging and practical, and give at most three concrete steps.';

let chatHistory = [];
let coachBusy = false;

function localCoachReply(text) {
  const t = String(text || '').toLowerCase();

  if (t.indexOf('tired') !== -1 || t.indexOf('energy') !== -1 || t.indexOf('slump') !== -1) {
    return 'Try three things: 1) Eat a proper breakfast with protein — eggs or dholl with rice. 2) Drink water at 11:00 and again at 15:00; afternoon tiredness is often dehydration. 3) Stand up and walk for five minutes after lunch. If the tiredness lasts more than two weeks, see a doctor at your nearest Area Health Centre.';
  }
  if (t.indexOf('sleep') !== -1 || t.indexOf('insomnia') !== -1) {
    return 'Three steps for tonight: 1) No screen for 30 minutes before bed. 2) Keep the room dark and cool. 3) Do four rounds of the 4-7-8 breathing exercise in the Health tab. If you still cannot sleep after two weeks, book an appointment with a doctor.';
  }
  if (t.indexOf('eat') !== -1 || t.indexOf('meal') !== -1 || t.indexOf('food') !== -1 || t.indexOf('protein') !== -1) {
    return 'Cheap protein in Mauritius: dholl, eggs, tinned tuna, chicken thighs, and fish from the market. A simple plate: rice, dholl, rougaille tomato, and a green vegetable. Fill half the plate with vegetables, a quarter with protein, a quarter with rice.';
  }
  if (t.indexOf('exercise') !== -1 || t.indexOf('sport') !== -1 || t.indexOf('fit') !== -1) {
    return 'Start small and stay consistent: 1) Walk 20 minutes every day this week. 2) Add 10 squats using the Workout tab once that feels easy. 3) Increase by a little each week. Consistency beats intensity — three short sessions a week is a real result.';
  }
  if (t.indexOf('stress') !== -1 || t.indexOf('anxious') !== -1 || t.indexOf('anxiety') !== -1) {
    return 'Try this now: four rounds of 4-7-8 breathing in the Health tab, then a 10-minute walk outside. Write down the one thing worrying you most and one small action you can take today. If anxiety is affecting your sleep or work for more than a month, speak to a doctor.';
  }
  return 'I can help with sleep, energy, food, exercise and stress. Tell me a little more about what you are feeling and I will give you three practical steps. For anything urgent — chest pain, trouble breathing, fainting — go to the nearest hospital or call 114.';
}

function loadChat() {
  const saved = readJSON(CHAT_KEY, []);
  chatHistory = Array.isArray(saved) ? saved : [];
}

function persistChat() {
  writeJSON(CHAT_KEY, chatHistory.slice(-40));
}

function renderChat() {
  const log = $('#chatLog');
  if (!log) return;
  log.innerHTML = '';

  if (!chatHistory.length) {
    const hint = document.createElement('div');
    hint.className = 'msg assistant';
    hint.textContent = 'Hello. I am your DayWeave coach. Ask me about sleep, energy, food or exercise — or tap a suggestion below.';
    log.appendChild(hint);
    return;
  }

  chatHistory.forEach(function (m) {
    const div = document.createElement('div');
    div.className = 'msg ' + m.role + (m.pending ? ' pending' : '');
    div.textContent = m.content;
    log.appendChild(div);
  });

  log.scrollTop = log.scrollHeight;
}

function pushChat(role, content, pending) {
  chatHistory.push({ role: role, content: content, pending: !!pending });
  persistChat();
  renderChat();
}

function replacePending(text) {
  for (let i = chatHistory.length - 1; i >= 0; i--) {
    if (chatHistory[i].pending) {
      chatHistory[i].content = text;
      chatHistory[i].pending = false;
      break;
    }
  }
  persistChat();
  renderChat();
}

async function askCoach(text) {
  const question = String(text || '').trim();
  if (!question || coachBusy) return;

  const key = (localStorage.getItem(GROQ_KEY) || '').trim();
  coachBusy = true;
  pushChat('user', question);

  if (!key) {
    pushChat('assistant', localCoachReply(question) + '\n\n(Add your Groq API key above for live answers.)');
    coachBusy = false;
    return;
  }

  pushChat('assistant', 'Thinking…', true);

  try {
    const history = chatHistory
      .filter(function (m) { return !m.pending; })
      .slice(-10)
      .map(function (m) { return { role: m.role, content: m.content }; });

    const res = await fetch(GROQ_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key
      },
      body: JSON.stringify({
        model: GROQ_MODEL,
        messages: [{ role: 'system', content: SYSTEM_PROMPT }].concat(history),
        temperature: 0.6,
        max_tokens: 500
      })
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(res.status + ' ' + body.slice(0, 140));
    }

    const data = await res.json();
    let reply = 'No reply received.';
    if (data && data.choices && data.choices[0] && data.choices[0].message) {
      reply = String(data.choices[0].message.content || '').trim();
    }
    replacePending(reply || 'No reply received.');
  } catch (err) {
    replacePending(
      'Could not reach the coach right now (' + err.message + ').\n\nOffline tip: ' + localCoachReply(question)
    );
  } finally {
    coachBusy = false;
  }
}

function updateCoachKeyStatus() {
  const el = $('#coachKeyStatus');
  const key = (localStorage.getItem(GROQ_KEY) || '').trim();
  if (!el) return;
  el.textContent = key
    ? 'Key saved on this device only. Live answers enabled.'
    : 'No key yet. The coach will use offline tips.';
  const input = $('#coachKey');
  if (input && key) input.value = key;
}

function initCoach() {
  loadChat();
  renderChat();
  updateCoachKeyStatus();

  const save = $('#coachKeySave');
  if (save) save.addEventListener('click', function () {
    const input = $('#coachKey');
    const val = input ? input.value.trim() : '';
    if (!val) { toast('Paste a key first'); return; }
    localStorage.setItem(GROQ_KEY, val);
    updateCoachKeyStatus();
    toast('Groq key saved');
  });

  const clear = $('#coachKeyClear');
  if (clear) clear.addEventListener('click', function () {
    localStorage.removeItem(GROQ_KEY);
    const input = $('#coachKey');
    if (input) input.value = '';
    updateCoachKeyStatus();
    toast('Key cleared');
  });

  const form = $('#chatForm');
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    const input = $('#chatInput');
    const val = input ? input.value.trim() : '';
    if (!val) return;
    if (input) input.value = '';
    askCoach(val);
  });

  $$('.chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      askCoach(chip.dataset.prompt || chip.textContent);
    });
  });
}

(function initMeds() {
  const MEDS_KEY = 'dayweave.meds';
  const HIST_KEY = 'dayweave.meds.history';

  const alertedThisMinute = new Set();
  let audioCtx = null;
  let tickTimer = null;
  let notifAsked = false;

  function readMeds() {
    const m = readJSON(MEDS_KEY, []);
    return Array.isArray(m) ? m : [];
  }
  function readHist() {
    const h = readJSON(HIST_KEY, []);
    return Array.isArray(h) ? h : [];
  }

  function renderMeds() {
    const list = $('#medsList');
    const empty = $('#medsEmpty');
    if (!list) return;

    const meds = readMeds().slice().sort(function (a, b) {
      return a.time < b.time ? -1 : 1;
    });

    list.innerHTML = '';

    meds.forEach(function (m) {
      const li = document.createElement('li');

      const left = document.createElement('div');
      const strong = document.createElement('strong');
      strong.textContent = m.name;
      const meta = document.createElement('span');
      meta.className = 'muted small';
      meta.textContent = m.time + ' · ' + (m.repeat === 'once' ? 'One time only' : 'Every day');
      left.appendChild(strong);
      left.appendChild(meta);

      const del = document.createElement('button');
      del.type = 'button';
      del.className = 'btn ghost tiny';
      del.textContent = 'Delete';
      del.addEventListener('click', function () {
        writeJSON(MEDS_KEY, readMeds().filter(function (x) { return x.id !== m.id; }));
        renderMeds();
        toast('Reminder deleted');
      });

      li.appendChild(left);
      li.appendChild(del);
      list.appendChild(li);
    });

    if (empty) empty.hidden = meds.length > 0;
  }

  function renderHistory() {
    const list = $('#medsHistory');
    const empty = $('#medsHistoryEmpty');
    if (!list) return;

    const hist = readHist().slice(-20).reverse();
    list.innerHTML = '';

    hist.forEach(function (h) {
      const li = document.createElement('li');
      const left = document.createElement('div');
      const strong = document.createElement('strong');
      strong.textContent = h.name;
      const meta = document.createElement('span');
      meta.className = 'muted small';
      meta.textContent = h.date + ' at ' + h.time;
      left.appendChild(strong);
      left.appendChild(meta);
      li.appendChild(left);
      list.appendChild(li);
    });

    if (empty) empty.hidden = hist.length > 0;
  }

  function ensureAudio() {
    if (audioCtx) return audioCtx;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    try { audioCtx = new AC(); } catch (e) { return null; }
    return audioCtx;
  }

  function playSound() {
    const ctx = ensureAudio();
    if (!ctx) return;
    if (ctx.state === 'suspended') { try { ctx.resume(); } catch (e) {} }

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.3, now + 0.03);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.4);
  }

  function vibrate() {
    if (navigator.vibrate) { try { navigator.vibrate([220, 110, 220]); } catch (e) {} }
  }

  function notify(names) {
    if (!('Notification' in window)) return;
    if (Notification.permission !== 'granted') return;
    try {
      new Notification('Medicine time', { body: names.join(', '), icon: 'icon-192.png' });
    } catch (e) {}
  }

  function fireAlert(names) {
    const dlg = $('#medsDialog');
    const list = $('#medsDialogList');

    if (list) {
      list.innerHTML = '';
      names.forEach(function (n) {
        const li = document.createElement('li');
        li.textContent = n;
        list.appendChild(li);
      });
    }

    if (dlg && typeof dlg.showModal === 'function') {
      if (!dlg.open) { try { dlg.showModal(); } catch (e) {} }
    }

    playSound();
    vibrate();
    notify(names);
  }

  function check() {
    const now = new Date();
    const today = localDateKey(now);
    const hhmm = pad2(now.getHours()) + ':' + pad2(now.getMinutes());
    const minuteKey = today + '-' + hhmm;

    const stamp = $('#medsLastChecked');
    if (stamp) stamp.textContent = 'Last checked ' + hhmm;

    if (alertedThisMinute.has(minuteKey)) return;

    const meds = readMeds();
    if (!meds.length) return;

    const due = meds.filter(function (m) { return m.time === hhmm; });
    if (!due.length) return;

    alertedThisMinute.add(minuteKey);
    if (alertedThisMinute.size > 240) alertedThisMinute.clear();

    fireAlert(due.map(function (m) { return m.name; }));

    const hist = readHist();
    due.forEach(function (m) {
      hist.push({ name: m.name, date: today, time: hhmm, at: Date.now() });
    });
    writeJSON(HIST_KEY, hist.slice(-120));

    const remaining = meds.filter(function (m) {
      const isDue = due.some(function (d) { return d.id === m.id; });
      return !(isDue && m.repeat === 'once');
    });
    if (remaining.length !== meds.length) writeJSON(MEDS_KEY, remaining);

    renderMeds();
    renderHistory();
  }

  function startTicking() {
    if (tickTimer) return;
    check();
    tickTimer = setInterval(check, 10000);
  }

  const form = $('#medsForm');
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    const name = $('#medsName') ? $('#medsName').value.trim() : '';
    const time = $('#medsTime') ? $('#medsTime').value : '';
    const repeat = $('#medsRepeat') ? $('#medsRepeat').value : 'daily';
    const msg = $('#medsFormMsg');

    if (!name || !time) {
      if (msg) msg.textContent = 'Enter a name and a time.';
      return;
    }

    const meds = readMeds();
    meds.push({ id: uid(), name: name, time: time, repeat: repeat, created: Date.now() });
    writeJSON(MEDS_KEY, meds);

    if (msg) msg.textContent = name + ' set for ' + time + '.';
    if ($('#medsName')) $('#medsName').value = '';
    toast('Reminder saved');
    renderMeds();
    check();
  });

  const dismiss = $('#medsDismiss');
  if (dismiss) dismiss.addEventListener('click', function () {
    const dlg = $('#medsDialog');
    if (dlg && dlg.open) dlg.close();
  });

  document.addEventListener('pointerdown', function askOnce() {
    if (notifAsked) return;
    notifAsked = true;
    if ('Notification' in window && Notification.permission === 'default') {
      try { Notification.requestPermission(); } catch (e) {}
    }
    ensureAudio();
  }, { once: true });

  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) check();
  });

  renderMeds();
  renderHistory();
  startTicking();
})();

(function initMap() {
  const ARRIVAL_RADIUS_M = 100;
  const NEARBY_RADIUS_KM = 10;
  const MAURITIUS_CENTER = [-20.25, 57.55];
  const MAURITIUS_ZOOM = 10;

  let map = null;
  let userLatLng = null;
  let userMarker = null;
  let rangeCircle = null;
  let placeLayer = null;
  let scope = 'nearby';
  let autoTried = false;
  let locating = false;
  const markerById = {};

  function haversineKm(a, b) {
    const R = 6371;
    const toRad = function (d) { return (d * Math.PI) / 180; };
    const dLat = toRad(b[0] - a[0]);
    const dLng = toRad(b[1] - a[1]);
    const s =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(a[0])) * Math.cos(toRad(b[0])) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2);
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(s)));
  }

  function fmtKm(km) {
    if (km == null) return '';
    if (km < 1) return Math.round(km * 1000) + ' m';
    return km.toFixed(1) + ' km';
  }

  function setStatus(text) {
    const el = $('#mapStatus');
    if (el) el.textContent = text;
  }

  function ensureMap() {
    if (map) return map;
    if (typeof L === 'undefined') { setStatus('Map library failed to load. Check your connection.'); return null; }

    const el = $('#mapContainer');
    if (!el) return null;

    map = L.map(el, { zoomControl: true, attributionControl: true })
      .setView(MAURITIUS_CENTER, MAURITIUS_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    placeLayer = L.layerGroup().addTo(map);

    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(function () {
        if (map) map.invalidateSize();
      });
      ro.observe(el);
    }

    return map;
  }

  function popupHtml(p) {
    return '<strong>' + typeIcon(p.type) + ' ' + escapeHtml(p.name) + '</strong><br>' +
      escapeHtml(p.type) + (p.district && p.district !== '—' ? ' · ' + escapeHtml(p.district) : '') +
      '<br>Open ' + p.open + '–' + p.close + ' · ' + escapeHtml(p.days) +
      (p.phone && p.phone !== '—' ? '<br>' + escapeHtml(p.phone) : '');
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function computeRanked() {
    const origin = userLatLng || MAURITIUS_CENTER;
    const withDist = PLACES.map(function (p) {
      return { place: p, km: haversineKm(origin, [p.lat, p.lng]) };
    });

    if (scope === 'nearby' && userLatLng) {
      const filtered = withDist.filter(function (x) { return x.km <= NEARBY_RADIUS_KM; });
      filtered.sort(function (a, b) { return a.km - b.km; });
      return filtered;
    }

    withDist.sort(function (a, b) { return a.km - b.km; });
    return withDist;
  }

  function checkArrival() {
    const banner = $('#arrivalBanner');
    if (!banner) return;

    if (!userLatLng) { banner.hidden = true; return; }

    let best = null;
    PLACES.forEach(function (p) {
      const km = haversineKm(userLatLng, [p.lat, p.lng]);
      if (!best || km < best.km) best = { place: p, km: km };
    });

    if (best && best.km * 1000 <= ARRIVAL_RADIUS_M) {
      banner.hidden = false;
      banner.textContent = '✅ You have arrived at ' + best.place.name + ' (' + fmtKm(best.km) + ' away).';
    } else {
      banner.hidden = true;
    }
  }

  function render() {
    if (!map) return;

    const ranked = computeRanked();

    placeLayer.clearLayers();
    Object.keys(markerById).forEach(function (k) { delete markerById[k]; });

    ranked.forEach(function (item) {
      const p = item.place;
      const marker = L.marker([p.lat, p.lng], { title: p.name }).bindPopup(popupHtml(p));
      marker.addTo(placeLayer);
      markerById[p.id] = marker;
    });

    if (rangeCircle) { map.removeLayer(rangeCircle); rangeCircle = null; }
    if (scope === 'nearby' && userLatLng) {
      rangeCircle = L.circle(userLatLng, {
        radius: NEARBY_RADIUS_KM * 1000,
        color: '#22D3A7',
        weight: 1,
        fillColor: '#22D3A7',
        fillOpacity: 0.06
      }).addTo(map);
    }

    const list = $('#placeList');
    const empty = $('#placeEmpty');
    const title = $('#placeListTitle');

    if (title) {
      title.textContent = scope === 'nearby'
        ? 'Within ' + NEARBY_RADIUS_KM + ' km'
        : 'All facilities';
    }

    if (list) {
      list.innerHTML = '';
      const slice = ranked.slice(0, 40);

      slice.forEach(function (item) {
        const p = item.place;
        const li = document.createElement('li');
        li.className = 'place-row';

        const left = document.createElement('div');
        const strong = document.createElement('strong');
        strong.textContent = typeIcon(p.type) + ' ' + p.name;
        const l1 = document.createElement('span');
        l1.className = 'muted small';
        l1.textContent = p.type + (p.district && p.district !== '—' ? ' · ' + p.district : '');
        const l2 = document.createElement('span');
        l2.className = 'muted small';
        l2.textContent = 'Open ' + p.open + '–' + p.close + ' · ' + p.days;
        left.appendChild(strong);
        left.appendChild(l1);
        left.appendChild(l2);

        const dist = document.createElement('span');
        dist.className = 'place-dist';
        dist.textContent = fmtKm(item.km);

        li.appendChild(left);
        li.appendChild(dist);
        li.addEventListener('click', function () {
          const m = markerById[p.id];
          if (m) {
            map.setView([p.lat, p.lng], 16);
            m.openPopup();
          }
        });

        list.appendChild(li);
      });

      if (empty) {
        if (!ranked.length) {
          empty.hidden = false;
          empty.textContent = userLatLng
            ? 'No facility within ' + NEARBY_RADIUS_KM + ' km. Switch to Across Mauritius.'
            : 'Allow location to see the nearest facilities.';
        } else {
          empty.hidden = true;
        }
      }
    }

    checkArrival();
  }

  function onLocated(latlng) {
    userLatLng = latlng;

    if (map) {
      if (userMarker) userMarker.setLatLng(latlng);
      else {
        userMarker = L.circleMarker(latlng, {
          radius: 8, color: '#38BDF8', weight: 3,
          fillColor: '#38BDF8', fillOpacity: 0.9
        }).addTo(map);
      }
      map.setView(latlng, 13);
    }

    setStatus('Location found. Showing ' + (scope === 'nearby' ? 'facilities within 10 km' : 'all facilities') + '.');
    render();
  }

  function locate() {
    if (locating) return;
    if (!navigator.geolocation) { setStatus('This device does not support GPS.'); return; }

    locating = true;
    setStatus('Getting your location…');

    navigator.geolocation.getCurrentPosition(
      function (pos) {
        locating = false;
        onLocated([pos.coords.latitude, pos.coords.longitude]);
      },
      function (err) {
        locating = false;
        const reason = err && err.code === 1 ? 'Location permission denied.'
          : err && err.code === 2 ? 'Location unavailable.'
          : 'Could not get your location.';
        setStatus(reason + ' You can still browse across Mauritius.');
        render();
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 30000 }
    );
  }

  document.addEventListener('dayweave:mapshow', function () {
    ensureMap();
    if (map) {
      setTimeout(function () { map.invalidateSize(); }, 120);
    }
    if (!autoTried && !userLatLng) {
      autoTried = true;
      locate();
    }
    render();
  });

  document.addEventListener('dayweave:placesready', function () {
    if (map) render();
    else if (document.body.dataset.tab === 'map') ensureMap();
  });

  $$('.scope-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      scope = btn.dataset.scope || 'nearby';
      $$('.scope-btn').forEach(function (b) { b.classList.toggle('active', b === btn); });
      if (scope === 'nearby' && !userLatLng) {
        setStatus('Tap "Use my location" to filter to 10 km.');
      }
      render();
    });
  });

  const locateBtn = $('#mapLocateBtn');
  if (locateBtn) locateBtn.addEventListener('click', locate);

  if (navigator.geolocation && navigator.geolocation.watchPosition) {
    try {
      navigator.geolocation.watchPosition(
        function (pos) {
          if (!userLatLng) return;
          userLatLng = [pos.coords.latitude, pos.coords.longitude];
          if (userMarker) userMarker.setLatLng(userLatLng);
          checkArrival();
        },
        function () {},
        { enableHighAccuracy: true, maximumAge: 15000, timeout: 20000 }
      );
    } catch (e) {}
  }
})();

(function initWorkout() {
  const VISION_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs';
  const WASM_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm';
  const MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task';

  let landmarker = null;
  let stream = null;
  let running = false;
  let reps = 0;
  let sets = 0;
  let phase = 'up';
  let lastVideoTime = -1;

  const video = $('#wVideo');
  const canvas = $('#wCanvas');

  function setStatus(t) {
    const el = $('#wStatus');
    if (el) el.textContent = t;
  }
  function setState(t) {
    const el = $('#wState');
    if (el) el.textContent = t;
  }
  function paintCounters() {
    const r = $('#wReps');
    const s = $('#wSets');
    if (r) r.textContent = reps;
    if (s) s.textContent = sets;
  }

  function angle(a, b, c) {
    const abx = a.x - b.x, aby = a.y - b.y;
    const cbx = c.x - b.x, cby = c.y - b.y;
    const dot = abx * cbx + aby * cby;
    const mags = Math.hypot(abx, aby) * Math.hypot(cbx, cby);
    if (!mags) return 180;
    return Math.acos(Math.max(-1, Math.min(1, dot / mags))) * (180 / Math.PI);
  }

  async function ensureLandmarker() {
    if (landmarker) return landmarker;

    setStatus('Loading the pose model…');
    const vision = await import(VISION_URL);
    const fileset = await vision.FilesetResolver.forVisionTasks(WASM_URL);

    const options = {
      baseOptions: { modelAssetPath: MODEL_URL, delegate: 'GPU' },
      runningMode: 'VIDEO',
      numPoses: 1
    };

    try {
      landmarker = await vision.PoseLandmarker.createFromOptions(fileset, options);
    } catch (e) {
      options.baseOptions.delegate = 'CPU';
      landmarker = await vision.PoseLandmarker.createFromOptions(fileset, options);
    }
    return landmarker;
  }

  function draw(landmarks) {
    if (!canvas || !video) return;
    const w = video.videoWidth || 640;
    const h = video.videoHeight || 480;
    if (canvas.width !== w) canvas.width = w;
    if (canvas.height !== h) canvas.height = h;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, w, h);

    if (!landmarks) return;

    const links = [
      [23, 25], [25, 27], [24, 26], [26, 28],
      [23, 24], [11, 23], [12, 24], [11, 12]
    ];

    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 4;
    links.forEach(function (pair) {
      const a = landmarks[pair[0]];
      const b = landmarks[pair[1]];
      if (!a || !b) return;
      ctx.beginPath();
      ctx.moveTo(a.x * w, a.y * h);
      ctx.lineTo(b.x * w, b.y * h);
      ctx.stroke();
    });

    [23, 24, 25, 26, 27, 28].forEach(function (i) {
      const p = landmarks[i];
      if (!p) return;
      ctx.beginPath();
      ctx.arc(p.x * w, p.y * h, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#22D3A7';
      ctx.fill();
    });
  }

  function loop() {
    if (!running) return;

    if (video && landmarker && video.readyState >= 2) {
      const now = performance.now();
      if (video.currentTime !== lastVideoTime) {
        lastVideoTime = video.currentTime;
        try {
          const result = landmarker.detectForVideo(video, now);
          const lm = result && result.landmarks && result.landmarks[0];

          if (lm) {
            draw(lm);
            const leftKnee = angle(lm[23], lm[25], lm[27]);
            const rightKnee = angle(lm[24], lm[26], lm[28]);
            const avg = (leftKnee + rightKnee) / 2;

            if (avg < 100) {
              if (phase !== 'down') setState('down');
              phase = 'down';
            } else if (avg > 155) {
              if (phase === 'down') {
                reps++;
                if (reps % 10 === 0) sets++;
                paintCounters();
                setState('rep ' + reps);
              }
              phase = 'up';
            } else if (phase === 'up' && avg >= 105 && avg <= 145) {
              setState('go lower');
            }
          } else {
            draw(null);
            setState('step back');
          }
        } catch (e) {}
      }
    }

    requestAnimationFrame(loop);
  }

  async function startCamera() {
    if (running) return;

    try {
      setStatus('Starting camera…');
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false
      });

      video.srcObject = stream;
      await video.play();

      await ensureLandmarker();

      running = true;
      lastVideoTime = -1;
      setStatus('Camera on. Stand back so your whole body is visible, then squat.');
      requestAnimationFrame(loop);
    } catch (err) {
      running = false;
      setStatus('Could not start: ' + (err && err.message ? err.message : 'unknown error'));
      stopCamera();
    }
  }

  function stopCamera() {
    running = false;

    if (stream) {
      stream.getTracks().forEach(function (t) { t.stop(); });
      stream = null;
    }
    if (video) video.srcObject = null;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    setState('idle');
    setStatus('Camera stopped.');
  }

  function resetCounters() {
    reps = 0;
    sets = 0;
    phase = 'up';
    paintCounters();
    setState('idle');
    toast('Counters reset');
  }

  const start = $('#wStart');
  const stop = $('#wStop');
  const form = $('#wForm');

  if (start) start.addEventListener('click', startCamera);
  if (stop) stop.addEventListener('click', stopCamera);
  if (form) form.addEventListener('submit', function (e) { e.preventDefault(); resetCounters(); });

  paintCounters();
})();

(function initSteps() {
  const STEP_KEY = 'dayweave.steps';
  const STEP_THRESHOLD = 12;
  const GYRO_THRESHOLD = 5;
  const MIN_STEP_INTERVAL_MS = 300;

  let steps = 0;
  let lastStepAt = 0;
  let tracking = false;
  let unsaved = 0;

  const stepsEl = $('#stepLive');
  const statusEl = $('#stepStatus');
  const startBtn = $('#stepStart');
  const stopBtn = $('#stepStop');
  const useBtn = $('#stepUse');
  if (!stepsEl) return;

  function loadToday() {
    const saved = readJSON(STEP_KEY, null);
    if (saved && saved.date === localDateKey()) return Number(saved.count) || 0;
    return 0;
  }
  function saveToday() {
    writeJSON(STEP_KEY, { date: localDateKey(), count: steps });
    unsaved = 0;
  }

  function render() {
    stepsEl.textContent = String(steps);
    if (statusEl) statusEl.textContent = tracking ? 'Tracking — walk with the phone' : 'Not tracking';
    if (startBtn) startBtn.disabled = tracking;
    if (stopBtn) stopBtn.disabled = !tracking;
    if (useBtn) useBtn.disabled = steps === 0;
  }

  async function askPermission() {
    if (typeof DeviceMotionEvent !== 'undefined' &&
        typeof DeviceMotionEvent.requestPermission === 'function') {
      try {
        return (await DeviceMotionEvent.requestPermission()) === 'granted';
      } catch (e) { return false; }
    }
    return true;
  }

  function countStep(accel, rotation) {
    if (!accel || accel.x == null || accel.y == null || accel.z == null) return;

    const magnitude = Math.sqrt(
      accel.x * accel.x + accel.y * accel.y + accel.z * accel.z
    );

    const gyro = rotation
      ? Math.sqrt(
          Math.pow(rotation.alpha || 0, 2) +
          Math.pow(rotation.beta || 0, 2) +
          Math.pow(rotation.gamma || 0, 2)
        )
      : null;

    const moving = magnitude > STEP_THRESHOLD &&
                   (gyro === null || gyro > GYRO_THRESHOLD);

    const now = Date.now();
    if (moving && now - lastStepAt > MIN_STEP_INTERVAL_MS) {
      steps++;
      lastStepAt = now;
      unsaved++;
      if (unsaved >= 10) saveToday();
      render();
    }
  }

  function onMotion(e) {
    if (e.accelerationIncludingGravity) {
      countStep(e.accelerationIncludingGravity, e.rotationRate);
    }
  }

  async function start() {
    if (tracking) return;
    steps = loadToday();
    render();

    const ok = await askPermission();
    if (!ok) { toast('Motion permission denied'); return; }

    window.addEventListener('devicemotion', onMotion);
    tracking = true;
    render();
    toast('Step counter started');
  }

  function stop() {
    window.removeEventListener('devicemotion', onMotion);
    saveToday();
    tracking = false;
    render();
    toast('Step counter stopped');
  }

  if (startBtn) startBtn.addEventListener('click', start);
  if (stopBtn) stopBtn.addEventListener('click', stop);

  if (useBtn) useBtn.addEventListener('click', function () {
    const input = $('#hSteps');
    if (!input) return;
    input.value = steps;
    toast('Copied — now tap Save today');
  });

  window.addEventListener('pagehide', function () {
    if (tracking) saveToday();
  });

  steps = loadToday();
  render();
})();

async function boot() {
  $$('.nav-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { switchTab(btn.dataset.tab); });
  });

  const hSave = $('#hSave');
  if (hSave) hSave.addEventListener('click', saveHealth);

  const breathBtn = $('#breathBtn');
  if (breathBtn) breathBtn.addEventListener('click', toggleBreathing);

  const apptForm = $('#apptForm');
  if (apptForm) apptForm.addEventListener('submit', saveAppointment);

  const dateEl = $('#apptDate');
  if (dateEl && !dateEl.value) dateEl.value = localDateKey();

  const routineForm = $('#routineForm');
  if (routineForm) routineForm.addEventListener('submit', addRoutine);

  const routineReset = $('#routineReset');
  if (routineReset) routineReset.addEventListener('click', resetRoutines);

  initCoach();

  fillHealthInputs();
  renderHealth();
  loadRoutines();
  renderRoutines();
  renderAppointments();

  await loadPlaces();
  fillPlaceSelect();
  renderAppointments();

  document.addEventListener('dayweave:placesready', function () {
    fillPlaceSelect();
  });

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('./sw.js').catch(function (err) {
        console.warn('Service worker registration failed:', err);
      });
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}