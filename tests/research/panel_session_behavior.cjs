// Research debugging UI regression harness.
/** Execute the real embedded console script in a minimal browser boundary.
 * No production function is replaced: DOM, storage, timers and HTTP are fakes.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const KEY = 'lightagent.research.auth.v1';

function storage(initial = null) {
  const values = new Map(initial === null ? [] : [[KEY, initial]]);
  return {
    values, failRead: false, failWrite: false, failRemove: false,
    getItem(key) { if (this.failRead) throw Error('Storage is disabled'); return values.get(key) ?? null; },
    setItem(key, value) { if (this.failWrite) throw Error('Storage is full'); values.set(key, String(value)); },
    removeItem(key) { if (this.failRemove) throw Error('Storage is disabled'); values.delete(key); },
    clear() { values.clear(); },
  };
}
function response(data, status = 200, json = null) {
  return {ok: status >= 200 && status < 300, status, json: json || (async () => data)};
}
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return {promise, resolve, reject};
}
function snapshot(id = 'agent-1', goal = 'Verified research') {
  return {
    agent: {id, goal, status: 'waiting', desired: 'running', backend: {kind: 'fixture'},
      contract: {evaluator: 'evidence', max_cycles_per_day: 24}, active_version_id: 'version-1'},
    service: {healthy: true}, tasks: [], cycles: [], experiments: [], versions: [],
    candidates: [], candidate_retries: [], messages: [], attempts: [], chats: [], jobs: [],
    contract_proposals: [], contract_revisions: [],
  };
}
function defaults(request) {
  if (request.path === '/api/agents') return response([
    {id: 'agent-1', goal: 'First researcher'}, {id: 'agent-2', goal: 'Second researcher'},
  ]);
  if (/\/events\?/.test(request.path)) return response([]);
  if (/^\/api\/agents\/agent-[12]$/.test(request.path)) return response(snapshot(request.path.split('/').at(-1)));
  throw Error('Unexpected test HTTP request: ' + request.path);
}
async function settle() {
  // Flush fire-and-forget refreshes and their fetch/json promise continuations.
  for (let i = 0; i < 4; i++) await new Promise(resolve => setImmediate(resolve));
}
function browser({saved = storage(), handler = defaults, storageGetterThrows = false} = {}) {
  const byId = new Map(), nodes = [], listeners = new Map(), intervals = new Map(), timeouts = new Map();
  let intervalId = 0;
  class Element {
    constructor(tag = 'div') {
      this.tagName = tag.toUpperCase(); this.attrs = new Map(); this.children = [];
      this.dataset = {}; this.style = {}; this.value = ''; this.disabled = false;
      this.hidden = false; this.scrollTop = 0; this.scrollHeight = 100; this.clientHeight = 100;
      this.offsetParent = {}; this.className = ''; this._text = ''; this._id = '';
      this.classList = {
        toggle: (name, enabled) => {
          const names = new Set(this.className.split(/\s+/).filter(Boolean));
          if (enabled === undefined) enabled = !names.has(name);
          if (enabled) names.add(name); else names.delete(name);
          this.className = [...names].join(' '); return enabled;
        },
        contains: name => this.className.split(/\s+/).includes(name),
      };
      nodes.push(this);
    }
    set id(value) { this._id = value; byId.set(value, this); }
    get id() { return this._id; }
    set textContent(value) { this._text = String(value ?? ''); this.children = []; }
    get textContent() { return this._text + this.children.map(c => typeof c === 'string' ? c : c.textContent).join(''); }
    get options() { return this.children.filter(child => child.tagName === 'OPTION'); }
    append(...children) { this.children.push(...children); for (const child of children) if (typeof child !== 'string') child.parentNode = this; }
    replaceChildren(...children) { this.children = []; this._text = ''; this.append(...children); }
    replaceWith(node) {
      if (this.parentNode) {
        const index = this.parentNode.children.indexOf(this);
        this.parentNode.children[index] = node; node.parentNode = this.parentNode;
      }
      if (node.id) byId.set(node.id, node);
    }
    setAttribute(key, value) {
      this.attrs.set(key, String(value));
      if (key === 'id') this.id = value;
      if (key === 'class') this.className = value;
      if (key.startsWith('data-')) this.dataset[key.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = value;
    }
    getAttribute(key) { return this.attrs.get(key) ?? null; }
    removeAttribute(key) { this.attrs.delete(key); }
    focus() { document.activeElement = this; }
    showModal() { this.open = true; }
    close() { this.open = false; }
    querySelectorAll(selector) { return document.querySelectorAll(selector); }
    querySelector(selector) { return document.querySelector(selector); }
  }
  for (const match of html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*)>/gi)) {
    const node = new Element(match[1]);
    for (const attr of match[2].matchAll(/([\w-]+)="([^"]*)"/g)) node.setAttribute(attr[1], attr[2]);
    node.disabled = /(?:^|\s)disabled(?:\s|$|=)/.test(match[2]);
    node.hidden = /(?:^|\s)hidden(?:\s|$|=)/.test(match[2]);
  }
  const document = {
    body: nodes.find(n => n.tagName === 'BODY'), activeElement: null,
    getElementById(id) { assert.ok(byId.has(id), 'Missing real HTML id: ' + id); return byId.get(id); },
    createElement: tag => new Element(tag),
    querySelectorAll(selector) {
      if (selector.startsWith('.')) return nodes.filter(n => n.className.split(/\s+/).includes(selector.slice(1)));
      const attr = /^\[([^\]=]+)\]$/.exec(selector);
      if (attr) return nodes.filter(n => n.attrs.has(attr[1]));
      return [];
    },
    querySelector(selector) { return this.querySelectorAll(selector)[0] || new Element(); },
    addEventListener() {},
  };
  const requests = [];
  const state = {saved, requests, intervals, timeouts, handler};
  const sandbox = {
    document, console, AbortController, DOMException, URL, URLSearchParams,
    crypto: {randomUUID: () => 'fixture-request-id'},
    location: {origin: 'http://127.0.0.1:8000'},
    matchMedia: () => ({matches: false, addEventListener() {}}),
    addEventListener(type, callback) { const list = listeners.get(type) || []; list.push(callback); listeners.set(type, list); },
    setInterval(callback) { const id = ++intervalId; intervals.set(id, callback); return id; },
    clearInterval(id) { intervals.delete(id); },
    setTimeout(callback) { const id = ++intervalId; timeouts.set(id, callback); return id; },
    clearTimeout(id) { timeouts.delete(id); },
    async fetch(path, options) {
      const request = {path, ...options}; requests.push(request);
      // Deliberately ignore signal cancellation: stale network replies still
      // have to fail the production session-generation check before rendering.
      return state.handler(request);
    },
  };
  Object.defineProperty(sandbox, 'localStorage', {get() {
    if (storageGetterThrows) throw Error('Storage access denied'); return saved;
  }});
  sandbox.window = sandbox;
  const context = vm.createContext(sandbox);
  const run = code => vm.runInContext(code, context);
  Object.assign(state, {
    run, dom: id => document.getElementById(id),
    async tick() { for (const callback of [...intervals.values()]) callback(); await settle(); },
    async retryTimers() {
      const pending = [...timeouts.entries()];
      for (const [id, callback] of pending) { timeouts.delete(id); callback(); }
      await settle();
    },
    async storageEvent(event) {
      for (const callback of listeners.get('storage') || []) callback({storageArea: saved, ...event});
      await settle();
    },
  });
  vm.runInContext(script, context, {filename: 'real-panel.js'});
  return state;
}
function savedRecord(b) { const value = b.saved.values.get(KEY); return value ? JSON.parse(value) : null; }
async function login(b, token = 'valid-a', agent = 'agent-1') {
  await b.run(`login(${JSON.stringify(token)},${JSON.stringify(agent)})`); await settle();
  assert.equal(b.run('authToken'), token, 'Only the validated token becomes active');
}
function assertLoggedOut(b) {
  assert.equal(b.run('authToken'), ''); assert.equal(b.run('aid'), '');
  assert.equal(b.run('currentData'), null); assert.equal(b.intervals.size, 0);
  assert.equal(b.dom('token').value, '');
  assert.equal(b.dom('agents').disabled, true); assert.equal(b.dom('send').disabled, true);
}

const scenarios = {
  async history_search_paging_and_polling() {
    const experiment = (id, summary) => ({id, created_at: 1, published: true,
      report: {summary, hypothesis: 'A fixture'}, artifacts: []});
    const latest = experiment('newest', 'Latest experiment'), oldest = experiment('oldest', 'Rare old baseline');
    const b = browser({handler(r) {
      if (r.path === '/api/agents/agent-1') return response({...snapshot(), experiments: [latest],
        experiment_page: {items: [latest], next_cursor: 'older', total: 1005}});
      if (r.path.includes('/records?')) {
        const query = new URL(r.path, 'http://localhost').searchParams;
        assert.equal(query.get('kind'), 'experiment');
        if (query.get('query') === 'rare') return response({items: [oldest], next_cursor: null, total: 1});
        assert.equal(query.get('cursor'), 'older');
        return response({items: [oldest], next_cursor: null, total: 1005});
      }
      return defaults(r);
    }});
    await login(b);
    assert.ok(b.dom('historyStatus').textContent.includes('1 / 1005'));
    assert.equal(b.dom('historyMore').hidden, false);
    await b.run('loadExperiments()');
    assert.equal(b.run('experimentHistory.items.length'), 2);
    assert.ok(b.dom('experiments').textContent.includes('Rare old baseline'));
    await b.tick();
    assert.equal(b.run('experimentHistory.items.length'), 2, 'Polling must not replace loaded historical pages');
    b.dom('historyQuery').value = 'rare';
    await b.run('loadExperiments({reset:true})');
    assert.equal(b.run('experimentHistory.items[0].id'), 'oldest');
    assert.ok(b.dom('historyStatus').textContent.includes('1 / 1'));
    await b.tick();
    assert.equal(b.run('experimentHistory.query'), 'rare');
    assert.equal(b.dom('historyMore').hidden, true);
  },
  async history_stale_responses() {
    for (const change of ['select', 'logout', 'pause']) {
      const delayed = deferred();
      const b = browser({handler(r) {
        if (r.path === '/api/agents/agent-1') return response({...snapshot(),
          experiment_page: {items: [], next_cursor: 'older', total: 1005}});
        if (r.path.includes('/records?')) return delayed.promise;
        if (r.path.endsWith('/control')) return response({desired: 'paused'});
        return defaults(r);
      }});
      await login(b);
      const pending = b.run('loadExperiments()'); await settle();
      if (change === 'select') b.run("selectAgent('agent-2')");
      if (change === 'logout') b.run('logout()');
      if (change === 'pause') await b.run("action('control',{action:'pause'})");
      await settle();
      delayed.resolve(response({items:[{id:'late-history',report:{summary:'Must not appear'},artifacts:[]}],total:1005,next_cursor:null}));
      await pending; await settle();
      assert.ok(!b.dom('experiments').textContent.includes('Must not appear'), change + ' fences late history');
      if (change === 'logout') { assertLoggedOut(b); assert.equal(b.run('experimentHistory'), null); }
    }
  },
  async instruction_preview_and_explicit_archive() {
    let submitted;
    const b = browser({handler(r) {
      if (r.path === '/api/agents/agent-1') {
        const d = snapshot(); d.agent.status = 'paused'; d.agent.desired = 'paused'; return response(d);
      }
      if (r.path.endsWith('/instructions')) return response({fingerprint:'f'.repeat(64),
        replacement:'Keep chronological evaluation.',active_message_count:2,active_bytes:131073,context_budget:131072,source_message_ids:['one','two']});
      if (r.path.endsWith('/control')) { submitted = JSON.parse(r.body); return response({id:'revision'}); }
      return defaults(r);
    }});
    await login(b);
    assert.equal(b.dom('instructionArchive').disabled, true);
    await b.run('previewInstructions()');
    assert.ok(b.dom('instructionState').textContent.includes('131073'));
    assert.equal(b.dom('instructionReplacement').value, 'Keep chronological evaluation.');
    assert.equal(b.dom('instructionArchive').disabled, false);
    b.dom('instructionReplacement').value = 'Use only past observations.';
    b.dom('instructionRationale').value = 'Reviewed the two source messages.';
    b.dom('instructionForm').onsubmit({preventDefault(){}}); await settle();
    assert.equal(submitted.action, 'archive_instructions');
    assert.equal(submitted.expected_fingerprint, 'f'.repeat(64));
    assert.equal(submitted.replacement, 'Use only past observations.');
    assert.equal(b.run('instructionPreview'), null);
    assert.ok(b.dom('instructionState').textContent.includes('仍保持暂停'));
    assert.ok(!b.requests.some(r => r.body && JSON.parse(r.body).action === 'resume'));
    b.run('logout()'); await settle();
    assert.equal(b.dom('instructionReplacement').value, '');
    assert.equal(b.dom('instructionState').textContent, '');
  },
  async verified_persistence_and_reload() {
    const b = browser(); await settle();
    assert.equal(b.requests.length, 0, 'No token means no automatic API call');
    const validation = deferred();
    b.handler = r => r.path === '/api/agents' ? validation.promise : defaults(r);
    const pending = b.run("login('valid-a','agent-2')"); await settle();
    assert.equal(savedRecord(b), null, 'Never persist an unvalidated token');
    assert.equal(b.run('authToken'), '');
    assert.equal(b.requests.length, 1, 'Do not fetch research data before token validation');
    validation.resolve(defaults(b.requests[0])); await pending; await settle();
    assert.deepEqual(savedRecord(b), {token: 'valid-a', agentId: 'agent-2'});
    assert.equal(b.run('currentData.agent.id'), 'agent-2');
    b.run("selectAgent('agent-1')"); await settle();
    assert.equal(savedRecord(b).agentId, 'agent-1');
    const reload = browser({saved: b.saved}); await settle();
    assert.equal(reload.requests[0].path, '/api/agents', 'Reload must revalidate saved credentials');
    assert.ok(reload.requests.every(r => r.headers.Authorization === 'Bearer valid-a'));
    assert.equal(reload.run('aid'), 'agent-1'); assert.equal(reload.run('currentData.agent.id'), 'agent-1');
    assert.equal(reload.intervals.size, 1);
  },
  async selected_agent_removed() {
    const saved = storage(JSON.stringify({token: 'valid-a', agentId: 'deleted-agent'}));
    const b = browser({saved}); await settle();
    assert.equal(b.run('aid'), 'agent-1', 'A removed selection falls back to an existing researcher');
    assert.equal(savedRecord(b).agentId, 'agent-1');
    assert.ok(!b.requests.some(r => r.path.includes('deleted-agent')));
  },
  async unsubmitted_input_is_not_authority() {
    const b = browser(); await settle(); await login(b);
    const start = b.requests.length;
    b.dom('token').value = 'unsubmitted-invalid-token'; await b.tick();
    assert.ok(b.requests.length > start);
    assert.ok(b.requests.slice(start).every(r => r.headers.Authorization === 'Bearer valid-a'));
    assert.equal(savedRecord(b).token, 'valid-a');
    assert.equal(b.run('authToken'), 'valid-a');
  },
  async unauthorized_invalid_json_clears_session() {
    const b = browser(); await settle(); await login(b);
    b.handler = () => response(null, 401, async () => { throw SyntaxError('Not JSON'); });
    await b.run('refresh()'); await settle();
    assertLoggedOut(b); assert.equal(savedRecord(b), null);
    assert.match(b.dom('error').textContent, /令牌|登录|失效/);
    const count = b.requests.length; await b.tick();
    assert.equal(b.requests.length, count, 'An expired login stops polling');
  },
  async rejected_restore_clears_credentials() {
    const saved = storage(JSON.stringify({token: 'expired-token', agentId: 'agent-2'}));
    const b = browser({saved, handler: () => response({error: 'Expired'}, 401)}); await settle();
    assertLoggedOut(b); assert.equal(savedRecord(b), null);
    assert.equal(b.requests.length, 1, 'Reject before reading researcher details');
  },
  async restored_snapshot_unauthorized_is_not_resaved() {
    const saved = storage(JSON.stringify({token: 'expired-after-validation', agentId: 'agent-2'}));
    const b = browser({saved, handler: request => request.path === '/api/agents'
      ? defaults(request) : response({error: 'Revoked during restore'}, 401)});
    await settle();
    assert.equal(b.requests.length, 2, 'Agent list validates, then snapshot immediately expires the token');
    assertLoggedOut(b); assert.equal(savedRecord(b), null);
    await b.tick(); await b.retryTimers();
    assert.equal(savedRecord(b), null, 'Login completion and timers cannot re-save an expired session');
    assert.equal(b.requests.length, 2);
  },
  async logout_ignores_late_refresh() {
    const b = browser(); await settle(); await login(b);
    const pending = deferred(); b.handler = () => pending.promise;
    const task = b.run('refresh()'); await settle();
    const request = b.requests.at(-1);
    b.run('logout()');
    assertLoggedOut(b); assert.equal(savedRecord(b), null);
    assert.equal(request.signal.aborted, true, 'Logout cancels in-flight browser requests');
    pending.resolve(response(snapshot('agent-1', 'STALE PRIVATE RESULT'))); await task; await settle();
    assertLoggedOut(b); assert.equal(savedRecord(b), null);
    assert.ok(!b.dom('status').textContent.includes('STALE PRIVATE RESULT'));
    assert.ok(!b.dom('connectionLabel').textContent.includes('在线'));
  },
  async logout_ignores_late_login() {
    const pending = deferred(); const b = browser({handler: () => pending.promise}); await settle();
    const task = b.run("login('valid-a','agent-1')").catch(() => {}); await settle();
    b.run('logout()'); pending.resolve(response([{id: 'agent-1', goal: 'First researcher'}]));
    await task; await settle();
    assertLoggedOut(b); assert.equal(savedRecord(b), null);
    assert.equal(b.requests.length, 1, 'A cancelled validation cannot start a researcher refresh');
  },
  async logout_during_json_read() {
    const b = browser(); await settle(); await login(b);
    const body = deferred(); b.handler = () => response(null, 200, () => body.promise);
    const task = b.run('refresh()'); await settle();
    b.run('logout()'); body.resolve(snapshot('agent-1', 'STALE BODY RESULT'));
    await task; await settle(); assertLoggedOut(b);
    assert.ok(!b.dom('status').textContent.includes('STALE BODY RESULT'));
  },
  async older_unauthorized_cannot_clear_new_login() {
    const b = browser(); await settle(); await login(b);
    const late = deferred(); b.handler = () => late.promise;
    const old = b.run('refresh()'); await settle();
    b.handler = defaults; await login(b, 'valid-b', 'agent-2');
    late.resolve(response(null, 401, async () => { throw SyntaxError('Not JSON'); }));
    await old; await settle();
    assert.equal(b.run('authToken'), 'valid-b'); assert.equal(b.run('aid'), 'agent-2');
    assert.deepEqual(savedRecord(b), {token: 'valid-b', agentId: 'agent-2'});
    assert.equal(b.run('currentData.agent.id'), 'agent-2'); assert.equal(b.intervals.size, 1);
  },
  async cross_tab_logout_and_late_response() {
    const first = browser(); await settle(); await login(first, 'valid-a', 'agent-2');
    const second = browser({saved: first.saved}); await settle();
    const late = deferred(); second.handler = () => late.promise;
    const task = second.run('refresh()'); await settle();
    const oldValue = first.saved.values.get(KEY); first.run('logout()');
    await second.storageEvent({key: KEY, oldValue, newValue: null});
    assertLoggedOut(second);
    late.resolve(response(snapshot('agent-2', 'STALE TAB RESULT'))); await task; await settle();
    assertLoggedOut(second); assert.equal(savedRecord(second), null);
    assert.ok(!second.dom('status').textContent.includes('STALE TAB RESULT'));
  },
  async storage_clear_event_logs_out() {
    const b = browser(); await settle(); await login(b);
    b.saved.clear(); await b.storageEvent({key: null, oldValue: null, newValue: null});
    assertLoggedOut(b);
  },
  async temporary_failures_preserve_credentials() {
    for (const failure of [() => response({error: 'Unavailable'}, 503),
      () => response({error: 'Forbidden'}, 403), () => { throw TypeError('Network unavailable'); }]) {
      const saved = storage(JSON.stringify({token: 'valid-a', agentId: 'agent-2'}));
      const b = browser({saved, handler: failure}); await settle();
      assert.deepEqual(savedRecord(b), {token: 'valid-a', agentId: 'agent-2'}, 'Temporary restore failure keeps saved credentials');
      assert.equal(b.run('authToken'), '', 'A failed restore must not authenticate');
      b.handler = defaults; await b.run('restoreLogin()'); await settle();
      assert.equal(b.run('authToken'), 'valid-a'); assert.equal(b.run('aid'), 'agent-2');
      b.handler = failure; await b.run('refresh()'); await settle();
      assert.deepEqual(savedRecord(b), {token: 'valid-a', agentId: 'agent-2'});
      assert.equal(b.run('authToken'), 'valid-a', 'A temporary API failure does not expire validated credentials');
      b.handler = defaults; await b.tick();
      assert.equal(b.run('currentData.agent.id'), 'agent-2');
    }
  },
  async automatic_restore_retry_and_logout_cancellation() {
    const saved = storage(JSON.stringify({token: 'valid-a', agentId: 'agent-2'}));
    const b = browser({saved, handler: () => response({error: 'Unavailable'}, 503)}); await settle();
    assert.equal(b.timeouts.size, 1, 'A temporary failure schedules a restore retry');
    b.handler = defaults; await b.retryTimers();
    assert.equal(b.run('authToken'), 'valid-a'); assert.equal(b.run('aid'), 'agent-2');
    assert.equal(b.timeouts.size, 0); assert.equal(b.intervals.size, 1);
    const disconnected = browser({saved, handler: () => { throw TypeError('Offline'); }}); await settle();
    const lateTimer = [...disconnected.timeouts.values()][0];
    assert.ok(lateTimer); disconnected.run('logout()'); assertLoggedOut(disconnected);
    assert.equal(disconnected.timeouts.size, 0);
    const requestCount = disconnected.requests.length;
    lateTimer(); await settle();
    assert.equal(disconnected.requests.length, requestCount, 'Even an already queued timer cannot undo explicit logout');
    assert.equal(savedRecord(disconnected), null);
  },
  async rejected_new_token_preserves_validated_session() {
    const b = browser(); await settle(); await login(b);
    b.handler = request => request.headers.Authorization === 'Bearer invalid-candidate'
      ? response({error: 'Invalid'}, 401) : defaults(request);
    b.dom('token').value = 'invalid-candidate';
    b.dom('connectionForm').onsubmit({preventDefault() {}}); await settle();
    assert.equal(b.run('authToken'), 'valid-a');
    assert.deepEqual(savedRecord(b), {token: 'valid-a', agentId: 'agent-1'});
    const start = b.requests.length; await b.tick();
    assert.ok(b.requests.length > start);
    assert.ok(b.requests.slice(start).every(request => request.headers.Authorization === 'Bearer valid-a'));
    assert.equal(b.run('currentData.agent.id'), 'agent-1');
  },
  async storage_failures_keep_in_memory_login() {
    for (const mode of ['getter', 'read', 'write', 'remove']) {
      const saved = storage();
      if (mode === 'read') saved.failRead = true;
      if (mode === 'write') saved.failWrite = true;
      const b = browser({saved, storageGetterThrows: mode === 'getter'}); await settle();
      await login(b);
      assert.equal(b.run('currentData.agent.id'), 'agent-1');
      if (mode === 'remove') saved.failRemove = true;
      b.run('logout()'); await settle(); assertLoggedOut(b);
      assert.ok(b.dom('authNotice').textContent, 'Storage failures have a visible nonfatal notice');
    }
  },
  async invalid_saved_record_does_not_authenticate() {
    for (const value of ['not-json', 'null', '[]', '{}',
      JSON.stringify({token: 42, agentId: 'agent-1'}), JSON.stringify({token: '', agentId: 'agent-1'})]) {
      const b = browser({saved: storage(value)}); await settle();
      assert.equal(b.requests.length, 0, 'Malformed local state must not make authenticated calls');
      assert.equal(b.run('authToken'), ''); assert.equal(b.intervals.size, 0);
    }
  },
};

const name = process.argv[3];
assert.ok(Object.hasOwn(scenarios, name), 'Unknown scenario: ' + name);
scenarios[name]().then(() => process.stdout.write(name + ': passed\n')).catch(error => {
  console.error(error.stack || error); process.exitCode = 1;
});
