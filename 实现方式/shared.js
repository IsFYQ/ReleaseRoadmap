/**
 * 发版路线图 · 运营/管理后台共享工具
 */
(function (window) {
  'use strict';

  const API = '';

  async function apiGet(path) {
    const r = await fetch(API + path);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const j = await r.json();
    if (j.code !== 'OK') throw new Error(j.message || '请求失败');
    return j.data;
  }

  async function apiSend(method, path, body) {
    const opt = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opt.body = JSON.stringify(body);
    const r = await fetch(API + path, opt);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const j = await r.json();
    if (j.code !== 'OK') throw new Error(j.message || '请求失败');
    return j.data;
  }

  function esc(s) {
    return (s == null ? '' : String(s))
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function typeClass(type) {
    return type === '新增' ? 'add' : type === '优化' ? 'opt' : 'fix';
  }

  function typeOrder(type) {
    return type === '新增' ? 1 : type === '优化' ? 2 : 3;
  }

  function todayStr() {
    return new Date().toISOString().slice(0, 10);
  }

  const CONSTANTS = {
    RELEASE_TYPES: ['新增', '优化', '修复'],
    TARGET_USERS: ['全部', '作业', '教辅'],
    MODULES: { base: '底座', resource: '资源应用' },
    DEFAULT_PRODUCT_LINE: '闻道作业',
    PAGE_SIZE: 20,
  };

  const AppToast = {
    _wrap: null,
    init() {
      if (this._wrap) return;
      this._wrap = document.createElement('div');
      this._wrap.className = 'app-toast-wrap';
      document.body.appendChild(this._wrap);
    },
    show(msg, type, duration) {
      this.init();
      type = type || 'info';
      duration = duration == null ? 3200 : duration;
      const el = document.createElement('div');
      el.className = 'app-toast ' + type;
      el.textContent = msg;
      this._wrap.appendChild(el);
      setTimeout(function () {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.2s';
        setTimeout(function () { el.remove(); }, 220);
      }, duration);
    },
    success(msg) { this.show(msg, 'success'); },
    error(msg) { this.show(msg, 'error', 5000); },
    warn(msg) { this.show(msg, 'warn', 4000); },
    info(msg) { this.show(msg, 'info'); },
  };

  const AppConfirm = {
    _overlay: null,
    _resolve: null,
    init() {
      if (this._overlay) return;
      const ov = document.createElement('div');
      ov.className = 'app-confirm-overlay';
      ov.id = 'app-confirm-overlay';
      ov.innerHTML =
        '<div class="app-confirm-box" onclick="event.stopPropagation()">' +
          '<div class="ac-title" id="app-confirm-title">确认</div>' +
          '<div class="ac-body" id="app-confirm-body"></div>' +
          '<div class="ac-footer">' +
            '<button type="button" class="btn" id="app-confirm-cancel">取消</button>' +
            '<button type="button" class="btn btn-primary" id="app-confirm-ok">确定</button>' +
          '</div>' +
        '</div>';
      document.body.appendChild(ov);
      ov.addEventListener('click', function () { AppConfirm._finish(false); });
      document.getElementById('app-confirm-cancel').addEventListener('click', function () { AppConfirm._finish(false); });
      document.getElementById('app-confirm-ok').addEventListener('click', function () { AppConfirm._finish(true); });
      this._overlay = ov;
    },
    ask(message, opts) {
      opts = opts || {};
      this.init();
      return new Promise(function (resolve) {
        AppConfirm._resolve = resolve;
        document.getElementById('app-confirm-title').textContent = opts.title || '确认';
        document.getElementById('app-confirm-body').textContent = message;
        const okBtn = document.getElementById('app-confirm-ok');
        okBtn.textContent = opts.confirmText || '确定';
        okBtn.className = opts.danger ? 'btn btn-warn' : 'btn btn-primary';
        document.getElementById('app-confirm-cancel').style.display = '';
        AppConfirm._overlay.classList.add('show');
      });
    },
    _finish(ok) {
      this._overlay.classList.remove('show');
      document.getElementById('app-confirm-cancel').style.display = '';
      if (this._resolve) { this._resolve(!!ok); this._resolve = null; }
    },
    info(message, opts) {
      opts = opts || {};
      this.init();
      return new Promise(function (resolve) {
        AppConfirm._resolve = resolve;
        document.getElementById('app-confirm-title').textContent = opts.title || '提示';
        document.getElementById('app-confirm-body').textContent = message;
        const okBtn = document.getElementById('app-confirm-ok');
        okBtn.textContent = opts.confirmText || '知道了';
        okBtn.className = 'btn btn-primary';
        document.getElementById('app-confirm-cancel').style.display = 'none';
        AppConfirm._overlay.classList.add('show');
      });
    },
  };

  async function withLoading(btn, fn) {
    if (!btn) return fn();
    const orig = btn.textContent;
    btn.disabled = true;
    btn.classList.add('is-loading');
    btn.textContent = '处理中…';
    try { return await fn(); }
    finally {
      btn.disabled = false;
      btn.classList.remove('is-loading');
      btn.textContent = orig;
    }
  }

  function paginate(list, page, pageSize) {
    const total = list.length;
    const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);
    const p = Math.min(Math.max(1, page), totalPages);
    return {
      items: list.slice((p - 1) * pageSize, p * pageSize),
      page: p,
      totalPages: totalPages,
      total: total,
      pageSize: pageSize,
    };
  }

  function renderPaginationBar(containerId, result, goFnName) {
    const box = document.getElementById(containerId);
    if (!box) return;
    if (result.total <= result.pageSize) {
      box.innerHTML = result.total ? '<span class="pg-info">共 ' + result.total + ' 条</span>' : '';
      return;
    }
    const pages = [];
    const tp = result.totalPages;
    const cur = result.page;
    for (let i = 1; i <= tp; i++) {
      if (i === 1 || i === tp || (i >= cur - 2 && i <= cur + 2)) pages.push(i);
      else if (pages[pages.length - 1] !== '…') pages.push('…');
    }
    let html = '<span class="pg-info">共 ' + result.total + ' 条 · 第 ' + cur + '/' + tp + ' 页</span><div class="pg-btns">';
    html += '<button type="button" class="pg-btn" ' + (cur <= 1 ? 'disabled' : '') + ' onclick="' + goFnName + '(' + (cur - 1) + ')">上一页</button>';
    pages.forEach(function (n) {
      if (n === '…') html += '<span style="padding:0 4px">…</span>';
      else html += '<button type="button" class="pg-btn' + (n === cur ? ' active' : '') + '" onclick="' + goFnName + '(' + n + ')">' + n + '</button>';
    });
    html += '<button type="button" class="pg-btn" ' + (cur >= tp ? 'disabled' : '') + ' onclick="' + goFnName + '(' + (cur + 1) + ')">下一页</button></div>';
    box.innerHTML = html;
  }

  function initMobileNav() {
    const topbar = document.querySelector('.topbar');
    const sidebar = document.querySelector('.sidebar');
    if (!topbar || !sidebar) return;
    if (!document.getElementById('mobile-nav-backdrop')) {
      const bd = document.createElement('div');
      bd.id = 'mobile-nav-backdrop';
      bd.className = 'mobile-nav-backdrop';
      bd.addEventListener('click', closeSidebar);
      document.body.appendChild(bd);
    }
    let btn = document.getElementById('mobile-nav-toggle');
    if (!btn) {
      btn = document.createElement('button');
      btn.id = 'mobile-nav-toggle';
      btn.className = 'mobile-nav-toggle';
      btn.type = 'button';
      btn.setAttribute('aria-label', '打开菜单');
      btn.textContent = '☰';
      const logo = topbar.querySelector('.logo');
      if (logo && logo.nextSibling) topbar.insertBefore(btn, logo.nextSibling);
      else topbar.insertBefore(btn, topbar.firstChild);
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        sidebar.classList.toggle('open');
        document.body.classList.toggle('sidebar-open');
      });
    }
    document.querySelectorAll('.nav-item').forEach(function (el) {
      el.addEventListener('click', function () {
        if (window.innerWidth <= 900) closeSidebar();
      });
    });
  }

  function closeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.remove('open');
    document.body.classList.remove('sidebar-open');
  }

  AppToast.init();
  AppConfirm.init();

  window.API = API;
  window.apiGet = apiGet;
  window.apiSend = apiSend;
  window.esc = esc;
  window.typeClass = typeClass;
  window.typeOrder = typeOrder;
  window.todayStr = todayStr;
  window.AppToast = AppToast;
  window.AppConfirm = AppConfirm;
  window.withLoading = withLoading;
  window.paginate = paginate;
  window.renderPaginationBar = renderPaginationBar;
  window.initMobileNav = initMobileNav;
  window.CONSTANTS = CONSTANTS;
  window.toast = AppToast;

})(window);
