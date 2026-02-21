export type Product = {
  product_name: string;
  selling_price: number;
  description: string;
  photo_base64: string;
  page_number: number;
  selected: boolean;
  tax_rate: number;
};

type Props = {
  products: Product[];
  onToggle: (index: number) => void;
  onUpdate: (index: number, field: keyof Product, value: unknown) => void;
};

export default function ProductList({ products, onToggle, onUpdate }: Props) {
  if (products.length === 0) return null;

  return (
    <section className="product-section">
      <h2>2. 商品一覧（抽出結果）</h2>
      <table className="product-table">
        <thead>
          <tr>
            <th>選択</th>
            <th>写真</th>
            <th>商品名</th>
            <th>売価（税抜）</th>
            <th>税率</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p, i) => (
            <tr key={i} className={p.selected ? "" : "unselected"}>
              <td>
                <input
                  type="checkbox"
                  checked={p.selected}
                  onChange={() => onToggle(i)}
                />
              </td>
              <td className="photo-cell">
                {p.photo_base64 ? (
                  <img src={p.photo_base64} alt={p.product_name} />
                ) : (
                  <span className="no-photo">--</span>
                )}
              </td>
              <td>
                <input
                  type="text"
                  value={p.product_name}
                  onChange={(e) => onUpdate(i, "product_name", e.target.value)}
                />
              </td>
              <td>
                <input
                  type="number"
                  value={p.selling_price}
                  onChange={(e) =>
                    onUpdate(i, "selling_price", Number(e.target.value))
                  }
                />
              </td>
              <td>
                <select
                  value={p.tax_rate}
                  onChange={(e) =>
                    onUpdate(i, "tax_rate", Number(e.target.value))
                  }
                >
                  <option value={1.08}>8%</option>
                  <option value={1.1}>10%</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
