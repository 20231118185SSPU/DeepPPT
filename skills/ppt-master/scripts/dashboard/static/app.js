const state = {
  pipeline: null,
  artifacts: null,
  quality: null,
  logs: null,
  selectedArtifact: null,
  traceFilters: {
    query: '',
    step: 'all',
    type: '',
    order: 'desc',
    limit: '80',
    offset: 0,
  },
  actionStatus: {},
  artifactFilters: {
    query: '',
    step: 'all',
    phase: 'all',
    sort: 'mtime_desc',
  },
  previewModal: {
    path: '',
    index: 0,
    fit: 'contain',
    pages: null,
    kind: '',
    title: '',
  },
  openArtifactGroups: new Set(),
  connected: false,
  polling: null,
  apiErrors: {},
  language: localStorage.getItem('dashboard-language') || 'zh',
};

const messages = {
  zh: {
    brand_subtitle: '项目控制台',
    route_pipeline: '管线总览',
    route_services: '服务入口',
    route_step: '步骤工作台',
    route_confirm: '确认中心',
    route_preview: '实时预览',
    route_quality: '质量中心',
    route_artifacts: '产物与日志',
    confirm_running: '打开确认',
    confirm_stopped: '确认未运行',
    preview_running: '打开预览',
    preview_stopped: '预览未运行',
    sse_live: 'SSE 实时',
    polling: '轮询模式',
    template_free: '自由设计',
    template_applied: '已应用模板',
    template_missing: '模板路径异常',
    template_option: '模板路线',
    current_route: '当前路线',
    template_discovery: '模板库候选',
    template_preview_title: '模板库候选预览',
    template_preview_desc: '这里展示全局模板库候选；Step 4 的设计确认以 Confirm UI / recommendations.json 为准。点击缩略图可放大查看。',
    no_template_preview: '暂无 SVG 预览',
    new_window: '新窗口',
    close: '关闭',
    modal_label: '放大预览',
  },
  en: {
    brand_subtitle: 'Project Dashboard',
    route_pipeline: 'Pipeline',
    route_services: 'Services',
    route_step: 'Step Workspace',
    route_confirm: 'Confirm Center',
    route_preview: 'Live Preview',
    route_quality: 'Quality',
    route_artifacts: 'Artifacts & Logs',
    confirm_running: 'Open Confirm',
    confirm_stopped: 'Confirm stopped',
    preview_running: 'Open Preview',
    preview_stopped: 'Preview stopped',
    sse_live: 'SSE live',
    polling: 'Polling',
    template_free: 'Free design',
    template_applied: 'Template applied',
    template_missing: 'Template path issue',
    template_option: 'Template Route',
    current_route: 'Current route',
    template_discovery: 'Template candidates',
    template_preview_title: 'Template Candidate Preview',
    template_preview_desc: 'This section shows global template-library candidates. Step 4 design confirmation remains driven by Confirm UI / recommendations.json. Click a thumbnail to enlarge.',
    no_template_preview: 'No SVG preview',
    new_window: 'New window',
    close: 'Close',
    modal_label: 'Enlarged preview',
  },
};

const statusLabels = {
  completed: '完成',
  active: '进行中',
  pending: '待处理',
  skipped: '已跳过',
  failed: '失败',
  blocked: '阻塞',
};

const artifactTypeLabels = {
  source: '源文件',
  template: '模板',
  analysis: '分析数据',
  image: '图片素材',
  image_ai: 'AI 图片配置',
  image_web: '网页图片配置',
  icon: '图标',
  svg: 'SVG 草稿',
  svg_final: 'SVG 成品',
  notes: '讲稿备注',
  pptx: 'PPTX 导出',
  backup: '备份',
  audio: '音频',
  video: '视频',
  pdf: 'PDF',
  confirm: '确认记录',
  spec: '设计规格',
  lock: '规格锁',
  animation: '动画配置',
  quality_report: '质量报告',
  markdown: 'Markdown 文档',
  json: 'JSON 数据',
  jsonl: 'JSONL 日志',
  text: '文本文件',
  binary: '二进制文件',
  unknown: '其他文件',
  config: '配置文件',
};

const artifactGroupLabels = {
  pptx: 'PPTX 文件',
  pdf: 'PDF 文件',
  audio: '音频文件',
  video: '视频文件',
  image: '图片文件',
  svg: 'SVG 页面',
  markdown: 'Markdown 文档',
  json: 'JSON 数据',
  jsonl: 'JSONL 日志',
  text: '文本文件',
  binary: '二进制文件',
  unknown: '其他文件',
};
const artifactTypeOrder = [
  'pptx',
  'pdf',
  'audio',
  'video',
  'svg_final',
  'svg',
  'image',
  'research',
  'markdown',
  'json',
  'jsonl',
  'text',
  'notes',
  'spec',
  'lock',
  'analysis',
  'source',
  'template',
  'icon',
  'confirm',
  'quality_report',
  'backup',
  'binary',
  'unknown',
  'config',
];

document.addEventListener('DOMContentLoaded', () => {
  document.addEventListener('click', handleDocumentClick);
  document.addEventListener('input', handleDocumentInput);
  document.addEventListener('change', handleDocumentChange);
  document.addEventListener('keydown', handleKeydown);
  window.addEventListener('hashchange', render);
  boot();
});

function t(key) {
  return messages[state.language]?.[key] || messages.zh[key] || key;
}

async function handleDocumentClick(event) {
  const phaseChip = event.target.closest('[data-artifact-phase]');
  if (phaseChip) {
    event.preventDefault();
    const phase = phaseChip.dataset.artifactPhase;
    state.artifactFilters.phase = state.artifactFilters.phase === phase ? 'all' : phase;
    render();
    return;
  }

  const action = event.target.closest('[data-action-run]');
  if (action) {
    event.preventDefault();
    await confirmAndRunAction(action.dataset.actionRun);
    return;
  }

  const tracePage = event.target.closest('[data-trace-page]');
  if (tracePage) {
    event.preventDefault();
    state.traceFilters.offset = Math.max(
      0,
      state.traceFilters.offset + Number(tracePage.dataset.tracePage || 0),
    );
    await loadLogs();
    render();
    return;
  }

  const refresh = event.target.closest('[data-refresh]');
  if (refresh) {
    event.preventDefault();
    await refreshAll();
    render();
    return;
  }

  const closeModal = event.target.closest('[data-modal-close]');
  if (closeModal && (event.target === closeModal || closeModal.tagName === 'BUTTON')) {
    event.preventDefault();
    closePreviewModal();
    return;
  }

  const modalNav = event.target.closest('[data-modal-nav]');
  if (modalNav) {
    event.preventDefault();
    movePreviewModal(Number(modalNav.dataset.modalNav));
    return;
  }

  const modalPage = event.target.closest('[data-modal-page]');
  if (modalPage) {
    event.preventDefault();
    setPreviewModalPage(Number(modalPage.dataset.modalPage));
    return;
  }

  const modalFit = event.target.closest('[data-modal-fit]');
  if (modalFit) {
    event.preventDefault();
    setPreviewModalFit(modalFit.dataset.modalFit);
    return;
  }

  const previewModal = event.target.closest('[data-preview-modal]');
  if (previewModal) {
    event.preventDefault();
    openPreviewModal(previewModal.dataset.previewModal);
    return;
  }

  const templateModal = event.target.closest('[data-template-modal]');
  if (templateModal) {
    event.preventDefault();
    openTemplatePreviewModal(templateModal);
    return;
  }

  const langToggle = event.target.closest('[data-lang-toggle]');
  if (langToggle) {
    event.preventDefault();
    state.language = state.language === 'zh' ? 'en' : 'zh';
    localStorage.setItem('dashboard-language', state.language);
    render();
    return;
  }

  const artifact = event.target.closest('[data-artifact-path]');
  if (artifact) {
    event.preventDefault();
    if (artifact.dataset.artifactJump === '1') window.location.hash = '#/artifacts';
    await loadArtifact(artifact.dataset.artifactPath);
    return;
  }

  const group = event.target.closest('[data-artifact-group]');
  if (group) {
    event.preventDefault();
    toggleArtifactGroup(group.dataset.artifactGroup);
    render();
  }
}

async function handleDocumentInput(event) {
  if (updateTraceFilter(event.target)) {
    await loadLogs();
    render();
    return;
  }
  updateArtifactFilter(event.target);
}

async function handleDocumentChange(event) {
  if (updateTraceFilter(event.target)) {
    await loadLogs();
    render();
    return;
  }
  updateArtifactFilter(event.target);
}

function updateArtifactFilter(target) {
  const key = target?.dataset?.artifactFilter;
  if (!key || !(key in state.artifactFilters)) return;
  state.artifactFilters[key] = target.value;
  render();
}

function updateTraceFilter(target) {
  const key = target?.dataset?.traceFilter;
  if (!key || !(key in state.traceFilters)) return false;
  state.traceFilters[key] = target.value;
  state.traceFilters.offset = 0;
  return true;
}

function handleKeydown(event) {
  if (!state.previewModal.path) return;
  if (event.key === 'Escape') closePreviewModal();
  if (event.key === 'ArrowLeft') movePreviewModal(-1);
  if (event.key === 'ArrowRight') movePreviewModal(1);
}

function openPreviewModal(path) {
  const detail = state.selectedArtifact;
  if (!detail || detail.loading || detail.error || detail.path !== path) return;
  if (!canEnlargeArtifact(detail)) return;
  const pages = previewModalPages(detail);
  const selectedIndex = Math.max(0, pages.findIndex((page) => page.path === detail.path));
  state.previewModal = {
    path,
    index: selectedIndex,
    fit: state.previewModal.fit || 'contain',
    pages: null,
    kind: '',
    title: '',
  };
  renderPreviewModal();
}

function openUrlPreviewModal(url, name, title, kind = 'svg') {
  if (!url) return;
  state.previewModal = {
    path: url,
    index: 0,
    fit: state.previewModal.fit || 'contain',
    pages: [{ name, path: title || name, url }],
    kind,
    title: title || name,
  };
  renderPreviewModal();
}

