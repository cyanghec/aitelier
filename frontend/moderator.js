// AItelier — Moderator Widget
// Self-contained: injects CSS + HTML, calls backend for AI-generated messages.
// Include on any page: <script src="moderator.js"></script>

(function () {
  'use strict';

  // ── CONFIG ──────────────────────────────────────────────────────────────────
  const MOD_PROF = 'Professor';          // Override per deployment
  const API = (window.AITELIER_API || 'http://localhost:8000').replace(/\/$/, '');

  // Fallback pre-scripted messages when API is unavailable
  const FALLBACK = {
    index:     { msg: "Welcome to AItelier. Before you begin, make sure your full team is present — every role matters for this canvas.", timer: null },
    canvas_1:  { msg: "Phase 1 — Inputs & Context. Map everything that feeds this initiative: data, people, systems, and the constraints that rarely get written down.", timer: 20 },
    canvas_2:  { msg: "Phase 2 — AI Capabilities. For each AI type you select, design its oversight chain. Who decides when the AI is wrong?", timer: 25 },
    canvas_3:  { msg: "Phase 3 — Decision & Oversight. Map your feedback loops before deployment. Define what 'working' looks like and who owns it.", timer: 20 },
    canvas_4:  { msg: "Phase 4 — Impact & Governance. Assign ownership while stakes feel abstract — it becomes much harder once the system is live.", timer: 15 },
    canvas_done:{ msg: "Excellent work. Your blueprint is being generated. Before you continue — what surprised you most about this session?", timer: null },
    blueprint: { msg: "Here is your AI Decision Blueprint. Review it together as a team — flag anything that doesn't match your shared understanding.", timer: 10 },
    survey:    { msg: "Almost done. Your individual reflections here are confidential — please answer honestly. This is where the real learning happens.", timer: null },
  };

  // ── CSS INJECTION ────────────────────────────────────────────────────────────
  const css = `
.mod-wrap{position:fixed;bottom:24px;left:24px;z-index:9000;display:flex;align-items:flex-end;gap:10px;pointer-events:none;}
.mod-avatar-btn{width:52px;height:52px;border-radius:50%;cursor:pointer;pointer-events:all;position:relative;flex-shrink:0;border:2px solid #C8922A60;box-shadow:0 4px 20px rgba(30,39,97,.35);transition:transform .2s;}
.mod-avatar-btn:hover{transform:scale(1.06);}
.mod-avatar-btn svg{display:block;width:100%;height:100%;border-radius:50%;}
.mod-badge{position:absolute;top:-3px;right:-3px;width:13px;height:13px;background:#C8922A;border-radius:50%;border:2px solid #f4f3f0;display:none;animation:modPulse 1.2s ease infinite;}
.mod-badge.on{display:block;}
@keyframes modPulse{0%,100%{transform:scale(1);opacity:1;}50%{transform:scale(1.3);opacity:.7;}}
.mod-panel{background:#16193d;border:1px solid rgba(200,146,42,.25);border-radius:14px;padding:14px 16px;width:264px;pointer-events:all;box-shadow:0 8px 32px rgba(0,0,0,.45);display:none;margin-bottom:4px;}
.mod-panel.on{display:block;animation:modFadeUp .25s ease both;}
@keyframes modFadeUp{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
.mod-phdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;}
.mod-pname{font-family:'Playfair Display',Georgia,serif;font-size:11px;font-weight:600;color:#C8922A;letter-spacing:.3px;}
.mod-prole{font-size:8px;color:rgba(255,255,255,.35);letter-spacing:.5px;text-transform:uppercase;margin-top:2px;}
.mod-x{width:18px;height:18px;cursor:pointer;color:rgba(255,255,255,.25);font-size:11px;display:flex;align-items:center;justify-content:center;border-radius:50%;transition:color .15s;line-height:1;}
.mod-x:hover{color:rgba(255,255,255,.7);}
.mod-cue-row{display:none;align-items:center;gap:6px;margin-bottom:8px;padding:5px 8px;background:rgba(200,146,42,.12);border-radius:6px;border:1px solid rgba(200,146,42,.2);}
.mod-cue-row.on{display:flex;}
.mod-cue-av{width:20px;height:20px;border-radius:4px;background:#C8922A;color:#1E2761;font-size:8px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.mod-cue-text{font-size:9px;color:#C8922A;font-weight:600;letter-spacing:.3px;}
.mod-msg-text{font-size:10px;color:rgba(255,255,255,.78);line-height:1.65;margin-bottom:10px;}
.mod-timer-row{display:none;align-items:center;gap:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,.07);}
.mod-timer-row.on{display:flex;}
.mod-timer-meta{display:flex;flex-direction:column;gap:1px;}
.mod-timer-lbl{font-size:8px;color:rgba(255,255,255,.3);text-transform:uppercase;letter-spacing:.5px;}
.mod-timer-count{font-family:'DM Mono',monospace,monospace;font-size:14px;color:#C8922A;font-weight:500;letter-spacing:1px;}
.mod-page-tag{display:inline-block;font-size:7px;text-transform:uppercase;letter-spacing:.6px;padding:2px 6px;border-radius:3px;background:rgba(255,255,255,.07);color:rgba(255,255,255,.3);margin-bottom:8px;}
`;
  const styleEl = document.createElement('style');
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  // ── HTML INJECTION ───────────────────────────────────────────────────────────
  const avatarSVG = `<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
    <circle cx="24" cy="24" r="24" fill="#1E2761"/>
    <rect x="20" y="35" width="8" height="6" rx="2" fill="#f2c18a"/>
    <path d="M6 48 Q6 38 24 38 Q42 38 42 48" fill="#2A3580"/>
    <path d="M19 38 L24 43 L29 38" fill="white"/>
    <path d="M22.5 41 L24 46 L25.5 41 L24 39.5Z" fill="#C8922A"/>
    <circle cx="24" cy="21" r="13" fill="#f2c18a"/>
    <path d="M11 19 Q11 7 24 7 Q37 7 37 19 L37 13 Q37 3 24 3 Q11 3 11 13Z" fill="#3d2015"/>
    <ellipse cx="11" cy="22" rx="2.5" ry="3" fill="#f2c18a"/>
    <ellipse cx="37" cy="22" rx="2.5" ry="3" fill="#f2c18a"/>
    <rect x="12" y="19" width="10" height="7" rx="2.5" fill="none" stroke="#C8922A" stroke-width="1.8"/>
    <rect x="26" y="19" width="10" height="7" rx="2.5" fill="none" stroke="#C8922A" stroke-width="1.8"/>
    <line x1="22" y1="22.5" x2="26" y2="22.5" stroke="#C8922A" stroke-width="1.5"/>
    <line x1="12" y1="22.5" x2="9" y2="22.5" stroke="#C8922A" stroke-width="1.5"/>
    <line x1="36" y1="22.5" x2="39" y2="22.5" stroke="#C8922A" stroke-width="1.5"/>
    <circle cx="17" cy="22.5" r="1.8" fill="#2d1a0e"/>
    <circle cx="31" cy="22.5" r="1.8" fill="#2d1a0e"/>
    <path d="M13 17.5 Q17 15.5 21 17.5" stroke="#3d2015" stroke-width="1.5" fill="none" stroke-linecap="round"/>
    <path d="M27 17.5 Q31 15.5 35 17.5" stroke="#3d2015" stroke-width="1.5" fill="none" stroke-linecap="round"/>
    <path d="M19 29 Q24 33 29 29" stroke="#c47a5a" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  </svg>`;

  const wrap = document.createElement('div');
  wrap.className = 'mod-wrap';
  wrap.id = 'modWrap';
  wrap.innerHTML = `
    <div class="mod-panel" id="modPanel">
      <div class="mod-phdr">
        <div>
          <div class="mod-pname" id="modProfName">${MOD_PROF}</div>
          <div class="mod-prole">Session Moderator</div>
        </div>
        <div class="mod-x" id="modX" title="Dismiss">✕</div>
      </div>
      <div class="mod-page-tag" id="modPageTag"></div>
      <div class="mod-cue-row" id="modCueRow">
        <div class="mod-cue-av" id="modCueAv"></div>
        <div class="mod-cue-text" id="modCueText"></div>
      </div>
      <div class="mod-msg-text" id="modMsgText"></div>
      <div class="mod-timer-row" id="modTimerRow">
        <svg width="30" height="30" viewBox="0 0 30 30" style="flex-shrink:0">
          <circle cx="15" cy="15" r="12" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="2.5"/>
          <circle id="modTimerArc" cx="15" cy="15" r="12" fill="none" stroke="#C8922A"
            stroke-width="2.5" stroke-dasharray="75.4" stroke-dashoffset="0"
            stroke-linecap="round" transform="rotate(-90 15 15)"/>
        </svg>
        <div class="mod-timer-meta">
          <div class="mod-timer-lbl">Discussion time</div>
          <div class="mod-timer-count" id="modTimerCount">—</div>
        </div>
      </div>
    </div>
    <div class="mod-avatar-btn" id="modAvatarBtn" title="${MOD_PROF} — Session Moderator">
      ${avatarSVG}
      <div class="mod-badge" id="modBadge"></div>
    </div>`;
  document.body.appendChild(wrap);

  document.getElementById('modX').addEventListener('click', modDismiss);
  document.getElementById('modAvatarBtn').addEventListener('click', modToggle);

  // ── STATE ────────────────────────────────────────────────────────────────────
  let _open = false;
  let _timerInterval = null, _timerTotal = 0, _timerLeft = 0;
  let _team = [];
  let _page = detectPage();
  let _sessionId = new URLSearchParams(window.location.search).get('session') || '';

  // ── PAGE DETECTION ───────────────────────────────────────────────────────────
  function detectPage() {
    const p = window.location.pathname.split('/').pop().replace('.html', '') || 'index';
    return p === '' ? 'index' : p;
  }

  // ── TEAM MEMBERS ─────────────────────────────────────────────────────────────
  function collectTeam() {
    _team = [];
    document.querySelectorAll('.nav-av.other').forEach(av => {
      const title = av.getAttribute('title') || '';
      const initials = av.textContent.trim();
      _team.push({ initials, name: title.split(' ')[0] || initials });
    });
  }

  // ── BACKEND API CALL ─────────────────────────────────────────────────────────
  async function fetchModMessage(trigger, context = {}) {
    try {
      const res = await fetch(`${API}/api/moderator/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: _sessionId,
          page: _page,
          trigger,
          context,
          team_members: _team,
        }),
      });
      if (!res.ok) throw new Error('api error');
      return await res.json(); // { message, cue_member, timer_minutes }
    } catch (_) {
      return null; // fall through to fallback
    }
  }

  // ── SHOW MESSAGE ─────────────────────────────────────────────────────────────
  function modRender(data, pageLabel) {
    if (!data || !data.message) return;
    document.getElementById('modMsgText').textContent = data.message;

    // Page tag
    const tag = document.getElementById('modPageTag');
    if (pageLabel) { tag.textContent = pageLabel; tag.style.display = 'inline-block'; }
    else tag.style.display = 'none';

    // Cue
    const cueRow = document.getElementById('modCueRow');
    if (data.cue_member) {
      document.getElementById('modCueAv').textContent = data.cue_member.initials || '?';
      document.getElementById('modCueText').textContent = (data.cue_member.name || '') + ' — your turn';
      cueRow.classList.add('on');
    } else {
      cueRow.classList.remove('on');
    }

    // Timer
    if (data.timer_minutes) modStartTimer(data.timer_minutes * 60);
    else document.getElementById('modTimerRow').classList.remove('on');

    document.getElementById('modPanel').classList.add('on');
    document.getElementById('modBadge').classList.add('on');
    _open = true;
  }

  async function modTrigger(trigger, context = {}, fallbackKey = null, pageLabel = null) {
    const data = await fetchModMessage(trigger, context);
    if (data) {
      modRender(data, pageLabel);
    } else if (fallbackKey && FALLBACK[fallbackKey]) {
      modRender({ message: FALLBACK[fallbackKey].msg, timer_minutes: FALLBACK[fallbackKey].timer }, pageLabel);
    }
  }

  function modDismiss() {
    document.getElementById('modPanel').classList.remove('on');
    document.getElementById('modBadge').classList.remove('on');
    _open = false;
  }

  function modToggle() {
    if (_open) { modDismiss(); }
    else if (document.getElementById('modMsgText').textContent) {
      document.getElementById('modPanel').classList.add('on');
      document.getElementById('modBadge').classList.remove('on');
      _open = true;
    }
  }

  // ── TIMER ────────────────────────────────────────────────────────────────────
  function modStartTimer(seconds) {
    if (_timerInterval) clearInterval(_timerInterval);
    _timerTotal = seconds; _timerLeft = seconds;
    document.getElementById('modTimerRow').classList.add('on');
    _tickTimer();
    _timerInterval = setInterval(() => {
      _timerLeft--;
      _tickTimer();
      if (_timerLeft <= 0) { clearInterval(_timerInterval); _timerInterval = null; }
    }, 1000);
  }

  function _tickTimer() {
    const m = Math.floor(_timerLeft / 60), s = _timerLeft % 60;
    document.getElementById('modTimerCount').textContent =
      String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    const arc = document.getElementById('modTimerArc');
    if (arc) arc.setAttribute('stroke-dashoffset', String(75.4 * (1 - _timerLeft / _timerTotal)));
  }

  // ── PAGE-SPECIFIC INIT ───────────────────────────────────────────────────────
  function initByPage() {
    const labels = { index: 'Session Start', canvas: 'Canvas', blueprint: 'Blueprint', survey: 'Survey' };
    const label = labels[_page] || _page;

    if (_page === 'index') {
      setTimeout(() => modTrigger('page_load', {}, 'index', label), 2000);
    } else if (_page === 'canvas') {
      setTimeout(() => modTrigger('page_load', { phase: 1 }, 'canvas_1', label), 2500);
    } else if (_page === 'blueprint') {
      setTimeout(() => modTrigger('page_load', {}, 'blueprint', label), 2000);
    } else if (_page === 'survey') {
      setTimeout(() => modTrigger('page_load', {}, 'survey', label), 1500);
    }
  }

  // ── PUBLIC API ───────────────────────────────────────────────────────────────
  // Called by canvas.html on phase change
  window.modOnPhaseChange = function (n) {
    const keys = { 1: 'canvas_1', 2: 'canvas_2', 3: 'canvas_3', 4: 'canvas_4' };
    modTrigger('phase_change', { phase: n }, keys[n] || 'canvas_1', 'Phase ' + n);
  };

  // Called by canvas.html on completion
  window.modOnComplete = function () {
    modTrigger('canvas_complete', {}, 'canvas_done', 'Canvas Done');
  };

  // Called externally to show a custom message with optional cue + timer
  window.modShow = function (msg, opts = {}) {
    modRender({ message: msg, cue_member: opts.cue || null, timer_minutes: opts.timer || null }, opts.label || null);
  };

  // ── INIT ─────────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    collectTeam();
    initByPage();
  });

})();
