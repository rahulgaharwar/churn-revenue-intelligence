let dashboardData = null;
let scatterChart = null;
let featureChart = null;
let survivalChart = null;

document.addEventListener('DOMContentLoaded', async () => {
  await loadDashboardData();
  setupNavigation();
  setupSimulatorEvents();
  setupTableFilters();
  setupReportExport();
});

async function loadDashboardData() {
  try {
    const response = await fetch('dashboard_data.json');
    dashboardData = await response.json();
    
    renderKPIs(dashboardData.kpi);
    renderModelComparison(dashboardData.model_comparison);
    renderScatterChart(dashboardData.customer_sample);
    renderFeatureImportanceChart(dashboardData.feature_importance);
    renderSurvivalChart(dashboardData.survival_curves);
    renderAccountTable(dashboardData.customer_sample);
    
    // Initial run for simulator
    updateSimulator();
  } catch (error) {
    console.error('Error loading dashboard data:', error);
  }
}

function formatCurrency(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
}

function renderKPIs(kpi) {
  document.getElementById('kpi-total-arr').textContent = formatCurrency(kpi.total_arr);
  document.getElementById('kpi-revenue-at-risk').textContent = formatCurrency(kpi.revenue_at_risk_arr);
  document.getElementById('kpi-high-risk-arr').textContent = `High Risk: ${formatCurrency(kpi.high_risk_arr)}`;
  document.getElementById('kpi-high-risk-count').textContent = kpi.high_risk_count.toLocaleString();
  document.getElementById('kpi-risk-breakdown').textContent = `Medium: ${kpi.medium_risk_count} | Low: ${kpi.low_risk_count.toLocaleString()}`;
  document.getElementById('kpi-churn-rate').textContent = `${kpi.observed_churn_rate}%`;
  document.getElementById('kpi-model-f1').textContent = kpi.model_f1;
  
  document.getElementById('active-model-name').textContent = kpi.model_best;
  document.getElementById('active-model-auc').textContent = `ROC-AUC: ${kpi.model_auc}`;
}

function renderModelComparison(models) {
  const tbody = document.querySelector('#table-model-comparison tbody');
  tbody.innerHTML = '';
  
  for (const [name, metrics] of Object.entries(models)) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${name}</strong></td>
      <td><span class="badge-tag" style="color:#10b981; background:rgba(16,185,129,0.15);">${metrics.roc_auc}</span></td>
      <td>${metrics.precision}</td>
      <td>${metrics.recall}</td>
      <td><strong>${metrics.f1_score}</strong></td>
    `;
    tbody.appendChild(tr);
  }
}

/* 1. Scatter Chart: Churn Probability vs MRR */
function renderScatterChart(customers) {
  const ctx = document.getElementById('chartScatterRisk').getContext('2d');
  
  const highRisk = customers.filter(c => c.risk_tier === 'High').map(c => ({ x: c.mrr, y: c.churn_probability * 100, name: c.company_name }));
  const medRisk = customers.filter(c => c.risk_tier === 'Medium').map(c => ({ x: c.mrr, y: c.churn_probability * 100, name: c.company_name }));
  const lowRisk = customers.filter(c => c.risk_tier === 'Low').map(c => ({ x: c.mrr, y: c.churn_probability * 100, name: c.company_name }));
  
  scatterChart = new Chart(ctx, {
    type: 'scatter',
    data: {
      datasets: [
        { label: 'High Risk (>=65%)', data: highRisk, backgroundColor: 'rgba(239, 68, 68, 0.85)', pointRadius: 5 },
        { label: 'Medium Risk (35-65%)', data: medRisk, backgroundColor: 'rgba(245, 158, 11, 0.8)', pointRadius: 4 },
        { label: 'Low Risk (<35%)', data: lowRisk, backgroundColor: 'rgba(16, 185, 129, 0.5)', pointRadius: 3 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.raw.name}: MRR $${ctx.raw.x}, Risk ${ctx.raw.y.toFixed(1)}%`
          }
        }
      },
      scales: {
        x: { title: { display: true, text: 'Monthly Recurring Revenue ($)', color: '#94a3b8' }, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { title: { display: true, text: 'Churn Risk Probability (%)', color: '#94a3b8' }, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, min: 0, max: 100 }
      }
    }
  });
}