function openTemplatePreviewModal(trigger) {
  const pages = parseTemplatePages(trigger.dataset.templatePages);
  const startIndex = Math.max(0, Number(trigger.dataset.templateIndex || 0) || 0);
  const fallbackUrl = trigger.dataset.templateModal;
  const fallbackName = trigger.dataset.templateName || 'Template preview';
  const title = trigger.dataset.templateTitle || fallbackName;
  const modalPages = pages.length ? pages : [{ name: fallbackName, path: title, url: fallbackUrl }];
  if (!modalPages.length || !modalPages[0].url) return;
  const index = Math.min(startIndex, modalPages.length - 1);
  state.previewModal = {
    path: modalPages[index].url,
    index,
    fit: state.previewModal.fit || 'contain',
    pages: modalPages,
    kind: 'svg',
    title,
  };
  renderPreviewModal();
}

function parseTemplatePages(raw) {
  if (!raw) return [];
  try {
    const pages = JSON.parse(raw);
    if (!Array.isArray(pages)) return [];
    return pages
      .filter((page) => page && page.url)
      .map((page) => ({
        name: String(page.name || 'Template preview'),
        path: String(page.path || page.name || ''),
        url: String(page.url),
      }));
  } catch {
    return [];
  }
}

function closePreviewModal() {
  state.previewModal.path = '';
  state.previewModal.index = 0;
  state.previewModal.pages = null;
  state.previewModal.kind = '';
  state.previewModal.title = '';
  renderPreviewModal();
}

function movePreviewModal(delta) {
  const detail = modalDetail();
  const pages = activePreviewModalPages(detail);
  if (!state.previewModal.path || !pages.length) return;
  state.previewModal.index = (state.previewModal.index + delta + pages.length) % pages.length;
  state.previewModal.path = pages[state.previewModal.index]?.url || state.previewModal.path;
  renderPreviewModal();
}

function setPreviewModalPage(index) {
  const detail = modalDetail();
  const pages = activePreviewModalPages(detail);
  if (!state.previewModal.path || index < 0 || index >= pages.length) return;
  state.previewModal.index = index;
  state.previewModal.path = pages[index]?.url || state.previewModal.path;
  renderPreviewModal();
}

function setPreviewModalFit(fit) {
  if (!state.previewModal.path) return;
  if (!['contain', 'width', 'height', 'actual'].includes(fit)) return;
  state.previewModal.fit = fit;
  renderPreviewModal();
}

function modalDetail() {
  if (state.previewModal.pages) {
    return {
      name: state.previewModal.title || state.previewModal.pages[0]?.name || '',
      path: state.previewModal.path,
      open_url: state.previewModal.pages[0]?.url || state.previewModal.path,
      preview_kind: state.previewModal.kind || 'svg',
    };
  }
  const detail = state.selectedArtifact;
  if (!state.previewModal.path || !detail || detail.path !== state.previewModal.path || detail.loading || detail.error) return null;
  return detail;
}

function renderPreviewModal() {
  let root = document.getElementById('modalRoot');
  if (!root) {
    root = document.createElement('div');
    root.id = 'modalRoot';
    document.body.appendChild(root);
  }
  const detail = modalDetail();
  if (!state.previewModal.path || !detail) {
    root.innerHTML = '';
    document.body.classList.remove('modal-open');
    return;
  }
  document.body.classList.add('modal-open');
  const pages = activePreviewModalPages(detail);
  const kind = state.previewModal.kind || effectivePreviewKind(detail);
  const index = Math.min(state.previewModal.index || 0, Math.max(0, pages.length - 1));
  const page = pages[index] || { name: detail.name, path: detail.path, url: detail.open_url };
  const fit = state.previewModal.fit || 'contain';
  const modalUrl = previewModalUrl(page.url || detail.open_url, kind, fit);
  const canPage = pages.length > 1 && ['svg', 'pptx'].includes(kind);
  state.previewModal.index = index;
  root.innerHTML = `
    <div class="modal-backdrop" data-modal-close="true">
      <section class="preview-modal modal-kind-${escapeAttr(kind)}" role="dialog" aria-modal="true" aria-label="${escapeAttr(t('modal_label'))}">
        <header class="modal-topbar">
          <div class="modal-title">
            <span class="eyebrow">${escapeHtml(previewKindLabel(kind))}</span>
            <h2>${escapeHtml(page.name || detail.name)}</h2>
            <p>${escapeHtml(page.path || detail.path)}</p>
          </div>
          <div class="modal-actions">
            ${modalFitControls(fit)}
            <a class="button secondary" href="${escapeAttr(page.url || detail.open_url)}" target="_blank" rel="noreferrer" title="${escapeAttr(t('new_window'))}">${escapeHtml(t('new_window'))}</a>
            <button type="button" class="button secondary" data-modal-close="true" aria-label="${escapeAttr(t('close'))}" title="${escapeAttr(t('close'))}">${escapeHtml(t('close'))}</button>
          </div>
        </header>
        <div class="modal-stage modal-fit-${escapeAttr(fit)}">
          ${canPage ? '<button type="button" class="modal-arrow left" data-modal-nav="-1" aria-label="上一页" title="上一页">‹</button>' : ''}
          ${modalFrameHtml(modalUrl, page.name || detail.name, kind)}
          ${canPage ? '<button type="button" class="modal-arrow right" data-modal-nav="1" aria-label="下一页" title="下一页">›</button>' : ''}
        </div>
        ${canPage ? modalStrip(pages, index) : ''}
      </section>
    </div>
  `;
}

function activePreviewModalPages(detail) {
  return state.previewModal.pages || previewModalPages(detail);
}

function modalFrameHtml(url, title, kind) {
  const safeUrl = escapeAttr(url);
  const safeTitle = escapeAttr(title || 'Preview');
  if (kind === 'svg' || kind === 'pptx') {
    return `<img class="modal-frame modal-image-frame" src="${safeUrl}" alt="${safeTitle}">`;
  }
  return `<iframe class="modal-frame" src="${safeUrl}" title="${safeTitle}"></iframe>`;
}

function modalFitControls(activeFit) {
  const options = [
    ['contain', '适配窗口'],
    ['width', '适配宽度'],
    ['height', '适配高度'],
    ['actual', '100%'],
  ];
  return `<div class="modal-fit-controls" aria-label="预览缩放">
    ${options.map(([fit, label]) => `<button
      type="button"
      class="modal-fit ${fit === activeFit ? 'active' : ''}"
      data-modal-fit="${fit}"
      aria-pressed="${fit === activeFit}"
      title="${label}"
    >${label}</button>`).join('')}
  </div>`;
}

function previewModalUrl(url, kind, fit) {
  if (kind !== 'pdf') return url;
  const fragment = {
    contain: 'zoom=page-fit',
    width: 'zoom=page-width',
    height: 'view=FitV',
    actual: 'zoom=100',
  }[fit] || 'zoom=page-fit';
  return `${url.split('#')[0]}#${fragment}`;
}
function modalStrip(pages, index) {
  if (pages.length <= 1) return '';
  return `<div class="modal-strip">
    ${pages.map((page, pageIndex) => `<button type="button" class="modal-page ${pageIndex === index ? 'active' : ''}" data-modal-page="${pageIndex}" title="第 ${pageIndex + 1} 页" aria-current="${pageIndex === index ? 'page' : 'false'}">${pageIndex + 1}</button>`).join('')}
  </div>`;
}

async function loadArtifact(relPath) {
  state.selectedArtifact = { loading: true, path: relPath };
  render();
  const detail = await fetchJson(
    `/api/artifact?path=${encodeURIComponent(relPath)}`,
    { error: '无法加载产物', path: relPath },
  );
  state.selectedArtifact = detail;
  render();
}

function toggleArtifactGroup(key) {
  if (state.openArtifactGroups.has(key)) state.openArtifactGroups.delete(key);
  else state.openArtifactGroups.add(key);
}

async function boot() {
  await refreshAll();
  connectEvents();
  render();
}

async function refreshAll() {
  state.pipeline = await fetchJson('/api/state', null, 'pipeline');
  state.artifacts = await fetchJson('/api/artifacts', { artifacts: [], total: 0, by_type: {} }, 'artifacts');
  state.quality = await fetchJson('/api/quality', null, 'quality');
  await loadLogs();
}

async function fetchJson(url, fallback = {}, key = '') {
  try {
    const res = await fetch(url);
    if (!res.ok) {
      if (key) state.apiErrors[key] = `HTTP ${res.status}`;
      return fallback;
    }
    const payload = await res.json();
    if (key) delete state.apiErrors[key];
    return payload;
  } catch (error) {
    if (key) state.apiErrors[key] = error?.message || '网络请求失败';
    return fallback;
  }
}

async function postJson(url, payload, fallback = {}, key = '') {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => fallback);
    if (!res.ok) {
      if (key) state.apiErrors[key] = data?.error || `HTTP ${res.status}`;
      return data || fallback;
    }
    if (key) delete state.apiErrors[key];
    return data;
  } catch (error) {
    if (key) state.apiErrors[key] = error?.message || '网络请求失败';
    return fallback;
  }
}

async function loadLogs() {
  state.logs = await fetchJson(traceLogUrl(), { events: [], total: 0, has_more: false }, 'logs');
}

function traceLogUrl() {
  const filters = state.traceFilters;
  const params = new URLSearchParams({
    limit: String(filters.limit || 80),
    offset: String(filters.offset || 0),
    order: filters.order || 'desc',
  });
  if (filters.query.trim()) params.set('query', filters.query.trim());
  if (filters.type.trim()) params.set('type', filters.type.trim());
  if (filters.step !== 'all') params.set('step', filters.step);
  return `/api/log?${params.toString()}`;
}

async function confirmAndRunAction(action) {
  const payload = actionPayload(action);
  const previewUrl = actionPreviewUrl(action, payload);
  const preview = await fetchJson(previewUrl, null, 'action');
  if (!preview || preview.error) {
    state.actionStatus[action] = { status: 'failed', stderr_tail: preview?.error || '无法读取命令预览。' };
    render();
    return;
  }
  const commands = (preview.commands || []).join('\n') || preview.command_preview || '';
  const confirmed = window.confirm([
    '确认执行这个 Dashboard 辅助动作？',
    '',
    `动作：${actionLabel(action)}`,
    `项目：${preview.project_path || state.pipeline?.project_path || ''}`,
    '',
    commands,
  ].join('\n'));
  if (!confirmed) return;

  const result = await postJson(`/api/actions/${encodeURIComponent(action)}`, payload, null, 'action');
  state.actionStatus[action] = result || { status: 'failed', stderr_tail: '动作请求失败。' };
  render();
  if (result?.action_id && ['running', 'existing'].includes(result.status)) {
    pollAction(action, result.action_id);
  }
}

