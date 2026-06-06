import { useEffect, useMemo, useState } from "react";
import "./App.css";
import ImageGenerator from "./components/ImageGenerator";
import ImageLibrary from "./components/ImageLibrary";
import BentoBox from "./components/BentoBox";
import type { StoredImage } from "./api/client";
import {
  listImages,
  deleteImage,
  getBento,
  saveBento,
} from "./api/client";

function App() {
  const [images, setImages] = useState<StoredImage[]>([]);
  const [layout, setLayout] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  // 初期ロード: 保管画像と弁当配置
  useEffect(() => {
    Promise.all([listImages(), getBento()])
      .then(([imgs, bento]) => {
        setImages(imgs);
        setLayout(bento.compartments ?? {});
        setSavedAt(bento.updated_at ?? null);
      })
      .catch((e) => setError((e as Error).message));
  }, []);

  const imagesById = useMemo(() => {
    const map: Record<string, StoredImage> = {};
    for (const img of images) map[img.id] = img;
    return map;
  }, [images]);

  const handleGenerated = (image: StoredImage) => {
    setImages((prev) => [image, ...prev]);
  };

  const handleDeleteImage = async (id: string) => {
    try {
      await deleteImage(id);
      setImages((prev) => prev.filter((i) => i.id !== id));
      // 配置からも除去
      setLayout((prev) => {
        const next = { ...prev };
        for (const slot of Object.keys(next)) {
          if (next[slot] === id) delete next[slot];
        }
        return next;
      });
    } catch (e) {
      setError((e as Error).message);
    }
  };

  // 仕切りへドロップ
  const handleDrop = (
    compartmentId: string,
    imageId: string,
    fromCompartment?: string
  ) => {
    setLayout((prev) => {
      const next = { ...prev };
      // 別の仕切りからの移動なら元を空にする（入れ替え対応）
      if (fromCompartment && fromCompartment !== compartmentId) {
        const displaced = next[compartmentId];
        next[fromCompartment] = displaced ?? "";
        if (!displaced) delete next[fromCompartment];
      }
      next[compartmentId] = imageId;
      return next;
    });
  };

  const handleClear = (compartmentId: string) => {
    setLayout((prev) => {
      const next = { ...prev };
      delete next[compartmentId];
      return next;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const result = await saveBento(layout);
      setSavedAt(result.updated_at);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const filledCount = Object.values(layout).filter(Boolean).length;

  return (
    <div className="app">
      <header className="app-header">
        <h1>🍱 幕の内弁当コンポーザー</h1>
        <p className="subtitle">
          画像を生成して保管し、仕切りごとに盛り付けてオリジナルのお弁当を組み立てよう
        </p>
      </header>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button className="error-close" onClick={() => setError(null)}>
            &times;
          </button>
        </div>
      )}

      <div className="app-content">
        <div className="app-left">
          <ImageGenerator onGenerated={handleGenerated} onError={setError} />
          <ImageLibrary images={images} onDelete={handleDeleteImage} />
        </div>

        <div className="app-right">
          <section className="panel">
            <div className="bento-header">
              <h2 className="panel-title">③ お弁当を盛り付け</h2>
              <div className="bento-actions">
                <span className="bento-count">{filledCount} / 6 仕切り</span>
                <button
                  className="primary-btn save-btn"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? "保存中…" : "献立を保存"}
                </button>
              </div>
            </div>
            {savedAt && (
              <p className="saved-note">
                保存済み: {new Date(savedAt).toLocaleString("ja-JP")}
              </p>
            )}
            <BentoBox
              layout={layout}
              imagesById={imagesById}
              onDrop={handleDrop}
              onClear={handleClear}
            />
          </section>
        </div>
      </div>
    </div>
  );
}

export default App;
