// static/js/kpis.js
(function () {
  const $  = (s, r=document) => r.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const nfmt = n => (isFinite(n) ? new Intl.NumberFormat('fr-FR').format(n) : '—');
  const fmtDate = iso => { if(!iso) return '—'; const d=new Date(iso); return isNaN(d)?'—':d.toLocaleDateString('fr-FR'); };

  const kpiRoot = document.getElementById('kpis');
  const workbenchModal = document.getElementById('workbenchModal');

  if (!kpiRoot || !workbenchModal) {
    window.KPIs = { hydrate: () => {} };
    return;
  }

  const WORKBENCH_API_URL =
    kpiRoot.getAttribute('data-workbench-url') ||
    (window.KPIs && window.KPIs.WORKBENCH_API_URL) ||
    ''; // must be provided

  const WB_STATE = { status:"requisition", page:1, per_page:10, total:0, pages:1, has_next:false, has_prev:false, q:"" };
  let WB_CACHE = [];

  function mapApiToRow(c){
    return {
      id: c.id,
      dateheurecargaison: c.dateheurecargaison,
      importateur_name: c.importateur || c.importateur_name || null,
      entrepot_name:     c.entrepot    || c.entrepot_name     || null,
      immatriculation:   c.immatriculation || null,
      produit_name:      c.produit || c.produit_name || null,
      volume:            c.volume,
      qrcode:            c.qrcode || c.uuid || c.code || null
    };
  }
  function wbRowHTML(r){
    const immat = esc(r.immatriculation || '—');
    return `
      <tr data-id="${esc(r.id)}">
        <td class="px-3 py-2" data-th="Date entrée">${fmtDate(r.dateheurecargaison)}</td>
        <td class="px-3 py-2" data-th="Importateur">${esc(r.importateur_name || '—')}</td>
        <td class="px-3 py-2" data-th="Entrepôt">${esc(r.entrepot_name || '—')}</td>
        <td class="px-3 py-2" data-th="Immatriculation"><span class="chip chip--immat">${immat}</span></td>
        <td class="px-3 py-2" data-th="Produit">${r.produit_name ? `<span class="chip">${esc(r.produit_name)}</span>` : '—'}</td>
        <td class="px-3 py-2" data-th="Volume">${r.volume!=null ? `${nfmt(r.volume)} m³` : '—'}</td>
      </tr>
    `;
  }
  function setWbPgBtnState(){
    const dis = (sel,on)=>{ const b=document.querySelector(sel); if(!b) return; b.disabled=on; b.classList.toggle('is-disabled',on); };
    dis('.pg-btn[data-wb-dir="first"]', WB_STATE.page <= 1);
    dis('.pg-btn[data-wb-dir="prev"]',  !WB_STATE.has_prev);
    dis('.pg-btn[data-wb-dir="next"]',  !WB_STATE.has_next);
    dis('.pg-btn[data-wb-dir="last"]',  WB_STATE.page >= WB_STATE.pages);
  }
  function renderWorkbench(rows){
    const body  = document.getElementById('wbTbody');
    const info  = document.getElementById('wbInfo');
    const page  = document.getElementById('wbPage');

    if (body){
      body.innerHTML = rows.length
        ? rows.map(wbRowHTML).join('')
        : `<tr><td class="px-3 py-6 text-center text-white/70" colspan="6">Aucun enregistrement pour ce filtre.</td></tr>`;
    }

    if (WB_STATE.total > 0){
      const start = (WB_STATE.per_page*(WB_STATE.page-1)) + (rows.length?1:0);
      const end   = (WB_STATE.per_page*(WB_STATE.page-1)) + rows.length;
      if (info) info.textContent = `Affichage ${start}–${end} sur ${WB_STATE.total}`;
      if (page) page.textContent = `${WB_STATE.page} / ${WB_STATE.pages}`;
    } else {
      if (info) info.textContent = '—';
      if (page) page.textContent = '1 / 1';
    }

    setWbPgBtnState();
  }
  async function loadWorkbenchFromAPI(opts={}){
    const { status=WB_STATE.status, page=WB_STATE.page, per_page=WB_STATE.per_page, q=WB_STATE.q } = opts;
    if (!WORKBENCH_API_URL) { console.warn('WORKBENCH_API_URL missing'); renderWorkbench([]); return; }

    try{
      const url = new URL(WORKBENCH_API_URL, window.location.origin);
      url.searchParams.set('status', status);
      url.searchParams.set('page', String(page));
      url.searchParams.set('per_page', String(per_page));
      if (q) url.searchParams.set('q', q);

      const res = await fetch(url.toString(), { headers:{ 'Accept':'application/json' }});
      if(!res.ok) throw new Error('HTTP '+res.status);
      const data = await res.json();

      const list = (data?.items || data?.pending || []);
      const rows = list.map(mapApiToRow);
      WB_CACHE = rows.slice();

      const p = data?.pagination || {};
      WB_STATE.status   = status;
      WB_STATE.page     = Number(p.page || page) || 1;
      WB_STATE.per_page = Number(p.per_page || per_page) || 10;
      WB_STATE.total    = Number(p.total ?? p.count ?? (typeof data?.total === 'number' ? data.total : 0));
      if (!WB_STATE.total) WB_STATE.total = rows.length;

      WB_STATE.pages    = Number(p.pages || Math.max(1, Math.ceil(WB_STATE.total / WB_STATE.per_page)));
      WB_STATE.has_next = ('has_next' in p) ? !!p.has_next : WB_STATE.page < WB_STATE.pages;
      WB_STATE.has_prev = ('has_prev' in p) ? !!p.has_prev : WB_STATE.page > 1;

      const titleMap = {
        requisition: "Cargaisons — En attente de réquisition",
        pending:     "Cargaisons — En attente",
        inspection:  "Cargaisons — En inspection",
        conformes:   "Cargaisons — En attente de déchargement",
        reports:     "Rapports / Historique"
      };
      const wbTitle = document.getElementById('wbTitle');
      const wbSub   = document.getElementById('wbSubtitle');
      if (wbTitle) wbTitle.textContent = titleMap[status] || "Tableau de travail";
      if (wbSub)   wbSub.textContent   = q ? `Filtre: “${q}”` : `Statut: ${status}`;

      renderWorkbench(rows);
    }catch(err){
      console.error('Workbench load failed:', err);
      WB_CACHE = [];
      Object.assign(WB_STATE, { page:1, total:0, pages:1, has_next:false, has_prev:false });
      renderWorkbench([]);
    }
  }
  function openWorkbench(status="requisition"){
    WB_STATE.status = status || "requisition";
    WB_STATE.page   = 1;
    WB_STATE.q      = "";
    const search = document.getElementById('wbSearch');
    if (search) search.value = "";
    workbenchModal?.classList.remove('hidden');
    loadWorkbenchFromAPI({ status: WB_STATE.status, page:1, per_page: WB_STATE.per_page });
  }

  function hydrateKpis(kpis){
    if (!kpis) return;
    const set = (id, v)=>{ const el=document.getElementById(id); if(el) el.textContent=nfmt(v??0); };
    set('kpi-waiting',    kpis.waiting);
    set('kpi-inspection', kpis.inspection);
    set('kpi-conformes',  kpis.conformes);
    set('kpi-actions',    kpis.reports);
  }

  // Open modal on KPI click
  document.addEventListener('click', (e)=>{
    const k = e.target.closest('.kpi-card[data-scope]');
    if (!k) return;
    openWorkbench(String(k.dataset.scope || 'requisition').toLowerCase());
  });

  // Workbench pagination
  document.addEventListener('click', (e)=>{
    const btn = e.target.closest('.pg-btn[data-wb-dir]');
    if (!btn) return;
    let target = WB_STATE.page;
    const dir = btn.dataset.wbDir || btn.getAttribute('data-wb-dir');
    if (dir==='first') target = 1;
    if (dir==='prev')  target = Math.max(1, WB_STATE.page-1);
    if (dir==='next')  target = Math.min(WB_STATE.pages, WB_STATE.page+1);
    if (dir==='last')  target = WB_STATE.pages;
    if (target !== WB_STATE.page) loadWorkbenchFromAPI({ page: target });
  });

  // Workbench search
  (function(){
    const inp = document.getElementById('wbSearch');
    if (!inp) return;
    let t;
    inp.addEventListener('keydown', (ev)=>{
      if (ev.key === 'Enter'){
        ev.preventDefault();
        WB_STATE.q = inp.value.trim();
        loadWorkbenchFromAPI({ page:1, q: WB_STATE.q });
      }
    });
    inp.addEventListener('input', () => {
      clearTimeout(t);
      t = setTimeout(() => {
        WB_STATE.q = inp.value.trim();
        loadWorkbenchFromAPI({ page:1, q: WB_STATE.q });
      }, 250);
    });
  })();

  // Close modal
  document.getElementById('wbClose')?.addEventListener('click', () => {
    workbenchModal?.classList.add('hidden');
  });
  document.addEventListener('click', (e)=>{
    if (e.target?.dataset?.close === 'wb-backdrop')
      workbenchModal?.classList.add('hidden');
  });

  // Public API (optional)
  window.KPIs = { hydrate: hydrateKpis, openWorkbench, WORKBENCH_API_URL, _debug_state: WB_STATE };
})();