function actionPayload(action) {
  if (action === 'run-quality') {
    return { confirm: true, mode: 'quick', checks: ['harness'] };
  }
  return { confirm: true };
}

function actionPreviewUrl(action, payload) {
  const params = new URLSearchParams();
  if (action === 'run-quality') {
    params.set('mode', payload.mode);
    params.set('checks', payload.checks.join(','));
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  return `/api/actions/${encodeURIComponent(action)}/preview${suffix}`;
}

function pollAction(action, actionId) {
  window.setTimeout(async () => {
    const result = await fetchJson(`/api/actions/${encodeURIComponent(actionId)}`, null, 'action');
    if (result) state.actionStatus[action] = result;
    if (result?.status === 'running') {
      pollAction(action, actionId);
    } else {
      await refreshAll();
    }
    render();
  }, 1200);
}

function connectEvents() {
  if (!window.EventSource) {
    startPolling();
    return;
  }
  const es = new EventSource('/api/events');
  es.addEventListener('open', () => {
    state.connected = true;
    updateConnection();
  });
  es.addEventListener('pipeline:state', (event) => {
    state.pipeline = JSON.parse(event.data);
    render();
  });
  es.addEventListener('artifact:new', async () => {
    state.artifacts = await fetchJson('/api/artifacts');
    render();
  });
  es.addEventListener('quality:update', async () => {
    state.quality = await fetchJson('/api/quality', null, 'quality');
    render();
  });
  es.addEventListener('confirm:done', async () => {
    state.pipeline = await fetchJson('/api/state');
    render();
  });
  es.addEventListener('error', () => {
    state.connected = false;
    updateConnection();
  });
  es.onerror = () => {
    state.connected = false;
    updateConnection();
    startPolling();
  };
}

function startPolling() {
  if (state.polling) return;
  state.polling = setInterval(async () => {
    await refreshAll();
    render();
  }, 5000);
}

function route() {
  const raw = location.hash || '#/artifacts';
  const parts = raw.replace(/^#\//, '').split('/');
  return { name: parts[0] || 'artifacts', arg: parts[1] };
}

function render() {
  applyStaticI18n();
  updateChrome();
  const current = route();
  const title = routeTitle(current.name);
  document.getElementById('pageTitle').textContent = title;
  document.querySelectorAll('.nav a').forEach((link) => {
    link.classList.toggle('active', link.dataset.route === current.name);
  });
  const app = document.getElementById('app');
  if (!state.pipeline) {
    app.innerHTML = state.apiErrors.pipeline
      ? errorState('无法读取控制台状态', state.apiErrors.pipeline)
      : '<div class="empty">正在读取控制台状态...</div>';
    return;
  }
  if (current.name === 'step') renderStep(app, Number(current.arg || state.pipeline.current_step || 1));
  else if (current.name === 'services') renderServices(app);
  else if (current.name === 'confirm') renderConfirm(app);
  else if (current.name === 'preview') renderPreview(app);
  else if (current.name === 'quality') renderQuality(app);
  else if (current.name === 'artifacts') renderArtifacts(app);
  else renderPipeline(app);
  renderPreviewModal();
}

function updateChrome() {
  updateConnection();
  if (!state.pipeline) return;
  const meta = `${state.pipeline.project_name} · Step ${state.pipeline.current_step || '-'} · ${state.pipeline.canvas_format || '画布待定'}`;
  document.getElementById('projectMeta').textContent = meta;
  setServiceLink('confirmLink', state.pipeline.confirm_ui, t('confirm_running'), t('confirm_stopped'), 'Confirm UI');
  setServiceLink('previewLink', state.pipeline.live_preview, t('preview_running'), t('preview_stopped'), 'Live Preview');
  renderStepRail();
}

function updateConnection() {
  const badge = document.getElementById('connectionBadge');
  badge.textContent = state.connected ? t('sse_live') : t('polling');
  badge.title = state.connected ? '事件流已连接' : '事件流不可用，正在定时刷新';
  badge.className = `badge ${state.connected ? 'ok' : 'warn'}`;
}

function setServiceLink(id, service, runningText, stoppedText, serviceName) {
  const link = document.getElementById(id);
  const running = Boolean(service?.running && service?.url);
  link.textContent = running ? runningText : stoppedText;
  link.classList.toggle('disabled', !running);
  link.setAttribute('aria-disabled', String(!running));
  link.title = running
    ? `${serviceName} 正在运行：${service.url}`
    : `${serviceName} 当前未运行；可在“服务入口”或对应工作台按需启动`;
  if (running) link.href = service.url;
  else link.removeAttribute('href');
}

function renderStepRail() {
  const rail = document.getElementById('stepRail');
  if (!state.pipeline?.steps) return;
  rail.innerHTML = state.pipeline.steps.map((step) => `
    <a class="rail-step ${escapeAttr(step.state)}" href="#/step/${step.step}" title="Step ${step.step}: ${escapeAttr(stepName(step))}">
      <span>${step.step}</span>
      <strong>${escapeHtml(stepName(step))}</strong>
    </a>
  `).join('');
}

function renderPipeline(app) {
  const p = state.pipeline;
  const steps = p.steps || [];
  const completed = steps.filter((step) => step.state === 'completed').length;
  const activeStep = steps.find((step) => step.step === p.current_step) || steps.find((step) => step.state === 'active') || steps[0];
  const progress = steps.length ? Math.round((completed / steps.length) * 100) : 0;
  const health = p.health_summary || { status: 'unknown', reasons: [] };
  app.innerHTML = `
    <section class="hero-panel pipeline-hero">
      <div>
        <span class="eyebrow">管线总览</span>
        <h2>${escapeHtml(p.project_name || 'DeepPPT Project')}</h2>
        <p>当前处于 Step ${p.current_step || '-'}${activeStep ? ` · ${escapeHtml(stepName(activeStep))}` : ''}</p>
        <div class="health-line">
          ${healthBadge(health.status)}
          <span>${escapeHtml((health.reasons || [])[0] || '暂无健康度说明。')}</span>
        </div>
      </div>
      <div class="hero-gauge">
        <strong>${progress}%</strong>
        <span>管线完成度</span>
      </div>
    </section>
    <div class="summary-grid premium">
      ${metric('当前步骤', `${p.current_step || '-'} / 8`)}
      ${metric('完成步骤', `${completed} / ${steps.length || 8}`)}
      ${metric('页面 / SVG', `${p.page_count ?? '-'} / ${p.svg_count ?? 0}`)}
      ${metric('质量状态', p.quality_summary?.overall || '待生成')}
    </div>
    <div class="panel premium-panel">
      <div class="panel-head">
        <div>
          <span class="eyebrow">项目健康度</span>
          <h2>${escapeHtml(healthStatusText(health.status))}</h2>
        </div>
      </div>
      ${healthReasons(health)}
    </div>
    <div class="panel premium-panel">
      <div class="panel-head">
        <div>
          <span class="eyebrow">执行地图</span>
          <h2>8 步管线</h2>
          <p>每个步骤卡片展示 Gate、子步骤和产物数量，点击可进入步骤工作台。</p>
        </div>
      </div>
      <div class="pipeline-track">
        ${steps.map(timelineStep).join('')}
      </div>
      <div class="step-grid dense premium-steps">
        ${steps.map(stepCard).join('')}
      </div>
    </div>
  `;
}

function renderStep(app, stepNo) {
  const step = state.pipeline.steps.find((item) => item.step === stepNo) || state.pipeline.steps[0];
  app.innerHTML = `
    <section class="hero-panel step-hero">
      <div>
        <span class="eyebrow">Step ${step.step}</span>
        <h2>${escapeHtml(stepName(step))}</h2>
        <p>${statusText(step.state)}${step.blocking ? ' · 需要确认后继续' : ' · Dashboard 读取当前步骤状态'}</p>
      </div>
      <div class="hero-stack">
        ${stateLabel(step.state)}
        <span>${gateSummaryText(step.gate)}</span>
      </div>
    </section>
    <div class="summary-grid premium">
      ${metric('步骤状态', statusText(step.state))}
      ${metric('Gate', gateSummaryText(step.gate))}
      ${metric('子步骤', `${completedSubSteps(step)} / ${(step.sub_steps || []).length}`)}
    </div>
    ${step.step === 3 ? templateRoutePanel(state.pipeline.template_route) : ''}
    <div class="workbench-grid">
      <div class="panel premium-panel">
        <span class="eyebrow">Gate</span>
        <h2>进入条件</h2>
        ${gateListHtml(step.gate)}
      </div>
      <div class="panel premium-panel">
        <span class="eyebrow">子步骤</span>
        <h2>执行明细</h2>
        <div class="list compact-list">
          ${(step.sub_steps || []).map(subStepHtml).join('') || '<div class="empty small">暂无子步骤。</div>'}
        </div>
      </div>
    </div>
  `;
}

function renderServices(app) {
  const p = state.pipeline;
  app.innerHTML = `
    <section class="hero-panel services-hero">
      <div>
        <span class="eyebrow">统一入口</span>
        <h2>本地页面与服务</h2>
        <p>所有本地页面都在这里显示实际 URL、端口、项目路径和日志位置；启动辅助页前后不依赖默认端口假设。</p>
      </div>
      <div class="hero-stack">
        <strong>${escapeHtml(serviceStatusText(p.dashboard))}</strong>
        <span>Dashboard</span>
      </div>
    </section>
    <div class="summary-grid premium">
      ${metric('Dashboard', serviceStatusText(p.dashboard))}
      ${metric('Confirm UI', serviceStatusText(p.confirm_ui))}
      ${metric('Live Preview', serviceStatusText(p.live_preview))}
      ${metric('项目路径', p.project_path || '-')}
    </div>
    <div class="service-center-grid">
      <div class="panel premium-panel service-panel-large">
        <span class="eyebrow">Dashboard</span>
        <h2>项目控制台</h2>
        ${servicePanel(p.dashboard, 'Dashboard', '打开控制台')}
      </div>
      <div class="panel premium-panel service-panel-large">
        <span class="eyebrow">Step 4</span>
        <h2>设计确认</h2>
        ${servicePanel(p.confirm_ui, 'Confirm UI', '打开确认页面', 'start-confirm')}
        ${actionStatusPanel('start-confirm')}
      </div>
      <div class="panel premium-panel service-panel-large">
        <span class="eyebrow">Step 6</span>
        <h2>实时预览</h2>
        ${servicePanel(p.live_preview, 'Live Preview', '打开实时预览', 'start-preview')}
        ${actionStatusPanel('start-preview')}
      </div>
    </div>
  `;
}

function renderConfirm(app) {
  const p = state.pipeline;
  app.innerHTML = `
    <section class="hero-panel confirm-hero">
      <div>
        <span class="eyebrow">决策中心</span>
        <h2>确认中心</h2>
        <p>只读呈现 Step 4 决策状态，确认动作仍由 Confirm UI 或聊天完成。</p>
      </div>
      <div class="hero-stack">
        <strong>${escapeHtml(p.confirm_status || '待确认')}</strong>
        <span>${p.spec_lock_digest ? 'Spec Lock 已生成' : 'Spec Lock 未生成'}</span>
      </div>
    </section>
    <div class="summary-grid premium">
      ${metric('确认状态', p.confirm_status || '待确认')}
      ${metric('生成模式', p.generation_mode || '待定')}
      ${metric('模板路线', templateRouteLabel(p.template_route))}
      ${metric('Confirm UI', serviceStatusText(p.confirm_ui))}
    </div>
    ${templateRoutePanel(p.template_route)}
    <div class="status-layout premium-layout">
      <div class="panel premium-panel service-panel-large">
        <span class="eyebrow">服务状态</span>
        <h2>确认服务</h2>
        ${servicePanel(p.confirm_ui, 'Confirm UI', '打开确认页面', 'start-confirm')}
        ${actionStatusPanel('start-confirm')}
      </div>
      <div class="panel premium-panel">
        <span class="eyebrow">确认文件</span>
        <h2>确认产物</h2>
        <div class="status-list rich-list">
          ${statusRow('design_spec.md', hasArtifactPath('design_spec.md'))}
          ${statusRow('spec_lock.md', hasArtifactPath('spec_lock.md'))}
          ${statusRow('confirm_ui/result.json', hasArtifactPath('confirm_ui/result.json'))}
        </div>
      </div>
    </div>
  `;
}

function renderPreview(app) {
  const p = state.pipeline;
  app.innerHTML = `
    <section class="hero-panel preview-hero">
      <div>
        <span class="eyebrow">实时预览</span>
        <h2>实时预览</h2>
        <p>显示 SVG 编辑预览服务状态；产物预览在“产物与日志”中按文件打开。</p>
      </div>
      <div class="hero-stack">
        <strong>${escapeHtml(serviceStatusText(p.live_preview))}</strong>
        <span>${p.svg_count ?? 0} / ${p.page_count ?? '?'} SVG</span>
      </div>
    </section>
    <div class="summary-grid premium">
      ${metric('Live Preview', serviceStatusText(p.live_preview))}
      ${metric('SVG', `${p.svg_count ?? 0} / ${p.page_count ?? '?'}`)}
      ${metric('导出文件', p.export_path ? '已导出' : '待导出')}
      ${metric('讲稿备注', stepState(6, 'notes_total'))}
    </div>
    <div class="status-layout premium-layout">
      <div class="panel premium-panel service-panel-large">
        <span class="eyebrow">服务状态</span>
        <h2>预览服务</h2>
        ${servicePanel(p.live_preview, 'Live Preview', '打开实时预览', 'start-preview')}
        ${actionStatusPanel('start-preview')}
      </div>
      <div class="panel premium-panel">
        <span class="eyebrow">预览来源</span>
        <h2>预览产物</h2>
        <div class="status-list rich-list">
          ${statusRow('svg_output/', countType('svg') > 0, `${countType('svg')} 个草稿 SVG`)}
          ${statusRow('svg_final/', countType('svg_final') > 0, `${countType('svg_final')} 个成品 SVG`)}
          ${statusRow('exports/', countType('pptx') > 0, `${countType('pptx')} 个 PPTX`)}
        </div>
      </div>
    </div>
  `;
}

function renderQuality(app) {
  if (state.apiErrors.quality) {
    app.innerHTML = qualityEmptyHtml(true);
    return;
  }
  const q = state.quality;
  if (!q) {
    app.innerHTML = qualityEmptyHtml(false);
    return;
  }
  const harness = q.harness || q;
  const checks = q.checks || legacyQualityChecks(harness);
  const issues = q.issues || { must_fix: [], should_fix: [], accepted_risks: [] };
  const overall = q.overall || normalizeQualityStatus(harness.overall);
  const raw = q.raw || q;
  const diagnostics = q.diagnostics || {};
  app.innerHTML = `
    <section class="hero-panel quality-hero">
      <div>
        <span class="eyebrow">质量门禁</span>
        <h2>质量中心</h2>
        <p>读取已有质量报告，按检查项和修复优先级聚合展示；不会自动运行质量脚本。</p>
      </div>
      <div class="hero-stack">
        <strong>${escapeHtml(qualityStatusText(overall))}</strong>
        <span>${escapeHtml(compactDate(q.checked_at || ''))}</span>
      </div>
    </section>
    <div class="summary-grid premium quality-summary">
      ${qualityMetric('总体', overall)}
      ${qualityMetric('规格', checkStatus(checks, 'spec_compliance'))}
      ${qualityMetric('SVG', checkStatus(checks, 'svg_quality'))}
      ${qualityMetric('E2E', checkStatus(checks, 'e2e'))}
      ${qualityMetric('视觉回看', checkStatus(checks, 'visual_review'))}
    </div>
    <div class="panel premium-panel quality-panel">
      <div class="panel-head">
        <div>
          <span class="eyebrow">检查项</span>
          <h2>质量矩阵</h2>
        </div>
        ${actionButton('run-quality')}
      </div>
      ${qualityCheckMatrix(checks)}
      ${actionStatusPanel('run-quality')}
    </div>
    ${qualityDiagnosticsPanel(diagnostics)}
    <div class="quality-issues-grid">
      ${qualityIssueSection('must_fix', '必须修复', issues.must_fix || [])}
      ${qualityIssueSection('should_fix', '建议修复', issues.should_fix || [])}
      ${qualityIssueSection('accepted_risks', '已接受风险', issues.accepted_risks || [])}
    </div>
    <div class="panel premium-panel quality-panel">
      <span class="eyebrow">原始数据</span>
      <h2>原始报告</h2>
      <details class="quality-raw">
        <summary>展开 JSON 原文</summary>
        <pre>${escapeHtml(JSON.stringify(raw, null, 2))}</pre>
      </details>
    </div>
  `;
}

function renderArtifacts(app) {
  if (state.apiErrors.artifacts) {
    app.innerHTML = errorState('无法读取产物列表', state.apiErrors.artifacts);
    return;
  }
  const artifacts = state.artifacts?.artifacts || [];
  const visibleArtifacts = filteredArtifacts(artifacts);
  const groups = artifactGroups(visibleArtifacts);
  const selectedVisible = selectedArtifactVisible(visibleArtifacts);
  const phases = state.artifacts?.phases || {};
  const phaseNav = [
    ['idea', '制作思路', phases.idea || 0],
    ['design', '设计契约', phases.design || 0],
    ['generate', '生成页面', phases.generate || 0],
    ['export', '导出成品', phases.export || 0],
  ].map(([key, label, count]) => `
    <button type="button" class="phase-chip${state.artifactFilters.phase === key ? ' active' : ''}"
      data-artifact-phase="${key}" title="只看${label}产物">
      <span class="phase-chip-label">${label}</span>
      <span class="phase-chip-count">${count}</span>
    </button>`).join('');
  app.innerHTML = `
    <div class="phase-nav" role="group" aria-label="产物阶段">
      ${phaseNav}
    </div>
    <div class="summary-grid compact">
      ${metric('产物总数', state.artifacts?.total ?? 0)}
      ${metric('筛选结果', visibleArtifacts.length)}
      ${metric('类型文件夹', groups.length)}
      ${metric('PPTX / PDF', `${countType('pptx')} / ${countExt('.pdf')}`)}
    </div>
    <div class="artifact-layout">
      <div class="artifact-main">
        <div class="panel artifact-browser">
        <div class="panel-head artifact-browser-head">
            <div>
              <h2>产物类型</h2>
              <p>按文件名、路径、类型和步骤筛选；展开后选择文件预览。</p>
            </div>
            <span class="pill">${visibleArtifacts.length} / ${artifacts.length}</span>
          </div>
          ${artifactFilterBar()}
          ${state.selectedArtifact && !selectedVisible ? '<div class="artifact-filter-note">当前预览文件不在筛选结果中；调整筛选条件可重新定位。</div>' : ''}
          <div class="artifact-group-list">
            ${groups.map(artifactGroupHtml).join('') || artifactEmptyState(artifacts.length)}
          </div>
        </div>
        <div class="panel trace-panel">
          <div class="panel-head">
            <div>
              <h2>Trace 事件</h2>
              <p>按 Step、类型和关键词过滤；分页读取避免一次渲染全部日志。</p>
            </div>
          </div>
          ${traceFilterBar()}
          ${state.apiErrors.logs ? errorState('无法读取 Trace 事件', state.apiErrors.logs, true) : logTable(state.logs?.events || [])}
          ${tracePager()}
        </div>
      </div>
      ${artifactDetailPanel()}
    </div>
  `;
}

function qualityEmptyHtml(hasError) {
  return `<section class="hero-panel quality-hero empty-hero">
    <div>
      <span class="eyebrow">质量门禁</span>
      <h2>质量中心</h2>
      <p>${hasError ? '当前未读取到质量报告。可以手动触发受控的 quick harness 检查。' : '还没有质量报告。Dashboard 不会自动运行质量脚本。'}</p>
    </div>
    <div class="hero-stack">
      <strong>${hasError ? '未发现' : '待生成'}</strong>
      <span>${hasError ? escapeHtml(state.apiErrors.quality) : '未发现质量报告'}</span>
      ${actionButton('run-quality')}
    </div>
  </section>
  ${actionStatusPanel('run-quality')}`;
}

function artifactFilterBar() {
  const filters = state.artifactFilters;
  return `<div class="artifact-filters">
    <label class="filter-field search-field">
      <span>搜索文件</span>
      <input
        type="search"
        placeholder="文件名、路径、类型"
        value="${escapeAttr(filters.query)}"
        data-artifact-filter="query"
      >
    </label>
    <label class="filter-field">
      <span>阶段</span>
      <select data-artifact-filter="phase">
        ${artifactPhaseOptions(filters.phase)}
      </select>
    </label>
    <label class="filter-field">
      <span>Step</span>
      <select data-artifact-filter="step">
        ${artifactStepOptions(filters.step)}
      </select>
    </label>
    <label class="filter-field">
      <span>排序</span>
      <select data-artifact-filter="sort">
        ${artifactSortOptions(filters.sort)}
      </select>
    </label>
  </div>`;
}

function artifactPhaseOptions(activePhase) {
  const options = [['all', '全部阶段']];
  for (const [value, label] of [
    ['idea', '制作思路'],
    ['design', '设计契约'],
    ['generate', '生成页面'],
    ['export', '导出成品'],
  ]) {
    options.push([value, label]);
  }
  return options
    .map(([value, label]) => `<option value="${value}"${value === activePhase ? ' selected' : ''}>${label}</option>`)
    .join('');
}

function artifactStepOptions(activeStep) {
  const options = [['all', '全部 Step']];
  for (let step = 1; step <= 8; step += 1) options.push([String(step), `Step ${step}`]);
  return options.map(([value, label]) => `
    <option value="${value}" ${value === activeStep ? 'selected' : ''}>${label}</option>
  `).join('');
}

function artifactSortOptions(activeSort) {
  const options = [
    ['mtime_desc', '修改时间：新到旧'],
    ['mtime_asc', '修改时间：旧到新'],
    ['name_asc', '名称：A-Z'],
    ['size_desc', '大小：大到小'],
  ];
  return options.map(([value, label]) => `
    <option value="${value}" ${value === activeSort ? 'selected' : ''}>${label}</option>
  `).join('');
}

function artifactEmptyState(total) {
  if (!total) return '<div class="empty small">暂无产物。</div>';
  return '<div class="empty small">没有文件符合当前筛选条件。</div>';
}

function traceFilterBar() {
  const filters = state.traceFilters;
  return `<div class="trace-filters">
    <label class="filter-field">
      <span>关键词</span>
      <input type="search" placeholder="详情、路径、错误" value="${escapeAttr(filters.query)}" data-trace-filter="query">
    </label>
    <label class="filter-field">
      <span>Step</span>
      <select data-trace-filter="step">${artifactStepOptions(filters.step)}</select>
    </label>
    <label class="filter-field">
      <span>类型</span>
      <input type="text" placeholder="error,artifact" value="${escapeAttr(filters.type)}" data-trace-filter="type">
    </label>
    <label class="filter-field">
      <span>排序</span>
      <select data-trace-filter="order">
        <option value="desc" ${filters.order === 'desc' ? 'selected' : ''}>新到旧</option>
        <option value="asc" ${filters.order === 'asc' ? 'selected' : ''}>旧到新</option>
      </select>
    </label>
  </div>`;
}

function tracePager() {
  const logs = state.logs || {};
  const offset = Number(logs.offset || 0);
  const limit = Number(logs.limit || state.traceFilters.limit || 80);
  const total = Number(logs.total || 0);
  if (!total) return '';
  return `<div class="trace-pager">
    <span>${offset + 1}-${Math.min(offset + limit, total)} / ${total}</span>
    <button type="button" class="button secondary" data-trace-page="${-limit}" ${offset <= 0 ? 'disabled' : ''}>上一页</button>
    <button type="button" class="button secondary" data-trace-page="${limit}" ${logs.has_more ? '' : 'disabled'}>下一页</button>
  </div>`;
}
function stepCard(step) {
  const subTotal = (step.sub_steps || []).length;
  const gateText = gateSummaryText(step.gate);
  return `
    <a class="step-card ${escapeAttr(step.state)}" href="#/step/${step.step}">
      <div class="step-number">${step.step}</div>
      <div class="step-card-main">
        <div class="step-title-line">
          <h3>${escapeHtml(stepName(step))}</h3>
          ${stateLabel(step.state)}
        </div>
        <p>${step.blocking ? '阻塞确认' : gateText}</p>
        <div class="step-meta">
          <span>${subTotal} 子步骤</span>
        </div>
      </div>
    </a>
  `;
}

function timelineStep(step) {
  return `
    <a class="timeline-step ${escapeAttr(step.state)}" href="#/step/${step.step}" title="查看 Step ${step.step}：${escapeAttr(stepName(step))}">
      <span>${step.step}</span>
      <strong>${escapeHtml(stepName(step))}</strong>
      <small>${statusText(step.state)}</small>
    </a>
  `;
}

function templateRouteLabel(route) {
  const key = route?.route || 'free_design';
  if (key === 'template_applied') return t('template_applied');
  if (key === 'template_expected_missing') return t('template_missing');
  return t('template_free');
}

function templateRoutePanel(route) {
  if (!route) return '';
  const library = route.library || {};
  const counts = library.counts || {};
  const applied = route.applied || {};
  const pending = route.pending_selection;
  return `
    <div class="panel premium-panel template-route-panel">
      <div class="panel-head">
        <div>
          <span class="eyebrow">${escapeHtml(t('template_option'))}</span>
          <h2>${escapeHtml(templateRouteLabel(route))}</h2>
          <p>${escapeHtml(route.reason || '')}</p>
        </div>
        ${stateLabel(route.route === 'template_expected_missing' ? 'failed' : (route.route === 'template_applied' ? 'completed' : 'skipped'))}
      </div>
      <div class="template-route-grid">
        <div>
          <strong>${escapeHtml(t('current_route'))}</strong>
          <span>${escapeHtml(templateRouteLabel(route))}</span>
          ${applied.path ? `<small>${escapeHtml(applied.kind || 'template')} · ${escapeHtml(applied.path)}</small>` : '<small>未应用模板包，系统按自由设计生成。</small>'}
        </div>
        <div>
          <strong>${escapeHtml(t('template_discovery'))}</strong>
          <span>${escapeHtml(String(library.total || 0))} 个可用候选</span>
          <small>Brand ${counts.brand || 0} · Layout ${counts.layout || 0} · Deck ${counts.deck || 0}</small>
        </div>
        <div>
          <strong>逐页 layout</strong>
          <span>不等同于 Step 3 模板包</span>
          <small>layout suggestion 来自 detailed_outline / design_spec / spec_lock；生成前调整走 refine_spec。</small>
        </div>
      </div>
      ${pending ? `<div class="template-pending-note">
        <strong>待处理模板选择</strong>
        <span>${escapeHtml(pending.kind || '')} · ${escapeHtml(pending.path || pending.id || '')}</span>
        <small>必须重新执行 Step 3/4 后才能继续；不会静默套用到当前 spec。</small>
      </div>` : ''}
      ${templateLibraryHtml(library)}
    </div>
  `;
}

function templateLibraryHtml(library) {
  const entries = library?.entries || {};
  const kinds = ['layout', 'deck', 'brand'];
  const cards = kinds.flatMap((kind) => (entries[kind] || []).map((item) => templateCardHtml(item)));
  if (!cards.length) return '';
  return `<div class="template-preview-library">
    <div class="panel-head">
      <div>
        <strong>${escapeHtml(t('template_preview_title'))}</strong>
        <p>${escapeHtml(t('template_preview_desc'))}</p>
      </div>
    </div>
    <div class="template-preview-grid">${cards.join('')}</div>
  </div>`;
}

function templateCardHtml(item) {
  const previews = item.preview_files || [];
  const first = previews[0];
  const desc = item.description_zh || item.description || '';
  const previewPages = previews.map((file) => ({
    name: file.name,
    path: `${item.name_zh || item.name || item.id} · ${file.name}`,
    url: file.url,
  }));
  const previewPagesAttr = escapeAttr(JSON.stringify(previewPages));
  const title = item.name_zh || item.name || item.id;
  return `<article class="template-preview-card">
    <div class="template-card-copy">
      <span class="pill">${escapeHtml(templateKindName(item.kind))}</span>
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(desc)}</p>
      <small>${escapeHtml(item.path || '')}</small>
    </div>
    ${first ? `<button class="template-thumb" type="button" data-template-modal="${escapeAttr(first.url)}" data-template-pages="${previewPagesAttr}" data-template-index="0" data-template-name="${escapeAttr(first.name)}" data-template-title="${escapeAttr(title)}" title="${escapeAttr(first.name)}">
      <img src="${escapeAttr(first.url)}" alt="${escapeAttr(first.name)}">
    </button>` : `<div class="template-thumb empty-thumb">${escapeHtml(t('no_template_preview'))}</div>`}
    ${previews.length > 1 ? `<div class="template-strip">${previews.map((file, index) => `
      <button type="button" data-template-modal="${escapeAttr(file.url)}" data-template-pages="${previewPagesAttr}" data-template-index="${index}" data-template-name="${escapeAttr(file.name)}" data-template-title="${escapeAttr(title)}">${escapeHtml(file.name.replace('.svg', ''))}</button>
    `).join('')}</div>` : ''}
  </article>`;
}

function templateKindName(kind) {
  return {
    brand: '品牌',
    layout: '版式',
    deck: '整套 deck',
  }[kind] || kind || '模板';
}

function gateListHtml(gate) {
  if (!gate?.requirements?.length) return '<div class="empty small">没有 Gate 要求。</div>';
  return `
    <div class="list compact-list">
      ${gate.requirements.map((item) => `
        <div class="list-row">
          <span class="dot ${item.met ? 'ok' : 'warn'}"></span>
          <span>${escapeHtml(gateRequirementLabel(item))}</span>
          <small>${item.detail ? escapeHtml(item.detail) : (item.met ? '已满足' : '待满足')}</small>
        </div>
      `).join('')}
    </div>
  `;
}

function subStepHtml(item) {
  const progress = item.progress == null ? '' : `<div class="progress"><span style="width:${Math.round(item.progress * 100)}%"></span></div>`;
  return `
    <div class="list-row">
      <span class="dot ${escapeAttr(item.state)}"></span>
      <span>${escapeHtml(subStepLabel(item))}</span>
      <small>${escapeHtml(item.detail || statusText(item.state))}</small>
      ${progress}
    </div>
  `;
}

function artifactGroups(items) {
  const groups = new Map();
  for (const item of items) {
    const key = artifactGroupKey(item);
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        label: artifactGroupLabels[key] || artifactTypeLabels[key] || key,
        items: [],
        size: 0,
        folders: new Set(),
      });
    }
    const group = groups.get(key);
    group.items.push(item);
    group.size += item.size_bytes || 0;
    group.folders.add(topFolder(item.path));
  }
  return Array.from(groups.values())
    .map((group) => ({
      ...group,
      folders: Array.from(group.folders).filter(Boolean).sort(),
      items: group.items.sort(sortArtifacts),
    }))
    .sort((a, b) => {
      const ai = artifactTypeOrder.indexOf(a.key);
      const bi = artifactTypeOrder.indexOf(b.key);
      const av = ai === -1 ? 999 : ai;
      const bv = bi === -1 ? 999 : bi;
      return av - bv || a.label.localeCompare(b.label, 'zh-CN');
    });
}

