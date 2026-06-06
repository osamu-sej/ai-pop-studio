import { useState } from "react";
import type { StoredImage } from "../api/client";
import { generateImage } from "../api/client";

interface Props {
  onGenerated: (image: StoredImage) => void;
  onError: (message: string) => void;
}

const STYLES = ["写実的", "イラスト", "水彩", "シンプル"];

export default function ImageGenerator({ onGenerated, onError }: Props) {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    const text = prompt.trim();
    if (!text) return;
    setLoading(true);
    try {
      const image = await generateImage(text, style || undefined);
      onGenerated(image);
      setPrompt("");
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      handleGenerate();
    }
  };

  return (
    <section className="panel">
      <h2 className="panel-title">① 料理画像を生成</h2>
      <p className="panel-desc">
        入れたい料理を言葉で入力して画像を作ります。作った画像は下のライブラリに保管されます。
      </p>
      <textarea
        className="prompt-input"
        placeholder="例: ふっくら焼き上げた塩鮭の切り身"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={3}
      />
      <div className="style-row">
        <span className="style-label">スタイル:</span>
        <div className="style-chips">
          <button
            type="button"
            className={`chip ${style === "" ? "chip-active" : ""}`}
            onClick={() => setStyle("")}
          >
            指定なし
          </button>
          {STYLES.map((s) => (
            <button
              type="button"
              key={s}
              className={`chip ${style === s ? "chip-active" : ""}`}
              onClick={() => setStyle(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
      <button
        className="primary-btn"
        onClick={handleGenerate}
        disabled={loading || prompt.trim() === ""}
      >
        {loading ? "生成中…" : "画像を生成 (⌘/Ctrl+Enter)"}
      </button>
    </section>
  );
}
