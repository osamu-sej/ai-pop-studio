const API_BASE = "/api";

export interface StoredImage {
  id: string;
  prompt: string;
  style: string | null;
  url: string;
  created_at: string;
}

export interface BentoLayout {
  preset: string | null;
  compartments: Record<string, string>;
  updated_at: string | null;
}

export async function generateImage(
  prompt: string,
  style?: string
): Promise<StoredImage> {
  const res = await fetch(`${API_BASE}/images/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, style: style || null }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `画像生成に失敗しました (${res.status})`);
  }
  return res.json();
}

export async function listImages(): Promise<StoredImage[]> {
  const res = await fetch(`${API_BASE}/images`);
  if (!res.ok) throw new Error(`画像一覧の取得に失敗しました (${res.status})`);
  const data = await res.json();
  return data.images;
}

export async function deleteImage(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/images/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`画像の削除に失敗しました (${res.status})`);
}

export async function getBento(): Promise<BentoLayout> {
  const res = await fetch(`${API_BASE}/bento`);
  if (!res.ok) throw new Error(`弁当配置の取得に失敗しました (${res.status})`);
  return res.json();
}

export async function saveBento(
  preset: string,
  compartments: Record<string, string | null>
): Promise<BentoLayout> {
  const res = await fetch(`${API_BASE}/bento`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preset, compartments }),
  });
  if (!res.ok) throw new Error(`弁当配置の保存に失敗しました (${res.status})`);
  return res.json();
}