function filteredArtifacts(items) {
  return items
    .filter(matchesArtifactQuery)
    .filter(matchesArtifactStep)
    .filter(matchesArtifactPhase)
    .slice()
    .sort(sortArtifacts);
}

function matchesArtifactQuery(item) {
  const query = state.artifactFilters.query.trim().toLowerCase();
  if (!query) return true;
  const kind = effectivePreviewKind(item);
  const haystack = [
    item.name,
    item.path,
    item.type,
    kind,
    artifactTypeLabels[item.type],
    previewKindLabel(kind),
  ].join(' ').toLowerCase();
  return haystack.includes(query);
}

function matchesArtifactStep(item) {
  const step = state.artifactFilters.step;
  if (step === 'all') return true;
  return String(item.created_by_step || '') === step;
}

function matchesArtifactPhase(item) {
  const phase = state.artifactFilters.phase;
  if (phase === 'all') return true;
  return item.phase === phase;
}

function selectedArtifactVisible(items) {
  const path = state.selectedArtifact?.path;
  if (!path || state.selectedArtifact.loading || state.selectedArtifact.error) return true;
  return items.some((item) => item.path === path);
}
function artifactGroupHtml(group) {
  const open = state.openArtifactGroups.has(group.key);
  const sample = group.items.slice(0, 3).map((item) => item.name).join(' / ');
  return `
    <section class="artifact-group ${open ? 'open' : ''}">
      <button type="button" class="artifact-folder" data-artifact-group="${escapeAttr(group.key)}" aria-expanded="${open}" title="${open ? '收起' : '展开'}${escapeAttr(group.label)}">
        <span class="folder-mark">${escapeHtml(group.label.slice(0, 1))}</span>
        <span class="folder-copy">
          <strong>${escapeHtml(group.label)}</strong>
          <small>${escapeHtml(sample || group.folders.join(' / '))}</small>
        </span>
        <span class="folder-count">${group.items.length}</span>
        <span class="folder-size">${formatBytes(group.size)}</span>
        <span class="folder-action">${open ? '收起' : '展开'}</span>
      </button>
      ${open ? `<div class="artifact-drawer">${group.items.map(artifactFileHtml).join('')}</div>` : ''}
    </section>
  `;
}

