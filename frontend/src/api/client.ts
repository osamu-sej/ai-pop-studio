const API_BASE = "http://localhost:8000/api";

export async function parsePdf(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/pdf/parse`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`PDF parse failed: ${res.status}`);
  return res.json();
}

export async function getTemplates() {
  const res = await fetch(`${API_BASE}/templates`);
  if (!res.ok) throw new Error(`Failed to fetch templates: ${res.status}`);
  return res.json();
}

export async function generatePop(templateId: string, products: unknown[]) {
  const res = await fetch(`${API_BASE}/pop/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template_id: templateId, products }),
  });
  if (!res.ok) throw new Error(`POP generation failed: ${res.status}`);
  return res.blob();
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
