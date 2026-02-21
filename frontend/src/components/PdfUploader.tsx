import { useCallback, useState } from "react";

type Props = {
  onUpload: (file: File) => void;
  loading: boolean;
};

export default function PdfUploader({ onUpload, loading }: Props) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file?.type === "application/pdf") {
        onUpload(file);
      }
    },
    [onUpload]
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
  };

  return (
    <section className="upload-section">
      <h2>1. PDFアップロード</h2>
      <div
        className={`drop-zone ${dragOver ? "drag-over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        {loading ? (
          <p>解析中...</p>
        ) : (
          <>
            <p>ドラッグ＆ドロップ</p>
            <p>または</p>
            <label className="file-label">
              ファイル選択
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                hidden
              />
            </label>
          </>
        )}
      </div>
    </section>
  );
}