function artifactFileHtml(item) {
  const selected = state.selectedArtifact?.path === item.path;
  return `
    <button type="button" class="artifact-file ${selected ? 'selected' : ''}" data-artifact-path="${escapeAttr(item.path)}" aria-pressed="${selected}" title="预览 ${escapeAttr(item.path)}">
      <span class="file-name">${escapeHtml(item.name)}</span>
      <span class="file-path">${escapeHtml(item.path)}</span>
      <span class="file-meta">${formatBytes(item.size_bytes)}${item.modified_at ? ` · ${compactDate(item.modified_at)}` : ''}</span>
    </button>
  `;
}

function artifactTable(items) {
  if (!items.length) return '<div class="empty small">暂无产物。</div>';
  return `
    <div class="table-wrap compact-table">
      <table>
        <thead><tr><th>类型</th><th>名称</th><th>路径</th><th>大小</th></tr></thead>
        <tbody>
          ${items.map((item) => `
            <tr class="artifact-row ${state.selectedArtifact?.path === item.path ? 'selected' : ''}" data-artifact-path="${escapeAttr(item.path)}" title="点击预览">
              <td><span class="pill">${escapeHtml(artifactTypeLabels[item.type] || item.type)}</span></td>
              <td>${escapeHtml(item.name)}</td>
              <td>${escapeHtml(item.path)}</td>
              <td>${formatBytes(item.size_bytes)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

function artifactDetailPanel() {
  const detail = state.selectedArtifact;
  if (!detail) {
    return `<aside class="detail-panel sticky-detail"><h2>文件预览</h2><div class="empty small">从左侧类型文件夹中选择一个文件。</div></aside>`;
  }
  if (detail.loading) {
    return `<aside class="detail-panel sticky-detail"><h2>${escapeHtml(detail.path)}</h2><div class="empty small">正在加载...</div></aside>`;
  }
  if (detail.error) {
    return `<aside class="detail-panel sticky-detail"><h2>文件预览</h2><div class="empty small">${escapeHtml(detail.error)}</div></aside>`;
  }
  const title = `${detail.name} · ${previewKindLabel(effectivePreviewKind(detail))} · ${formatBytes(detail.size_bytes)}`;
  const body = artifactPreviewBody(detail);
  const truncated = detail.truncated ? '<p class="muted">内容较长，预览已截断。</p>' : '';
  return `
    <aside class="detail-panel sticky-detail">
      <div class="panel-head detail-head">
        <div><h2>${escapeHtml(title)}</h2><p>${escapeHtml(detail.path)}</p></div>
        <div class="detail-actions">
          ${canEnlargeArtifact(detail) ? `<button type="button" class="button secondary" data-preview-modal="${escapeAttr(detail.path)}" title="放大预览当前文件">放大预览</button>` : ''}
          <a class="button secondary" href="${escapeAttr(detail.open_url)}" target="_blank" rel="noreferrer" title="在新窗口打开当前文件">打开</a>
        </div>
      </div>
      ${truncated}
      ${body}
    </aside>
  `;
}

function artifactExt(detail) {
  const name = String(detail?.name || detail?.path || '').toLowerCase();
  const dot = name.lastIndexOf('.');
  return dot >= 0 ? name.slice(dot) : '';
}

function artifactGroupKey(item) {
  return item.type || inferTypeFromName(item.name);
}

function inferTypeFromName(name) {
  const text = String(name || '').toLowerCase();
  const dot = text.lastIndexOf('.');
  const ext = dot >= 0 ? text.slice(dot) : '';
  if (ext === '.pdf') return 'pdf';
  if (['.pptx', '.pptm'].includes(ext)) return 'pptx';
  if (['.mp4', '.webm', '.mov', '.mkv'].includes(ext)) return 'video';
  if (['.mp3', '.m4a', '.wav', '.aac', '.ogg'].includes(ext)) return 'audio';
  if (['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'].includes(ext)) return 'image';
  if (ext === '.svg') return 'svg';
  if (ext === '.md') return 'markdown';
  if (ext === '.json') return 'json';
  if (ext === '.jsonl') return 'jsonl';
  if (['.txt', '.csv', '.tsv', '.html', '.css', '.js', '.xml', '.log'].includes(ext)) return 'text';
  if (['.emf', '.wmf'].includes(ext)) return 'binary';
  return 'unknown';
}

function effectivePreviewKind(detail) {
  const ext = artifactExt(detail);
  if (detail.preview_kind && detail.preview_kind !== 'binary' && detail.preview_kind !== 'unknown') return detail.preview_kind;
  if (['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'].includes(ext)) return 'image';
  if (ext === '.svg') return 'svg';
  if (ext === '.pdf') return 'pdf';
  if (['.mp3', '.m4a', '.wav', '.aac', '.ogg'].includes(ext)) return 'audio';
  if (['.mp4', '.webm', '.mov', '.mkv'].includes(ext)) return 'video';
  if (['.pptx', '.pptm'].includes(ext)) return 'pptx';
  if (ext === '.md') return 'markdown';
  if (ext === '.json') return 'json';
  if (ext === '.jsonl') return 'jsonl';
  if (['.txt', '.csv', '.tsv', '.html', '.css', '.js', '.xml', '.log'].includes(ext)) return 'text';
  if (['.emf', '.wmf'].includes(ext)) return 'binary';
  return detail.preview_kind || inferTypeFromName(detail.name || detail.path);
}

function previewKindLabel(kind) {
  const labels = {
    image: '图片',
    svg: 'SVG',
    pdf: 'PDF',
    audio: '音频',
    video: '视频',
    pptx: 'PPTX',
    markdown: 'Markdown',
    json: 'JSON',
    jsonl: 'JSONL',
    text: '文本',
    binary: '二进制',
    unknown: '未知类型',
  };
  return labels[kind] || kind;
}

function svgPreviewPages(detail) {
  const related = detail.related?.svg_pages;
  if (related && related.length) return related;
  const artifacts = state.artifacts?.artifacts || [];
  const draftPages = artifacts.filter((item) => artifactDirectory(item.path) === 'svg_output');
  const finalPages = artifacts.filter((item) => artifactDirectory(item.path) === 'svg_final');
  const pages = draftPages.length ? draftPages : finalPages;
  return pages
    .sort((a, b) => a.path.localeCompare(b.path, undefined, { numeric: true }))
    .map((item) => ({ name: item.name, path: item.path, url: `/artifact-file/${item.path}` }));
}
function canEnlargeArtifact(detail) {
  const kind = effectivePreviewKind(detail);
  return kind === 'svg' || kind === 'pptx' || kind === 'pdf';
}

function previewModalPages(detail) {
  if (!detail) return [];
  const kind = effectivePreviewKind(detail);
  if (kind === 'pptx') return svgPreviewPages(detail);
  if (kind === 'svg') {
    const detailDir = artifactDirectory(detail.path);
    const pages = (state.artifacts?.artifacts || [])
      .filter((item) => artifactDirectory(item.path) === detailDir && effectivePreviewKind(item) === 'svg')
      .sort((a, b) => a.path.localeCompare(b.path, undefined, { numeric: true }))
      .map((item) => ({ name: item.name, path: item.path, url: `/artifact-file/${item.path}` }));
    return pages.length ? pages : [{ name: detail.name, path: detail.path, url: detail.open_url }];
  }
  return [{ name: detail.name, path: detail.path, url: detail.open_url }];
}

function artifactPreviewBody(detail) {
  const kind = effectivePreviewKind(detail);
  if (kind === 'image') {
    return `<img class="artifact-image" src="${escapeAttr(detail.open_url)}" alt="${escapeAttr(detail.name)}">`;
  }
  if (kind === 'svg') {
    return `<div class="preview-shell">
      <iframe class="artifact-frame" src="${escapeAttr(detail.open_url)}" title="${escapeAttr(detail.name)}"></iframe>
    </div>
      <pre>${escapeHtml(detail.content || '')}</pre>`;
  }
  if (kind === 'pdf') {
    return `<iframe class="artifact-frame tall" src="${escapeAttr(detail.open_url)}" title="${escapeAttr(detail.name)}"></iframe>`;
  }
  if (kind === 'audio') {
    return `<audio class="artifact-media" controls src="${escapeAttr(detail.open_url)}"></audio>`;
  }
  if (kind === 'video') {
    return `<video class="artifact-media" controls src="${escapeAttr(detail.open_url)}"></video>`;
  }
  if (kind === 'pptx') {
    const pages = svgPreviewPages(detail);
    if (!pages.length) {
      return `<div class="empty small">浏览器不能直接渲染 PPTX，也没有找到对应的 SVG 页面。</div>`;
    }
    return `<div class="deck-preview">
      <div class="preview-shell">
        <iframe class="artifact-frame" src="${escapeAttr(pages[0].url)}" title="${escapeAttr(pages[0].name)}"></iframe>
      </div>
      <div class="deck-strip">
        ${pages.map((page, index) => `<a href="${escapeAttr(page.url)}" target="_blank" rel="noreferrer">${index + 1}</a>`).join('')}
      </div>
      <p class="muted">PPTX 预览使用生成的 SVG 页面；点击“打开”可打开原生 PPTX。</p>
    </div>`;
  }
  if (['markdown', 'json', 'jsonl', 'text'].includes(kind)) {
    return `<pre>${escapeHtml(detail.content || '')}</pre>`;
  }
  return `<div class="binary-preview">
    <strong>${escapeHtml(detail.name)}</strong>
    <p>浏览器没有可嵌入的原生预览器。请使用右上角“打开”在浏览器或系统应用中查看。</p>
  </div>`;
}

function artifactDirectory(path) {
  return String(path || '').split('/')[0] || '';
}

function logTable(events) {
  if (!events.length) return '<div class="empty small">暂无 trace 事件。</div>';
  return `
    <div class="table-wrap compact-table">
      <table>
        <thead><tr><th>时间</th><th>类型</th><th>详情</th></tr></thead>
        <tbody>
          ${events.map((event) => `
            <tr>
              <td>${escapeHtml(event.ts || '')}</td>
              <td><span class="pill">${escapeHtml(event.type || '')}</span></td>
              <td>${escapeHtml(event.detail || '')}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

function servicePanel(service, label, actionText, action = '') {
  const diagnostics = serviceDiagnostics(service);
  if (service?.running && service.url) {
    return `<div class="service-card running">
      <div>
        <strong>${escapeHtml(label)} 正在运行</strong>
        <p>${escapeHtml(service.url)} · pid ${escapeHtml(service.pid || '-')} · port ${escapeHtml(service.port || '-')}</p>
        ${diagnostics}
      </div>
      <a class="button" href="${escapeAttr(service.url)}" target="_blank" rel="noreferrer" title="${escapeAttr(actionText)}">${escapeHtml(actionText)}</a>
    </div>`;
  }
  return `<div class="service-card stopped">
    <div>
      <strong>${escapeHtml(label)} 未运行</strong>
      <p>${escapeHtml(serviceNextActionText(service?.next_action))}</p>
      ${diagnostics}
    </div>
    ${action ? actionButton(action) : ''}
  </div>`;
}

function serviceStatusText(service) {
  if (service?.running) return '运行中';
  if (service?.stale_lock) return '锁已过期';
  if (service?.project_matches === false) return '项目不匹配';
  return '未运行';
}

function serviceDiagnostics(service) {
  if (!service) return '';
  const rows = [];
  if (service.lock_path) rows.push(`lock ${compactPath(service.lock_path)}`);
  if (service.lock_age_seconds !== null && service.lock_age_seconds !== undefined) {
    rows.push(`age ${formatAge(service.lock_age_seconds)}`);
  }
  if (service.stale_lock) rows.push('stale lock');
  if (service.project_matches === false) rows.push('project mismatch');
  if (service.last_result_file?.path) rows.push(`result ${service.last_result_file.path}`);
  if (service.last_annotation_file?.path) rows.push(`annotations ${service.last_annotation_file.path}`);
  if (service.last_update_file?.path) rows.push(`edits ${service.last_update_file.path}`);
  if (service.log_path) rows.push(`log ${compactPath(service.log_path)}`);
  return rows.length ? `<p class="service-diagnostics">${escapeHtml(rows.join(' · '))}</p>` : '';
}

function serviceNextActionText(action) {
  return {
    open_confirm_ui: '打开 Confirm UI 完成或查看确认。',
    review_confirm_result: '已有确认结果，可查看 result.json。',
    start_confirm_ui: '建议启动 Confirm UI。',
    restart_confirm_ui: '存在过期锁，建议重新启动确认页。',
    prepare_confirm_recommendations: '等待 Step 4 生成确认建议。',
    review_live_preview_changes_after_export: '已有预览注解或编辑，导出后按 Live Preview workflow 处理。',
    open_live_preview: '打开实时预览继续查看。',
    restart_live_preview: '存在过期锁，建议重新启动实时预览。',
    start_live_preview: '建议启动实时预览。',
    open_dashboard: '当前 Dashboard 就是统一入口。',
    start_dashboard: 'Dashboard 未运行时按 Step 2 命令启动。',
  }[action] || '对应工作流启动后，这里会显示可打开的入口。';
}

function compactPath(path) {
  const text = String(path || '').replaceAll('\\', '/');
  const parts = text.split('/');
  return parts.slice(-3).join('/');
}

function formatAge(seconds) {
  const value = Number(seconds || 0);
  if (value < 60) return `${value}s`;
  if (value < 3600) return `${Math.floor(value / 60)}m`;
  return `${Math.floor(value / 3600)}h`;
}

function actionButton(action) {
  const current = state.actionStatus[action];
  const running = current?.status === 'running';
  return `<button
    type="button"
    class="button ${running ? 'disabled' : ''}"
    data-action-run="${escapeAttr(action)}"
    ${running ? 'disabled' : ''}
    title="${escapeAttr(actionHelp(action))}"
  >${escapeHtml(running ? '运行中...' : actionLabel(action))}</button>`;
}

function actionLabel(action) {
  return {
    'start-confirm': '启动确认页',
    'start-preview': '启动实时预览',
    'run-quality': '运行质量检查',
  }[action] || action;
}

function actionHelp(action) {
  return {
    'start-confirm': '将通过 POST + confirm:true 启动 Confirm UI 辅助服务。',
    'start-preview': '将通过 POST + confirm:true 启动 Live Preview 辅助服务。',
    'run-quality': '将通过 POST + confirm:true 运行 quick harness 质量检查。',
  }[action] || '执行受控 Dashboard 动作。';
}

function actionStatusPanel(action) {
  const item = state.actionStatus[action];
  if (!item) return '';
  const status = item.status || 'unknown';
  const detail = item.url || item.stderr_tail || item.stdout_tail || item.command_preview || '';
  return `<div class="action-status ${escapeAttr(status)}">
    <strong>${escapeHtml(actionLabel(action))}：${escapeHtml(actionStatusText(status))}</strong>
    ${detail ? `<pre>${escapeHtml(String(detail))}</pre>` : ''}
  </div>`;
}

function actionStatusText(status) {
  return {
    running: '运行中',
    done: '完成',
    failed: '失败',
    existing: '已在运行',
    unknown: '未知',
  }[status] || status;
}

function healthBadge(status) {
  const normalized = String(status || 'unknown').toLowerCase();
  return `<span class="health-badge ${escapeAttr(normalized)}">${escapeHtml(healthStatusText(normalized))}</span>`;
}

function healthStatusText(status) {
  return {
    healthy: '健康',
    warn: '有警告',
    blocked: '阻塞',
    unknown: '未知',
  }[String(status || 'unknown').toLowerCase()] || '未知';
}

function healthReasons(health) {
  const reasons = health?.reasons || [];
  if (!reasons.length) return '<div class="empty small">暂无健康度说明。</div>';
  return `<div class="health-reasons">
    ${reasons.map((item) => `<div class="status-row"><span class="dot ${escapeAttr(health.status || 'unknown')}"></span><span>${escapeHtml(item)}</span><small>${escapeHtml(healthStatusText(health.status))}</small></div>`).join('')}
  </div>`;
}

function legacyQualityChecks(harness) {
  return [
    { id: 'spec_compliance', label: '规格一致性', status: normalizeQualityStatus(harness.spec_compliance) },
    { id: 'svg_quality', label: 'SVG 质量', status: normalizeQualityStatus(harness.svg_quality) },
    { id: 'e2e', label: 'E2E 验证', status: normalizeQualityStatus(harness.e2e) },
    { id: 'visual_review', label: '视觉回看', status: normalizeQualityStatus(harness.visual_review) },
  ];
}

function checkStatus(checks, id) {
  return (checks || []).find((item) => item.id === id)?.status || 'unknown';
}

function normalizeQualityStatus(value) {
  const normalized = String(value || '').toLowerCase();
  if (['pass', 'passed', 'ok', 'clean'].includes(normalized)) return 'pass';
  if (['warn', 'warning', 'warnings', 'pass_with_warnings'].includes(normalized)) return 'warn';
  if (['fail', 'failed', 'error', 'blocked'].includes(normalized)) return 'fail';
  return 'unknown';
}

function qualityStatusText(value) {
  return {
    pass: '通过',
    warn: '有警告',
    fail: '失败',
    unknown: '未知',
  }[normalizeQualityStatus(value)] || '未知';
}

function qualityMetric(label, status) {
  const normalized = normalizeQualityStatus(status);
  return `<div class="metric quality-metric ${escapeAttr(normalized)}">
    <span>${escapeHtml(label)}</span>
    <strong>${escapeHtml(qualityStatusText(normalized))}</strong>
  </div>`;
}

function qualityCheckMatrix(checks) {
  if (!checks?.length) return '<div class="empty small">未发现检查项。</div>';
  return `<div class="quality-check-grid">
    ${checks.map((item) => {
      const status = normalizeQualityStatus(item.status);
      const updated = item.updated_at ? compactDate(item.updated_at) : '未发现报告';
      return `<div class="quality-check ${escapeAttr(status)}">
        <div>
          <strong>${escapeHtml(item.label || item.id)}</strong>
          <small>${escapeHtml(item.source_file || '无报告文件')}</small>
        </div>
        <span class="quality-status ${escapeAttr(status)}">${escapeHtml(qualityStatusText(status))}</span>
        <em>${escapeHtml(updated)}</em>
        ${item.parse_warning ? `<p>${escapeHtml(item.parse_warning)}</p>` : ''}
      </div>`;
    }).join('')}
  </div>`;
}

function qualityDiagnosticsPanel(diagnostics) {
  const failed = diagnostics.failed_scripts || [];
  const reports = diagnostics.report_files || [];
  const commands = diagnostics.recommended_commands || [];
  const details = diagnostics.failed_details || [];
  if (!failed.length && !reports.length && !diagnostics.final_export_path) return '';
  return `<div class="panel premium-panel quality-panel">
    <span class="eyebrow">失败诊断</span>
    <h2>诊断摘要</h2>
    <div class="status-list rich-list">
      ${statusRow('最近报告', !!diagnostics.latest_check, diagnostics.latest_check?.source_file || '未发现')}
      ${statusRow('失败阶段', !failed.length, failed.join(', ') || '无失败')}
      ${statusRow('最终导出', !!diagnostics.final_export_path, diagnostics.final_export_path || '未导出')}
    </div>
    ${diagnostics.error_summary ? `<p class="diagnostic-summary">${escapeHtml(diagnostics.error_summary)}</p>` : ''}
    ${details.length ? `<div class="quality-issue-list">${details.map(qualityFailedDetailCard).join('')}</div>` : ''}
    ${commands.length ? `<pre>${escapeHtml(commands.slice(0, 3).join('\n'))}</pre>` : ''}
    ${reports.length ? `<small>${escapeHtml(reports.map((item) => item.source_file).join(' · '))}</small>` : ''}
  </div>`;
}

function qualityFailedDetailCard(item) {
  const text = item.stderr || item.stdout || '未提供输出。';
  return `<article class="quality-issue must_fix">
    <div class="quality-issue-top">
      <span class="quality-severity">失败</span>
      <strong>${escapeHtml(item.check || '质量检查')}</strong>
    </div>
    <p>${escapeHtml(text)}</p>
    <div class="quality-issue-meta">
      <span>${escapeHtml(item.command || '')}</span>
      <span>${escapeHtml(String(item.returncode ?? ''))}</span>
    </div>
  </article>`;
}

function qualityIssueSection(group, label, items) {
  const count = items.length;
  return `<div class="panel premium-panel quality-issue-panel ${escapeAttr(group)}">
    <div class="panel-head">
      <div>
        <span class="eyebrow">${escapeHtml(qualityGroupLabel(group))}</span>
        <h2>${escapeHtml(label)}</h2>
      </div>
      <span class="quality-count">${count}</span>
    </div>
    <div class="quality-issue-list">
      ${count ? items.map((item) => qualityIssueCard(item, group)).join('') : '<div class="empty small">没有记录。</div>'}
    </div>
  </div>`;
}

function qualityIssueCard(item, group) {
  const path = item.path || '';
  const pathHtml = path
    ? `<a href="#/artifacts" data-artifact-jump="1" data-artifact-path="${escapeAttr(path)}">${escapeHtml(path)}</a>`
    : '<span>未关联产物</span>';
  return `<article class="quality-issue ${escapeAttr(group)}">
    <div class="quality-issue-top">
      <span class="quality-severity">${escapeHtml(qualitySeverityText(item.severity || group))}</span>
      <strong>${escapeHtml(item.check || '质量检查')}</strong>
    </div>
    <p>${escapeHtml(item.message || '未提供详情')}</p>
    ${item.recommendation ? `<small>${escapeHtml(item.recommendation)}</small>` : ''}
    <div class="quality-issue-meta">
      ${pathHtml}
      <span>${escapeHtml(item.source_file || '')}</span>
    </div>
  </article>`;
}

function qualityGroupLabel(group) {
  return {
    must_fix: '必须修复',
    should_fix: '建议修复',
    accepted_risks: '已接受风险',
  }[group] || group;
}

function qualitySeverityText(value) {
  return {
    must_fix: '必须修复',
    should_fix: '建议修复',
    accepted_risks: '已接受风险',
    error: '错误',
    warning: '警告',
    info: '信息',
  }[value] || value || '未知';
}

function errorState(title, detail, compact = false) {
  return `<div class="empty ${compact ? 'small' : ''} error-state">
    <strong>${escapeHtml(title)}</strong>
    <p>${escapeHtml(detail || '请求失败，请稍后重试。')}</p>
    <button type="button" class="button secondary" data-refresh="true" title="重新读取 Dashboard 数据">重试</button>
  </div>`;
}

function statusRow(label, ok, detail = '') {
  return `
    <div class="status-row">
      <span class="dot ${ok ? 'ok' : 'warn'}"></span>
      <span>${escapeHtml(label)}</span>
      <small>${escapeHtml(detail || (ok ? '已存在' : '未找到'))}</small>
    </div>
  `;
}

function metric(label, value) {
  return `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`;
}

function applyStaticI18n() {
  document.documentElement.lang = state.language === 'en' ? 'en' : 'zh-CN';
  document.querySelectorAll('[data-i18n]').forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  const langToggle = document.getElementById('langToggle');
  if (langToggle) langToggle.textContent = state.language === 'zh' ? '中文 / EN' : 'EN / 中文';
}

function routeTitle(name) {
  const keys = {
    pipeline: 'route_pipeline',
    services: 'route_services',
    step: 'route_step',
    confirm: 'route_confirm',
    preview: 'route_preview',
    quality: 'route_quality',
    artifacts: 'route_artifacts',
  };
  return t(keys[name] || 'route_pipeline');
}

function stepName(step) {
  if (!step) return '';
  return state.language === 'en'
    ? (step.name_en || step.name || step.name_zh || '')
    : (step.name_zh || step.name || step.name_en || '');
}

function subStepLabel(item) {
  if (!item) return '';
  return state.language === 'en'
    ? (item.label_en || item.label || item.label_zh || '')
    : (item.label_zh || item.label || item.label_en || '');
}

function gateRequirementLabel(item) {
  if (!item) return '';
  return state.language === 'en'
    ? (item.label_en || item.label || item.label_zh || '')
    : (item.label_zh || item.label || item.label_en || '');
}

function stateLabel(value) {
  return `<span class="status ${escapeAttr(value)}">${escapeHtml(statusText(value))}</span>`;
}

function statusText(value) {
  return statusLabels[value] || value || '未知';
}

function stepState(stepNo, subId) {
  const step = state.pipeline.steps.find((item) => item.step === stepNo);
  const sub = step?.sub_steps.find((item) => item.id === subId);
  return sub ? statusText(sub.state) : '待处理';
}

function countType(type) {
  return state.artifacts?.by_type?.[type] || 0;
}

function countExt(ext) {
  const lower = ext.toLowerCase();
  return (state.artifacts?.artifacts || []).filter((item) => item.name.toLowerCase().endsWith(lower)).length;
}

function countMedia() {
  return (state.artifacts?.artifacts || []).filter((item) => {
    const kind = effectivePreviewKind(item);
    return ['image', 'audio', 'video', 'pdf', 'pptx'].includes(kind);
  }).length;
}

function hasArtifactPath(path) {
  return (state.artifacts?.artifacts || []).some((item) => item.path === path || item.path.endsWith(`/${path}`));
}

function completedSubSteps(step) {
  return (step.sub_steps || []).filter((item) => item.state === 'completed').length;
}

function gateSummaryText(gate) {
  const total = gate?.requirements?.length || 0;
  if (!total) return '无 Gate';
  const met = gate.requirements.filter((item) => item.met).length;
  return `${met} / ${total} 已满足`;
}

function sortArtifacts(a, b) {
  const sort = state.artifactFilters.sort;
  if (sort === 'mtime_asc') return compareMtime(a, b, 1);
  if (sort === 'name_asc') return a.name.localeCompare(b.name, 'zh-CN', { numeric: true }) || compareMtime(a, b, -1);
  if (sort === 'size_desc') return (b.size_bytes || 0) - (a.size_bytes || 0) || compareMtime(a, b, -1);
  return compareMtime(a, b, -1);
}

function compareMtime(a, b, direction) {
  const am = Date.parse(a.modified_at || '') || 0;
  const bm = Date.parse(b.modified_at || '') || 0;
  if (am !== bm) return (am - bm) * direction;
  return a.path.localeCompare(b.path, undefined, { numeric: true });
}

function topFolder(path) {
  return String(path || '').split('/')[0] || '';
}

function compactDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatBytes(value) {
  if (value == null) return '';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll('`', '&#096;');
}











