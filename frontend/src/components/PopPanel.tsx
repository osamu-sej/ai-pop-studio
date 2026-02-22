import type { Product } from "./ProductList";
import ImageEditor from "./ImageEditor";

type Props = {
  products: Product[];
  editingIndex: number | null;
  onEditImage: (index: number) => void;
  onUpdatePhoto: (index: number, newPhoto: string) => void;
  onCloseEditor: () => void;
};

export default function PopPanel({
  products,
  editingIndex,
  onEditImage,
  onUpdatePhoto,
  onCloseEditor,
}: Props) {
  const selectedWithIndex = products
    .map((p, i) => ({ product: p, index: i }))
    .filter(({ product }) => product.selected);

  return (
    <div className="pop-panel">
      <div className="pop-panel-header">
        <h2>POPプレビュー</h2>
        <span className="pop-panel-hint">写真をクリックして編集</span>
      </div>

      {selectedWithIndex.length === 0 ? (
        <div className="pop-panel-empty">
          <div className="pop-frame-placeholder">
            <p>商品を選択すると<br />プレビューが表示されます</p>
          </div>
        </div>
      ) : (
        <div className="pop-cards">
          {selectedWithIndex.map(({ product: p, index }) => {
            const taxIncluded = Math.round(p.selling_price * p.tax_rate);
            const taxLabel = p.tax_rate === 1.08 ? "8%" : "10%";

            return (
              <div key={index} className="pop-card">
                {/* Photo area */}
                <div
                  className={`pop-card-photo${p.photo_base64 ? " clickable" : ""}`}
                  onClick={() => p.photo_base64 && onEditImage(index)}
                  title={p.photo_base64 ? "クリックして画像を編集" : ""}
                >
                  {p.photo_base64 ? (
                    <>
                      <img src={p.photo_base64} alt={p.product_name} />
                      <div className="pop-photo-overlay">
                        <span>✏ 編集</span>
                      </div>
                    </>
                  ) : (
                    <div className="pop-card-no-photo">写真なし</div>
                  )}
                </div>

                {/* Info area */}
                <div className="pop-card-info">
                  <div className="pop-price-row">
                    <span className="pop-price-excl">
                      ¥{p.selling_price.toLocaleString()}
                    </span>
                    <span className="pop-price-excl-label">税抜</span>
                  </div>
                  <div className="pop-price-incl">
                    ¥{taxIncluded.toLocaleString()}
                    <span className="pop-price-incl-label">税込（{taxLabel}）</span>
                  </div>
                  <div className="pop-name">{p.product_name || "（商品名未入力）"}</div>
                  {p.recommendation && (
                    <div className="pop-recommendation">{p.recommendation}</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {editingIndex !== null && products[editingIndex]?.photo_base64 && (
        <ImageEditor
          photoBase64={products[editingIndex].photo_base64}
          onSave={(newPhoto) => {
            onUpdatePhoto(editingIndex, newPhoto);
            onCloseEditor();
          }}
          onCancel={onCloseEditor}
        />
      )}
    </div>
  );
}
