const companyForm = document.getElementById('company-form');
const companiesBody = document.getElementById('companies-body');
const jobsBody = document.getElementById('jobs-body');
const docsBody = document.getElementById('docs-body');
const docsHeader = document.getElementById('documents-header');

let companiesById = {};

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Erro inesperado' }));
    throw new Error(err.error || 'Falha na requisição');
  }
  return res.json();
}

async function loadCompanies() {
  const companies = await api('/api/companies');
  companiesById = Object.fromEntries(companies.map(c => [c.id, c]));
  companiesBody.innerHTML = '';

  companies.forEach((c) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${c.id}</td>
      <td>${c.name}</td>
      <td>${c.cnpj}</td>
      <td>${c.strategy}</td>
      <td>
        <button class="secondary" data-sync="${c.id}">Sincronizar agora</button>
        <button class="secondary" data-docs="${c.id}">Ver docs</button>
      </td>
    `;
    companiesBody.appendChild(tr);
  });
}

async function loadJobs() {
  const jobs = await api('/api/jobs');
  jobsBody.innerHTML = '';
  jobs.forEach((j) => {
    const company = companiesById[j.company_id];
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>#${j.id}</td>
      <td>${company ? company.name : j.company_id}</td>
      <td>${j.status}</td>
      <td>${j.total_documents || 0}</td>
      <td>${j.message || ''}</td>
    `;
    jobsBody.appendChild(tr);
  });
}

async function loadDocuments(companyId) {
  const company = companiesById[companyId];
  docsHeader.textContent = `Empresa: ${company.name} (${company.cnpj})`;
  const docs = await api(`/api/documents?company_id=${companyId}`);
  docsBody.innerHTML = '';

  docs.forEach((d) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${d.model}</td>
      <td>${d.direction}</td>
      <td><small>${d.chave}</small></td>
      <td>${d.issue_date}</td>
      <td>R$ ${Number(d.amount).toFixed(2)}</td>
      <td><small>${d.xml_path}</small></td>
    `;
    docsBody.appendChild(tr);
  });
}

companyForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = new FormData(companyForm);
  try {
    await api('/api/companies', {
      method: 'POST',
      body: JSON.stringify(Object.fromEntries(data.entries())),
    });
    companyForm.reset();
    await loadCompanies();
    await loadJobs();
  } catch (error) {
    alert(error.message);
  }
});

companiesBody.addEventListener('click', async (e) => {
  const syncId = e.target.getAttribute('data-sync');
  const docsId = e.target.getAttribute('data-docs');

  if (syncId) {
    await api(`/api/sync/${syncId}`, { method: 'POST', body: '{}' });
    await loadJobs();
    return;
  }

  if (docsId) {
    await loadDocuments(Number(docsId));
  }
});

async function bootstrap() {
  await loadCompanies();
  await loadJobs();
  setInterval(loadJobs, 3000);
}

bootstrap();
