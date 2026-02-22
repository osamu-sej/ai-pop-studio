import { useRef, useState } from "react";

type Selection = { x: number; y: number; width: number; height: number };

type Props = {
  photoBase64: string;
  onSave: (newBase64: string) => void;
  onCancel: () => void;
};

export default function ImageEditor({ photoBase64, onSave, onCancel }: Props) {
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [saturation, setSaturation] = useState(100);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  const getRelativePos = (e: React.MouseEvent) => {
    const rect = containerRef.current!.getBoundingClientRect();
    const imgRect = imgRef.current!.getBoundingClientRect();
    // Clamp to image bounds within container
    const x = Math.max(0, Math.min(e.clientX - imgRect.left, imgRect.width));
    const y = Math.max(0, Math.min(e.clientY - imgRect.top, imgRect.height));
    // Offset relative to container
    const ox = imgRect.left - rect.left;
    const oy = imgRect.top - rect.top;
    return { x: x + ox, y: y + oy, ox, oy, iw: imgRect.width, ih: imgRect.height };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!imgRef.current) return;
    const pos = getRelativePos(e);
    setDragStart({ x: pos.x, y: pos.y });
    setSelection({ x: pos.x, y: pos.y, width: 0, height: 0 });
    setIsDragging(true);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging || !imgRef.current) return;
    const pos = getRelativePos(e);
    const x = Math.min(dragStart.x, pos.x);
    const y = Math.min(dragStart.y, pos.y);
    setSelection({
      x,
      y,
      width: Math.abs(pos.x - dragStart.x),
      height: Math.abs(pos.y - dragStart.y),
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleApply = () => {
    const img = new Image();
    img.onload = () => {
      const displayImg = imgRef.current;
      if (!displayImg) return;
      const displayW = displayImg.width;
      const displayH = displayImg.height;
      const scaleX = img.naturalWidth / displayW;
      const scaleY = img.naturalHeight / displayH;

      // Offset of image within container
      const containerRect = containerRef.current!.getBoundingClientRect();
      const imgRect = displayImg.getBoundingClientRect();
      const ox = imgRect.left - containerRect.left;
      const oy = imgRect.top - containerRect.top;

      let cropX = 0,
        cropY = 0,
        cropW = img.naturalWidth,
        cropH = img.naturalHeight;

      if (selection && selection.width > 10 && selection.height > 10) {
        cropX = (selection.x - ox) * scaleX;
        cropY = (selection.y - oy) * scaleY;
        cropW = selection.width * scaleX;
        cropH = selection.height * scaleY;
        // Clamp to natural dimensions
        cropX = Math.max(0, cropX);
        cropY = Math.max(0, cropY);
        cropW = Math.min(cropW, img.naturalWidth - cropX);
        cropH = Math.min(cropH, img.naturalHeight - cropY);
      }

      const canvas = document.createElement("canvas");
      canvas.width = Math.round(cropW);
      canvas.height = Math.round(cropH);
      const ctx = canvas.getContext("2d")!;
      ctx.filter = `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`;
      ctx.drawImage(img, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH);
      onSave(canvas.toDataURL("image/png"));
    };
    img.src = photoBase64;
  };

  const handleReset = () => {
    setBrightness(100);
    setContrast(100);
    setSaturation(100);
    setSelection(null);
  };

  const hasCrop = selection && selection.width > 10 && selection.height > 10;

  return (
    <div className="ie-modal" onClick={(e) => e.target === e.currentTarget && onCancel()}>
      <div className="ie-content">
        <div className="ie-header">
          <h3>画像編集</h3>
          <button className="ie-close" onClick={onCancel}>×</button>
        </div>

        <p className="ie-hint">ドラッグしてトリミング範囲を選択できます</p>

        <div
          className="ie-canvas-wrap"
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <img
            ref={imgRef}
            src={photoBase64}
            alt="編集中"
            className="ie-img"
            style={{
              filter: `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`,
            }}
            draggable={false}
          />
          {hasCrop && (
            <div
              className="ie-crop-overlay"
              style={{
                left: selection!.x,
                top: selection!.y,
                width: selection!.width,
                height: selection!.height,
              }}
            />
          )}
        </div>

        {hasCrop && (
          <p className="ie-crop-info">
            トリミング選択中 —
            <button className="ie-crop-clear" onClick={() => setSelection(null)}>
              選択解除
            </button>
          </p>
        )}

        <div className="ie-controls">
          <div className="ie-control-row">
            <label>明るさ</label>
            <input
              type="range"
              min={50}
              max={150}
              value={brightness}
              onChange={(e) => setBrightness(Number(e.target.value))}
            />
            <span className="ie-value">{brightness}%</span>
          </div>
          <div className="ie-control-row">
            <label>コントラスト</label>
            <input
              type="range"
              min={50}
              max={150}
              value={contrast}
              onChange={(e) => setContrast(Number(e.target.value))}
            />
            <span className="ie-value">{contrast}%</span>
          </div>
          <div className="ie-control-row">
            <label>彩度</label>
            <input
              type="range"
              min={0}
              max={200}
              value={saturation}
              onChange={(e) => setSaturation(Number(e.target.value))}
            />
            <span className="ie-value">{saturation}%</span>
          </div>
        </div>

        <div className="ie-actions">
          <button className="ie-btn-reset" onClick={handleReset}>
            リセット
          </button>
          <button className="ie-btn-cancel" onClick={onCancel}>
            キャンセル
          </button>
          <button className="ie-btn-apply" onClick={handleApply}>
            適用
          </button>
        </div>
      </div>
    </div>
  );
}
