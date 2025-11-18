(function(){
  const SDK_NAME = 'TGOWidget';
  const UI_IFRAME_NAME = 'tgo-ui-frame';
  const UI_CONTAINER_ID = 'tgo-ui-container';
  const CTRL_IFRAME_NAME = 'tgo-controller-frame';
  const READY_TIMEOUT = 8000; // ms, fallback if UI load takes too long
  let __tgo_lastInstance = null; // holds latest injected instance (show/hide)

  // ------- Utilities -------
  function getCurrentScript(){
    const cs = document.currentScript; if(cs) return cs;
    const scripts = document.getElementsByTagName('script');
    for(let i=scripts.length-1;i>=0;i--){
      const s = scripts[i]; const src = (s.getAttribute('src')||'');
      if(src.includes('tgo-widget-sdk.js') || src.includes('/widget.js') || /(?:^|[\\/])widget\.js(?:[?#]|$)/.test(src)) return s;
    }
    return null;
  }

  function dirnameFromScript(script){
    try {
      const abs = new URL(script && script.getAttribute('src') ? script.getAttribute('src') : '', window.location.href);
      return new URL('.', abs).toString();
    } catch (e) {
      return new URL('.', window.location.href).toString();
    }
  }

  function onDOMReady(cb){
    if(document.readyState === 'complete' || document.readyState === 'interactive') cb();
    else document.addEventListener('DOMContentLoaded', cb, { once: true });
  }

  function createIframe(attrs){
    const f = document.createElement('iframe');
    Object.entries(attrs||{}).forEach(([k,v])=>{
      if(k==='style' && typeof v==='object') Object.assign(f.style, v);
      else if(v!=null) f.setAttribute(k, v);
    });
    return f;
  }

  // ------- Iframe lifecycle -------
  function writeHTML(doc, html, lang){
    try {
      // Ensures a clean document (helps Firefox)
      const w = doc.open();
      w.write('<!DOCTYPE html>');
      w.close();
    } catch (err) {
      console.error('[TGO SDK] Failed to write HTML', err);
    }
    doc.documentElement.innerHTML = html;
    if(lang) doc.documentElement.setAttribute('lang', lang);
  }

  const UI_SHELL_HTML = '<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>TGO UI Shell</title><style>html,body{height:100%}body{margin:0;font:14px/1.4 system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;background:#fff}#tgo-root{height:100%}</style></head><body><div id="tgo-root" aria-label="TGO Widget UI Root"></div></body></html>';

  function createUIFrame(baseUrl){
    // Outer container controls layout and animations (Intercom-like)
    const container = document.createElement('div');
    container.id = UI_CONTAINER_ID;
    Object.assign(container.style, {
      zIndex: 2147483000,
      position: 'fixed',
      bottom: '84px',
      right: '20px',
      transformOrigin: 'right bottom',
      // Size behavior inspired by Intercom
      height: 'min(704px, calc(100% - 104px))',
      minHeight: '80px',
      width: 'min(400px, max(0px, calc(-20px + 100vw)))',
      maxHeight: '704px',
      borderRadius: '16px',
      overflow: 'hidden',
      boxShadow: 'rgba(9, 14, 21, 0.16) 0px 5px 40px 0px',
      background: '#fff',
      // Closed by default
      transform: 'scale(0)',
      opacity: '0',
      pointerEvents: 'none',
      visibility: 'hidden',
      transition: 'width 320ms, height 320ms, max-height 320ms, left 240ms, right 240ms, top 240ms, bottom 240ms, transform 300ms cubic-bezier(0, 1.2, 1, 1), opacity 120ms ease-out'
    });

    // UI iframe fills the container; no own transitions/transform
    const ui = createIframe({
      name: UI_IFRAME_NAME,
      title: 'TGO Widget',
      style: {
        position: 'absolute', inset: '0', width: '100%', height: '100%',
        border: '0', display: 'block'
      },
      allow: 'clipboard-read; clipboard-write',
      loading: 'eager'
    });

    container.appendChild(ui);
    return { container, iframe: ui };
  }

  function createLauncher(){
    const btn = document.createElement('button');
    btn.setAttribute('aria-label', 'Open chat');
    Object.assign(btn.style, {
      position:'fixed', right:'16px', bottom:'16px', width:'56px', height:'56px', borderRadius:'50%',
      display:'block', cursor:'pointer', zIndex:2147483001,
      background:'#fff', color:'#111827', border:'0',
      boxShadow:'0 8px 20px rgba(0,0,0,.2)',
      transform:'scale(1)', opacity:'1',
      transition:'transform 120ms ease-out, opacity 220ms ease-out, background-color 200ms ease, color 200ms ease, box-shadow 200ms ease, top 200ms, bottom 200ms, left 200ms, right 200ms'
    });
    // default icon: TGO logo image (preserve original color)
    const logoImg = document.createElement('img');
    const _scriptEl = getCurrentScript();
    const _baseDir = dirnameFromScript(_scriptEl);
    logoImg.src = new URL('./logo.svg', _baseDir).toString();
    logoImg.alt = 'TGO';
    logoImg.setAttribute('aria-hidden', 'true');
    Object.assign(logoImg.style, { width:'28px', height:'28px', display:'block' });
    // Center image inside the button
    btn.style.display = 'grid';
    btn.style.alignItems = 'center';
    btn.style.justifyContent = 'center';
    btn.textContent = '';
    btn.appendChild(logoImg);

    // press/hover state machine with priority: pressed > hover
    let pressed = false;
    let hovered = false;
    const applyTransform = ()=>{
      const scale = pressed ? 0.92 : (hovered ? 1.06 : 1);
      btn.style.transform = 'scale(' + scale + ')';
    };

    btn.addEventListener('mouseenter', ()=>{ hovered = true; applyTransform(); });
    btn.addEventListener('mouseleave', ()=>{ hovered = false; applyTransform(); });
    btn.addEventListener('mousedown', ()=>{ pressed = true; applyTransform(); });
    btn.addEventListener('mouseup', ()=>{ pressed = false; applyTransform(); });
    btn.addEventListener('touchstart', ()=>{ pressed = true; applyTransform(); }, { passive: true });
    btn.addEventListener('touchend', ()=>{ pressed = false; applyTransform(); });
    // ensure release outside still restores scale
    window.addEventListener('mouseup', ()=>{ if(pressed){ pressed=false; applyTransform(); } });
    window.addEventListener('touchend', ()=>{ if(pressed){ pressed=false; applyTransform(); } });

    // expose a small API to update visual state (do not set transform here)
    btn.setOpenVisual = (open)=>{
      if(open){
        btn.setAttribute('aria-label', 'Close chat');
        // remove logo image if present, show ✕ icon
        try { if (logoImg.parentNode === btn) btn.removeChild(logoImg); } catch {}
        btn.textContent = '✕';
        btn.style.background = 'var(--primary, #2f80ed)';
        btn.style.color = '#fff';
        btn.style.boxShadow = '0 8px 20px rgba(0,0,0,.2)';
        btn.style.opacity = '1';
      } else {
        btn.setAttribute('aria-label', 'Open chat');
        btn.textContent = '';
        // ensure logo is attached on closed state
        try { if (logoImg.parentNode !== btn) btn.appendChild(logoImg); } catch {}
        btn.style.background = '#fff';
        btn.style.color = '#111827';
        btn.style.boxShadow = '0 8px 20px rgba(0,0,0,.2)';
        btn.style.opacity = '1';
      }
      applyTransform();
    };

    // position + theme runtime APIs
    btn.setPosition = (pos)=>{
      try {
        btn.style.top = 'auto'; btn.style.bottom = 'auto'; btn.style.left = 'auto'; btn.style.right = 'auto';
        switch(String(pos||'bottom-right')){
          case 'bottom-left': btn.style.bottom = '16px'; btn.style.left = '16px'; break;
          case 'top-right': btn.style.top = '16px'; btn.style.right = '16px'; break;
          case 'top-left': btn.style.top = '16px'; btn.style.left = '16px'; break;
          case 'bottom-right': default: btn.style.bottom = '16px'; btn.style.right = '16px'; break;
        }
      } catch(_){}
    };
    btn.setThemeColor = (color)=>{
      try {
        const c = String(color||'').trim() || '#2f80ed';
        btn.style.setProperty('--primary', c);
        // apply background depending on state (open => primary, closed => white)
        const isClosed = btn.contains(logoImg);
        btn.style.background = isClosed ? '#fff' : 'var(--primary, #2f80ed)';
      } catch(_){}
    };

    return btn;
  }

  function createControllerFrame(baseUrl, opts){
    const ctrl = createIframe({
      name: CTRL_IFRAME_NAME,
      title: 'TGO Controller',
      style: { position:'absolute', width:'0', height:'0', border:'0', opacity:'0', pointerEvents:'none' },
      'aria-hidden': 'true'
    });

    // Navigate the controller iframe directly to the built app entry (index.html)
    // and pass apiKey via query string BEFORE the app starts. This avoids race conditions
    // and cross-origin fetch issues for manifest discovery.
    try {
      const ctrlUrl = new URL('./index.html', baseUrl);
      if (opts && opts.apiKey) ctrlUrl.searchParams.set('apiKey', String(opts.apiKey));
      ctrl.src = ctrlUrl.toString();
    } catch (_) { /* keep about:blank if URL resolution fails */ }

    // Notify UI-ready once when the controller finishes its first load
    ctrl.addEventListener('load', ()=>{
      try { window.frames[CTRL_IFRAME_NAME]?.postMessage({ type:'tgo:ui-ready', name:UI_IFRAME_NAME }, '*'); } catch(e) {}
    }, { once: true });

    return ctrl;
  }

  function inject(baseUrl, opts){
    const state = { uiContainer: null, uiIframe: null, ctrl: null, launcher: null, isOpen: false, pageForwardingInited: false };

    function applyOpen(open){
      if(!state.uiContainer) return;
      state.isOpen = !!open;
      if(open){
        // show container (Intercom-like)
        state.uiContainer.style.visibility = 'visible';
        state.uiContainer.style.opacity = '1';
        state.uiContainer.style.transform = 'scale(1)';
        state.uiContainer.style.pointerEvents = 'all';
      } else {
        // hide container
        state.uiContainer.style.transform = 'scale(0)';
        state.uiContainer.style.opacity = '0';
        state.uiContainer.style.pointerEvents = 'none';
        state.uiContainer.style.visibility = 'hidden';
      }
      // Update launcher visual instead of hiding it
      try { state.launcher && state.launcher.setOpenVisual && state.launcher.setOpenVisual(!!open); } catch(e) {}
      try { window.frames[CTRL_IFRAME_NAME]?.postMessage({ type:'tgo:visibility', open: !!open }, '*'); } catch(e) {}
    }

    const apiShow = ()=> applyOpen(true);
    const apiHide = ()=> applyOpen(false);


    function applyPosition(pos){
      try {
        const c = state.uiContainer; if(!c) return;
        c.style.top = 'auto'; c.style.bottom = 'auto'; c.style.left = 'auto'; c.style.right = 'auto';
        switch(String(pos||'bottom-right')){
          case 'bottom-left': c.style.bottom = '84px'; c.style.left = '20px'; c.style.transformOrigin = 'left bottom'; break;
          case 'top-right': c.style.top = '20px'; c.style.right = '20px'; c.style.transformOrigin = 'right top'; break;
          case 'top-left': c.style.top = '20px'; c.style.left = '20px'; c.style.transformOrigin = 'left top'; break;
          case 'bottom-right': default: c.style.bottom = '84px'; c.style.right = '20px'; c.style.transformOrigin = 'right bottom'; break;
        }
        try { state.launcher && state.launcher.setPosition && state.launcher.setPosition(pos); } catch(_){ }
      } catch(e) { /* noop */ }
    }

    function applyExpanded(expanded){
      try {
        const c = state.uiContainer; if(!c) return;
        if(!!expanded){
          c.style.width = 'min(90vw, 1200px)';
          c.style.height = 'min(90vh, 900px)';
          c.style.maxHeight = '90vh';
        } else {
          c.style.width = 'min(400px, max(0px, calc(-20px + 100vw)))';
          c.style.height = 'min(704px, calc(100% - 104px))';
          c.style.maxHeight = '704px';
        }
      } catch(e) { /* noop */ }
    }

    const mount = () => {
      const { container, iframe } = createUIFrame(baseUrl);
      state.uiContainer = container;
      state.uiIframe = iframe;
      document.body.appendChild(container);

      // Write UI shell immediately (no reliance on load event)
      try { writeHTML(iframe.contentDocument, UI_SHELL_HTML, 'en'); } catch(e) { console.error('[TGO SDK] Failed to write UI frame', e); }

      // Launcher
      const launcher = createLauncher();
      state.launcher = launcher;
      launcher.addEventListener('click', ()=>{ state.isOpen ? apiHide() : apiShow(); });
      document.body.appendChild(launcher);
      // ensure launcher reflects current state
      // Set UI iframe URL with apiKey via history.replaceState (no navigation)
      try {
        if(opts && opts.apiKey && iframe && iframe.contentWindow){
          let uiUrl;
          try { uiUrl = new URL(iframe.contentWindow.location.href); } catch { uiUrl = new URL('./ui-shell.html', baseUrl); }
          if(uiUrl.protocol === 'about:') { uiUrl = new URL('./ui-shell.html', baseUrl); }
          uiUrl.searchParams.set('apiKey', String(opts.apiKey));
          iframe.contentWindow.history.replaceState({}, '', uiUrl.toString());
        }
      } catch (_err) { /* ignore */ }

      try { launcher.setOpenVisual && launcher.setOpenVisual(state.isOpen); } catch {}

      // Start controller immediately after UI is prepared
      const ctrl = createControllerFrame(baseUrl, opts);
      state.ctrl = ctrl;
      document.body.appendChild(ctrl);

      // Host page activity forwarding -> controller
      let __tgo_pg_timer = null;
      const notifyPageInfo = ()=>{
        try {
          const payload = { page_url: window.location.href, title: document.title, referrer: document.referrer || '' };
          window.frames[CTRL_IFRAME_NAME]?.postMessage({ type:'TGO_HOST_PAGE_INFO', payload }, '*');
        } catch(e) { /* noop */ }
      };
      const notifyPageInfoDebounced = ()=>{ try { if(__tgo_pg_timer) clearTimeout(__tgo_pg_timer); __tgo_pg_timer = setTimeout(notifyPageInfo, 300); } catch(_){} };


      // Notify controller on page exit (before unload/hidden)
      let __tgo_last_exit_at = 0;
      const notifyPageExit = ()=>{
        try {
          const now = Date.now();
          if (now - __tgo_last_exit_at < 500) return; // throttle duplicate events
          __tgo_last_exit_at = now;
          const payload = { page_url: window.location.href, title: document.title, referrer: document.referrer || '' };
          window.frames[CTRL_IFRAME_NAME]?.postMessage({ type:'TGO_HOST_PAGE_EXIT', payload }, '*');
        } catch(e) { /* noop */ }
      };

      // Notify controller (optional) + initial page info
      ctrl.addEventListener('load', ()=>{
        try { window.frames[CTRL_IFRAME_NAME]?.postMessage({ type:'tgo:ui-ready', name:UI_IFRAME_NAME }, '*'); } catch(e) {}
        notifyPageInfoDebounced();
      }, { once: true });

      // Default closed
      applyOpen(false);

      // Install listeners once per instance
      if(!state.pageForwardingInited){
        state.pageForwardingInited = true;
        try {
          const origPush = history.pushState; history.pushState = function(){ origPush.apply(history, arguments); notifyPageInfoDebounced(); };
        } catch(_){ }
        try {
          const origReplace = history.replaceState; history.replaceState = function(){ origReplace.apply(history, arguments); notifyPageInfoDebounced(); };
        } catch(_){ }
        try { window.addEventListener('popstate', notifyPageInfoDebounced); } catch(_){ }
        try { window.addEventListener('hashchange', notifyPageInfoDebounced); } catch(_){ }
        try { document.addEventListener('visibilitychange', ()=>{ if (!document.hidden) { try { notifyPageInfoDebounced(); } catch(_){} } }); } catch(_){ }

        try { window.addEventListener('beforeunload', ()=>{ try { notifyPageExit(); } catch(_){} }); } catch(_){ }
        // Also send once in case ctrl loaded earlier
        try { notifyPageInfoDebounced(); } catch(_){ }
      }

      // Listen to controller messages (e.g., header close requests)
      window.addEventListener('message', (e)=>{
        const d = e.data || {};
        if(d && d.type === 'tgo:hide') apiHide();
        if(d && d.type === 'tgo:show') apiShow();
        if(d && d.type === 'TGO_WIDGET_CONFIG' && d.payload){
          if (typeof d.payload.position === 'string') applyPosition(d.payload.position);
          if (typeof d.payload.theme_color === 'string') {
            try { state.launcher && state.launcher.setThemeColor && state.launcher.setThemeColor(d.payload.theme_color); } catch(_){}
          }
          if (typeof d.payload.expanded === 'boolean') applyExpanded(!!d.payload.expanded);
        }
        if(d && d.type === 'TGO_REQUEST_PAGE_INFO'){
          try { notifyPageInfoDebounced(); } catch(_){}
        }
      });

      return state;
    };

    onDOMReady(mount);

    return {
      get uiContainer(){ return state.uiContainer; },
      get uiIframe(){ return state.uiIframe; },
      get ctrl(){ return state.ctrl; },
      show: apiShow,
      hide: apiHide,
      get isOpen(){ return state.isOpen; }
    };
  }

  function init(opts){
    if (__tgo_lastInstance) return __tgo_lastInstance;
    const script = getCurrentScript();
    const base = dirnameFromScript(script);
    __tgo_lastInstance = inject(base, opts||{});
    return __tgo_lastInstance;
  }

  function shutdown(){
    try {
      const container = document.getElementById(UI_CONTAINER_ID);
      container && container.parentNode && container.parentNode.removeChild(container);
    } catch (e) { /* noop */ }
    try {
      const ctrl = document.getElementsByName(CTRL_IFRAME_NAME)[0];
      ctrl && ctrl.parentNode && ctrl.parentNode.removeChild(ctrl);
    } catch (e) { /* noop */ }
    try {
      const launcher = document.querySelector('button[aria-label="Open chat"]');
      launcher && launcher.parentNode && launcher.parentNode.removeChild(launcher);
    } catch (e) { /* noop */ }
  }

  // ------- Public API -------
  const queue = [];
  let booted = false;
  function flush(){ while(queue.length) { const [fn, args] = queue.shift(); try{ api[fn]?.apply(null, args);}catch(e){console.error('[TGO SDK]', e);} } }

  const api = {
    init: function(){
      const res = init.apply(null, arguments);
      booted = true; flush();
      return res;
    },
    show: function(){ if(!__tgo_lastInstance) init(); return __tgo_lastInstance?.show?.(); },
    hide: function(){ if(!__tgo_lastInstance) init(); return __tgo_lastInstance?.hide?.(); },
    track: function(){
      try {
        const arg0 = arguments[0];
        let payload = null;
        if (typeof arg0 === 'string') {
          payload = Object.assign({ activity_type: arg0, title: arguments[1] }, (typeof arguments[2] === 'object' && arguments[2]) || {});
        } else if (arg0 && typeof arg0 === 'object') {
          payload = arg0;
        }
        if (payload) window.frames[CTRL_IFRAME_NAME]?.postMessage({ type:'TGO_TRACK_EVENT', payload }, '*');
      } catch(e) { /* noop */ }
    },
    shutdown
  };


  if(!window[SDK_NAME]){
    const stub = function(cmd){
      const args = Array.prototype.slice.call(arguments, 1);
      if(!booted) queue.push([cmd, args]); else api[cmd]?.apply(null, args);
    };
    stub.init = api.init; stub.shutdown = api.shutdown; stub.show = api.show; stub.hide = api.hide; stub.track = api.track;
    window[SDK_NAME] = stub;
  } else {
    Object.assign(window[SDK_NAME], api);
  }

  // ------- Auto-initialize if api_key is present on script src -------
  (function(){
    try {
      const script = getCurrentScript(); if(!script) return;
      const src = script.getAttribute('src') || '';
      const url = new URL(src, window.location.href);
      const apiKey = url.searchParams.get('api_key') || url.searchParams.get('apiKey') || url.searchParams.get('platform_api_key');
      if (apiKey) {
        // Avoid duplicate injection; init() now returns existing instance if already created
        try { window[SDK_NAME].init({ apiKey: String(apiKey) }); } catch(e) { /* ignore */ }
      }
    } catch (e) { /* ignore */ }
  })();
})();

