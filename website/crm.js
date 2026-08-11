/* ═══════════════════════════════════════════════
   LOCALOS CRM — Kanban Pipeline Logic
   Drag & Drop · localStorage · CSV Import/Export
   ═══════════════════════════════════════════════ */

(function () {
  'use strict';

  const STORAGE_KEY = 'localos_crm_leads';
  const STAGES = ['new', 'contacted', 'replied', 'call_booked', 'proposal', 'won', 'lost'];
  const MRR_PER_CLIENT = 499; // Average revenue per won client

  // ── Data Layer ──
  function loadLeads() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  }

  function saveLeads(leads) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(leads));
  }

  function generateId() {
    return 'ld_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  }

  // ── Render ──
  function renderBoard(filter = '') {
    const leads = loadLeads();
    const filterLower = filter.toLowerCase();

    STAGES.forEach(stage => {
      const col = document.getElementById('col-' + stage);
      col.innerHTML = '';

      const stageLeads = leads.filter(l => {
        if (l.stage !== stage) return false;
        if (!filterLower) return true;
        const searchable = `${l.business_name} ${l.city} ${l.niche} ${l.email}`.toLowerCase();
        return searchable.includes(filterLower);
      });

      stageLeads.forEach(lead => {
        col.appendChild(createCard(lead));
      });

      // Update count
      const countEl = document.getElementById('count-' + stage);
      if (countEl) countEl.textContent = stageLeads.length;
    });

    updateStats(leads);
  }

  function createCard(lead) {
    const card = document.createElement('div');
    card.className = 'lead-card';
    card.draggable = true;
    card.dataset.id = lead.id;

    const tierClass = `tier-${lead.tier || 'C'}`;
    const tierLabel = { A: '🔥 A', B: '🟡 B', C: '❄️ C' }[lead.tier] || '❄️ C';

    card.innerHTML = `
      <div class="card-top">
        <div class="card-name">${escHtml(lead.business_name || 'Unknown')}</div>
        <span class="card-tier ${tierClass}">${tierLabel}</span>
      </div>
      <div class="card-meta">
        ${lead.niche ? `<span class="card-tag">${escHtml(lead.niche)}</span>` : ''}
        ${lead.city ? `<span class="card-tag">📍 ${escHtml(lead.city)}</span>` : ''}
      </div>
      <div class="card-contact">
        ${lead.email && lead.email.includes('@')
          ? `<a href="mailto:${escHtml(lead.email)}">📧 ${escHtml(lead.email)}</a>`
          : ''}
        ${lead.phone ? `<span>📞 ${escHtml(lead.phone)}</span>` : ''}
        ${lead.website ? `<a href="${escHtml(lead.website)}" target="_blank">🌐 Website</a>` : ''}
      </div>
      <div class="card-footer">
        <span class="card-date">${lead.date_scraped || lead.date_added || ''}</span>
        ${lead.score ? `<span class="card-score">${lead.score} pts</span>` : ''}
        <div class="card-actions">
          <button class="card-btn" data-action="delete" data-id="${lead.id}" title="Delete">🗑</button>
        </div>
      </div>
    `;

    // Drag events
    card.addEventListener('dragstart', (e) => {
      card.classList.add('dragging');
      e.dataTransfer.setData('text/plain', lead.id);
      e.dataTransfer.effectAllowed = 'move';
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      document.querySelectorAll('.col-body').forEach(c => c.classList.remove('drag-over'));
    });

    // Delete button
    card.querySelector('[data-action="delete"]').addEventListener('click', (e) => {
      e.stopPropagation();
      if (confirm(`Delete "${lead.business_name}"?`)) {
        deleteLead(lead.id);
      }
    });

    return card;
  }

  function escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ── Stats ──
  function updateStats(leads) {
    const won = leads.filter(l => l.stage === 'won').length;
    const lost = leads.filter(l => l.stage === 'lost').length;
    const total = leads.length;
    const pipeline = leads.filter(l => !['won', 'lost', 'new'].includes(l.stage)).length;
    const convRate = total > 0 ? Math.round((won / total) * 100) : 0;

    document.getElementById('statMRR').textContent = `$${(won * MRR_PER_CLIENT).toLocaleString()}`;
    document.getElementById('statTotal').textContent = total;
    document.getElementById('statConv').textContent = convRate + '%';
    document.getElementById('statWon').textContent = won;
    document.getElementById('statPipeline').textContent = pipeline;
  }

  // ── CRUD ──
  function addLead(leadData) {
    const leads = loadLeads();
    const newLead = {
      id: generateId(),
      stage: 'new',
      date_added: new Date().toISOString().split('T')[0],
      ...leadData,
    };
    leads.push(newLead);
    saveLeads(leads);
    renderBoard();
  }

  function moveLead(leadId, newStage) {
    const leads = loadLeads();
    const lead = leads.find(l => l.id === leadId);
    if (lead) {
      lead.stage = newStage;
      lead.last_updated = new Date().toISOString().split('T')[0];
      saveLeads(leads);
      renderBoard(document.getElementById('searchInput').value);
    }
  }

  function deleteLead(leadId) {
    let leads = loadLeads();
    leads = leads.filter(l => l.id !== leadId);
    saveLeads(leads);
    renderBoard(document.getElementById('searchInput').value);
  }

  // ── Drag & Drop ──
  function setupDropZones() {
    document.querySelectorAll('.col-body').forEach(col => {
      col.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        col.classList.add('drag-over');
      });

      col.addEventListener('dragleave', () => {
        col.classList.remove('drag-over');
      });

      col.addEventListener('drop', (e) => {
        e.preventDefault();
        col.classList.remove('drag-over');
        const leadId = e.dataTransfer.getData('text/plain');
        const stage = col.id.replace('col-', '');
        moveLead(leadId, stage);
      });
    });
  }

  // ── CSV Import ──
  function importCSV(csvText) {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) return;

    const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/"/g, ''));
    const leads = loadLeads();
    let imported = 0;

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
      const row = {};
      headers.forEach((h, idx) => {
        row[h] = values[idx] || '';
      });

      // Map CSV fields to CRM fields
      const lead = {
        id: generateId(),
        stage: row.outreach_status === 'contacted' ? 'contacted' : 'new',
        business_name: row.business_name || '',
        email: row.email || '',
        phone: row.phone || '',
        city: row.city || '',
        niche: row.niche || '',
        website: row.website || '',
        tier: row.tier || 'C',
        score: row.score || '',
        google_rating: row.google_rating || '',
        review_count: row.review_count || '',
        date_scraped: row.date_scraped || new Date().toISOString().split('T')[0],
        date_added: new Date().toISOString().split('T')[0],
      };

      // Skip duplicates (by business name)
      const exists = leads.some(l =>
        l.business_name.toLowerCase() === lead.business_name.toLowerCase()
      );
      if (!exists && lead.business_name) {
        leads.push(lead);
        imported++;
      }
    }

    saveLeads(leads);
    renderBoard();
    alert(`Imported ${imported} new leads!`);
  }

  // ── CSV Export ──
  function exportCSV() {
    const leads = loadLeads();
    const headers = ['business_name', 'email', 'phone', 'city', 'niche', 'website', 'tier', 'score', 'stage', 'date_scraped', 'date_added'];

    let csv = headers.join(',') + '\n';
    leads.forEach(lead => {
      const row = headers.map(h => {
        const val = (lead[h] || '').toString().replace(/"/g, '""');
        return `"${val}"`;
      });
      csv += row.join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `localos_crm_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── Event Listeners ──
  function init() {
    setupDropZones();
    renderBoard();

    // Search
    document.getElementById('searchInput').addEventListener('input', (e) => {
      renderBoard(e.target.value);
    });

    // Add Lead Modal
    const modal = document.getElementById('addLeadModal');
    document.getElementById('btnAddLead').addEventListener('click', () => {
      modal.classList.add('open');
    });
    document.getElementById('btnCancelAdd').addEventListener('click', () => {
      modal.classList.remove('open');
    });
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('open');
    });

    // Add Lead Form
    document.getElementById('addLeadForm').addEventListener('submit', (e) => {
      e.preventDefault();
      addLead({
        business_name: document.getElementById('ml-name').value,
        email: document.getElementById('ml-email').value,
        phone: document.getElementById('ml-phone').value,
        city: document.getElementById('ml-city').value,
        niche: document.getElementById('ml-niche').value,
        website: document.getElementById('ml-website').value,
        tier: document.getElementById('ml-tier').value,
        score: { A: '70', B: '50', C: '25' }[document.getElementById('ml-tier').value] || '30',
      });
      e.target.reset();
      modal.classList.remove('open');
    });

    // Import CSV
    const fileInput = document.getElementById('csvFileInput');
    document.getElementById('btnImport').addEventListener('click', () => {
      fileInput.click();
    });
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        importCSV(ev.target.result);
        fileInput.value = '';
      };
      reader.readAsText(file);
    });

    // Export CSV
    document.getElementById('btnExport').addEventListener('click', exportCSV);
  }

  init();
})();
