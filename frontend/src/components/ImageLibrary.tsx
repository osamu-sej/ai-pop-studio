import type { StoredImage } from "../api/client";
import { DRAG_MIME } from "../dnd";

interface Props {
  images: StoredImage[];
  onDelete: (id: string) => void;
}

export default function ImageLibrary({ images, onDelete }: Props) {
  return (
    <section className="panel">
      <h2 className="panel-title">② 画像ライブラリ（保管庫）</h2>
      <p className="panel-desc">
        画像を右の弁当の仕切りへドラッグ&ドロップして盛り付けます。
      </p>
      {images.length === 0 ? (
        <div className="library-empty">
          まだ画像がありません。上で料理画像を生成してください。
        </div>
      ) : (
        <div className="library-grid">
          {images.map((img) => (
            <div
              key={img.id}
              className="library-item"
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData(DRAG_MIME, img.id);
                e.dataTransfer.effectAllowed = "copy";
              }}
              title={img.prompt}
            >
              <img src={img.url} alt={img.prompt} draggable={false} />
              <span className="library-caption">{img.prompt}</span>
              <button
                className="library-delete"
                onClick={() => onDelete(img.id)}
                title="削除"
                aria-label="削除"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
