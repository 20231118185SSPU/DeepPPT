(function () {
  function renderLayoutPreviewPanel() {
    const preview = window.dashboardState?.layoutPreview;
    if (!preview || !preview.available || !Array.isArray(preview.pages) || !preview.pages.length) {
      return `
        <div class="panel premium-panel layout-preview-panel">
          <span class="eyebrow">页面布局</span>
          <h2>逐页布局预览</h2>
          <div class="empty small">spec_lock.md 尚未提供 page_rhythm / page_layouts，或当前项目还没有可预览页面。</div>
        </div>
      `;
    }
    const cards = preview.pages.map(layoutPreviewCard).join('');
    return `
      <div class="template-preview-library layout-preview-panel">
        <div class="panel-head">
          <div>
            <strong>逐页布局预览</strong>
            <p>${escapeHtml(preview.generated_count || 0)} 页已生成预览，${escapeHtml(preview.template_count || 0)} 页显示模板参考。点击缩略图放大查看。</p>
          </div>
          <span class="layout-preview-count">${escapeHtml(preview.page_count || preview.pages.length)} 页</span>
        </div>
        <div class="template-preview-grid">${cards}</div>
      </div>
    `;
  }

  function layoutPreviewCard(page) {
    const source = page.source || {};
    const hasPreview = Boolean(source.url);
    const kind = source.kind || 'free_design';
    const label = layoutSourceLabel(kind);

    // Thumb: use img for rendered PNGs, styled div for SVG/templates
    let thumbHtml;
    if (!hasPreview) {
      thumbHtml = `<div class="template-thumb empty-thumb">自由设计</div>`;
    } else if (kind === 'rendered_png') {
      thumbHtml = `<button type="button" class="template-thumb" data-layout-modal="${escapeAttr(source.url)}" data-layout-title="${escapeAttr(page.page || '')} ${escapeAttr(label)}" title="放大查看 ${escapeAttr(page.page || '')}">
        <img src="${escapeAttr(source.url)}" alt="${escapeAttr(page.page || '')} ${escapeAttr(label)}" loading="lazy">
      </button>`;
    } else {
      // SVG/template: show as styled preview
      thumbHtml = `<button type="button" class="template-thumb layout-svg-thumb" data-layout-modal="${escapeAttr(source.url)}" data-layout-title="${escapeAttr(page.page || '')} ${escapeAttr(label)}" title="放大查看 ${escapeAttr(page.page || '')}">
        <span class="layout-svg-label">${escapeHtml(label)}</span>
      </button>`;
    }

    // Meta tags
    const metaTags = [];
    if (page.rhythm) metaTags.push(page.rhythm);
    if (page.type) metaTags.push(page.type);
    if (page.layout) metaTags.push(page.layout);
    if (page.chart) metaTags.push(page.chart);

    return `
      <article class="template-preview-card layout-preview-card ${escapeAttr(kind)}">
        <div class="template-card-copy">
          <span class="pill">${escapeHtml(label)}</span>
          <strong>${escapeHtml(page.page || '')}</strong>
          ${metaTags.length ? `<div class="layout-preview-meta">${metaTags.map(t => `<span>${escapeHtml(t)}</span>`).join('')}</div>` : ''}
          ${page.notes ? `<p>${escapeHtml(page.notes)}</p>` : ''}
        </div>
        ${thumbHtml}
      </article>
    `;
  }

  function layoutSourceLabel(kind) {
    return {
      rendered_png: '截图',
      svg_final: '成品 SVG',
      svg_output: '生成 SVG',
      layout_template: '模板',
      chart_template: '图表模板',
      free_design: '自由设计',
    }[kind] || '预览';
  }

  // Click handler for layout modal — delegated to document
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-layout-modal]');
    if (btn) {
      e.preventDefault();
      openLayoutModal(btn.dataset.layoutModal, btn.dataset.layoutTitle);
      return;
    }
    const overlay = e.target.closest('.layout-modal-overlay');
    if (overlay && e.target === overlay) {
      closeLayoutModal();
    }
  });

  // ESC to close
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeLayoutModal();
  });

  function openLayoutModal(url, title) {
    // Reuse existing modal infrastructure if available
    const modal = document.getElementById('layout-preview-modal');
    if (!modal) return;
    const frame = document.getElementById('layout-modal-frame');
    const titleEl = document.getElementById('layout-modal-title');
    if (titleEl) titleEl.textContent = title || '布局预览';
    if (frame) frame.src = url;
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
  }

  function closeLayoutModal() {
    const modal = document.getElementById('layout-preview-modal');
    if (!modal) return;
    modal.style.display = 'none';
    const frame = document.getElementById('layout-modal-frame');
    if (frame) frame.src = '';
    document.body.classList.remove('modal-open');
  }

  window.closeLayoutModal = closeLayoutModal;
  window.renderLayoutPreviewPanel = renderLayoutPreviewPanel;
})();