/* 2. Feature Importance Bar Chart */
function renderFeatureImportanceChart(features) {
  const ctx = document.getElementById('chartFeatureImportance').getContext('2d');
  
  const labels = features.map(f => f.feature.replace('_', ' ').toUpperCase());
  const data = features.map(f => f.importance);
  
  featureChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Feature Weight',
        data: data,
        backgroundColor: 'rgba(139, 92, 246, 0.85)',
        borderColor: '#8b5cf6',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#f1f5f9', font: { family: 'Inter', size: 11 } }, grid: { display: false } }
      }
    }
  });
}

/* 3. Survival Curves Chart */
function renderSurvivalChart(survival) {
  const ctx = document.getElementById('chartSurvivalCurves').getContext('2d');
  
  survivalChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: survival.timeline.map(t => `Month ${t}`),
      datasets: [
        { label: 'Enterprise Plan', data: survival.curves.Enterprise.map(v => v * 100), borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', tension: 0.3, fill: false },
        { label: 'Pro Plan', data: survival.curves.Pro.map(v => v * 100), borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.1)', tension: 0.3, fill: false },
        { label: 'Basic Plan', data: survival.curves.Basic.map(v => v * 100), borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', tension: 0.3, fill: false }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } }
      },
      scales: {
        x: { title: { display: true, text: 'Customer Tenure Timeline', color: '#94a3b8' }, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { title: { display: true, text: 'Survival Probability (%)', color: '#94a3b8' }, ticks: { color: '#94a3b8' }, min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
}

/* 4. What-If Churn Simulator Logic */
function setupSimulatorEvents() {
  const inputs = ['sim-plan', 'sim-contract', 'sim-mrr', 'sim-decay', 'sim-adoption', 'sim-tickets', 'sim-res-hrs', 'sim-pay-fail', 'sim-nps'];
  
  inputs.forEach(id => {
    document.getElementById(id).addEventListener('input', updateSimulator);
  });
}

function updateSimulator() {
  const plan = document.getElementById('sim-plan').value;
  const contract = document.getElementById('sim-contract').value;
  const mrr = parseFloat(document.getElementById('sim-mrr').value);
  const decay = parseFloat(document.getElementById('sim-decay').value);
  const adoption = parseFloat(document.getElementById('sim-adoption').value);
  const tickets = parseInt(document.getElementById('sim-tickets').value);
  const resHrs = parseFloat(document.getElementById('sim-res-hrs').value);
  const payFail = parseInt(document.getElementById('sim-pay-fail').value);
  const nps = parseInt(document.getElementById('sim-nps').value);

  // Update slider label texts
  document.getElementById('val-sim-mrr').textContent = mrr;
  document.getElementById('val-sim-decay').textContent = `${(decay * 100).toFixed(0)}%`;
  document.getElementById('val-sim-adoption').textContent = adoption;
  document.getElementById('val-sim-tickets').textContent = tickets;
  document.getElementById('val-sim-res-hrs').textContent = `${resHrs} hrs`;
  document.getElementById('val-sim-pay-fail').textContent = payFail;
  document.getElementById('val-sim-nps').textContent = nps;

  // Logistic Logit Formula matching training parameters
  let logit = -0.45
    - 2.8 * decay
    + 0.16 * (tickets * resHrs / 24.0)
    + 0.75 * payFail
    - 0.03 * adoption
    - 0.22 * nps
    + (contract === 'Monthly' ? 0.55 : 0)
    + (plan === 'Basic' ? 0.35 : (plan === 'Enterprise' ? -0.60 : 0));

  const prob = 1 / (1 + Math.exp(-logit));
  const probPct = Math.min(99, Math.max(1, Math.round(prob * 100)));

  // Display probability
  document.getElementById('sim-prob-display').textContent = `${probPct}%`;
  
  const circle = document.getElementById('sim-gauge-circle');
  const pill = document.getElementById('sim-risk-pill');
  const revenueLoss = mrr * 12 * (probPct / 100);
  
  document.getElementById('sim-revenue-loss').textContent = formatCurrency(revenueLoss);
  document.getElementById('sim-workload-idx').textContent = Math.round(tickets * resHrs);

  // Risk styling
  circle.className = 'gauge-circle';
  pill.className = 'risk-status-pill';

  if (probPct >= 65) {
    circle.style.borderColor = 'var(--danger)';
    circle.style.boxShadow = '0 0 20px rgba(239, 68, 68, 0.4)';
    pill.classList.add('risk-high');
    pill.textContent = 'Tier: High Risk';
  } else if (probPct >= 35) {
    circle.style.borderColor = 'var(--warning)';
    circle.style.boxShadow = '0 0 20px rgba(245, 158, 11, 0.4)';
    pill.classList.add('risk-medium');
    pill.textContent = 'Tier: Medium Risk';
  } else {
    circle.style.borderColor = 'var(--success)';
    circle.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.4)';
    pill.classList.add('risk-low');
    pill.textContent = 'Tier: Low Risk';
  }

  // Prescriptive Action Text
  const recs = [];
  if (decay < -0.2) recs.push('Initiate CSM proactive check-in (usage dropped significantly).');
  if (tickets >= 3 && resHrs > 24) recs.push('Escalate open support tickets to priority queue.');
  if (payFail > 0) recs.push('Trigger dunning flow & update payment method.');
  if (adoption < 45) recs.push('Offer tailored product onboarding webinar.');
  if (nps <= 5) recs.push('Trigger executive sponsor outreach call.');
  if (recs.length === 0) recs.push('Account in healthy standing. Include in monthly feature newsletter.');

  document.getElementById('sim-rec-text').textContent = recs.join(' ');
}

/* 5. Account Directory Table */
function setupTableFilters() {
  document.getElementById('account-search').addEventListener('input', filterAccounts);
  document.getElementById('filter-risk-tier').addEventListener('change', filterAccounts);
  document.getElementById('filter-plan').addEventListener('change', filterAccounts);
}

function filterAccounts() {
  if (!dashboardData) return;
  
  const search = document.getElementById('account-search').value.toLowerCase();
  const riskFilter = document.getElementById('filter-risk-tier').value;
  const planFilter = document.getElementById('filter-plan').value;

  const filtered = dashboardData.customer_sample.filter(c => {
    const matchesSearch = c.company_name.toLowerCase().includes(search) || c.customer_id.toLowerCase().includes(search);
    const matchesRisk = riskFilter === 'ALL' || c.risk_tier === riskFilter;
    const matchesPlan = planFilter === 'ALL' || c.plan_tier === planFilter;
    return matchesSearch && matchesRisk && matchesPlan;
  });

  renderAccountTable(filtered);
}

function renderAccountTable(customers) {
  const tbody = document.querySelector('#table-accounts tbody');
  tbody.innerHTML = '';

  customers.slice(0, 100).forEach(c => {
    const tr = document.createElement('tr');
    
    let riskBadgeClass = 'risk-low';
    if (c.risk_tier === 'High') riskBadgeClass = 'risk-high';
    if (c.risk_tier === 'Medium') riskBadgeClass = 'risk-medium';

    tr.innerHTML = `
      <td><code>${c.customer_id}</code></td>
      <td><strong>${c.company_name}</strong></td>
      <td>${c.plan_tier}</td>
      <td>${c.contract_type}</td>
      <td>$${c.mrr}</td>
      <td><strong>${(c.churn_probability * 100).toFixed(1)}%</strong></td>
      <td><span class="risk-status-pill ${riskBadgeClass}">${c.risk_tier}</span></td>
      <td style="font-size:12px; color:#cbd5e1;">${c.recommended_action}</td>
    `;
    tbody.appendChild(tr);
  });
}

function setupNavigation() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      item.classList.add('active');
    });
  });
}

function setupReportExport() {
  document.getElementById('btn-export-report').addEventListener('click', () => {
    if (!dashboardData) return;
    
    let csv = 'Customer_ID,Company_Name,Plan_Tier,Contract_Type,MRR,Churn_Probability,Risk_Tier,Recommended_Action\n';
    dashboardData.customer_sample.forEach(c => {
      csv += `"${c.customer_id}","${c.company_name}","${c.plan_tier}","${c.contract_type}",${c.mrr},${c.churn_probability},"${c.risk_tier}","${c.recommended_action}"\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SaaS_Revenue_Risk_Report_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  });
}
