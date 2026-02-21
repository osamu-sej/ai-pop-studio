export type Template = {
  template_id: string;
  name: string;
  products_per_sheet: number;
  total_sheets: number;
};

type Props = {
  templates: Template[];
  selected: string;
  onSelect: (id: string) => void;
};

export default function TemplateSelector({
  templates,
  selected,
  onSelect,
}: Props) {
  if (templates.length === 0) return null;

  return (
    <section className="template-section">
      <h2>3. テンプレート選択</h2>
      <div className="template-options">
        {templates.map((t) => (
          <label key={t.template_id} className="template-option">
            <input
              type="radio"
              name="template"
              value={t.template_id}
              checked={selected === t.template_id}
              onChange={() => onSelect(t.template_id)}
            />
            <span>{t.name}</span>
            <small>（1シート{t.products_per_sheet}商品）</small>
          </label>
        ))}
      </div>
    </section>
  );
}
