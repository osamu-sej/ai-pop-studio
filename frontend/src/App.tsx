import { useEffect, useState } from "react";
import "./App.css";
import PdfUploader from "./components/PdfUploader";
import ProductList from "./components/ProductList";
import type { Product } from "./components/ProductList";
import TemplateSelector from "./components/TemplateSelector";
import type { Template } from "./components/TemplateSelector";
import PopPreview from "./components/PopPreview";
import { parsePdf, getTemplates, generatePop } from "./api/client";

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [parsing, setParsing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTemplates()
      .then((data) => {
        setTemplates(data.templates);
        if (data.templates.length > 0) {
          setSelectedTemplate(data.templates[0].template_id);
        }
      })
      .catch(() => {
        setError("テンプレート一覧の取得に失敗しました。バックエンドが起動しているか確認してください。");
      });
  }, []);

  const handleUpload = async (file: File) => {
    setParsing(true);
    setError(null);
    try {
      const data = await parsePdf(file);
      setProducts(
        data.products.map(
          (p: Record<string, unknown>) => ({
            product_name: p.product_name ?? "",
            selling_price: p.selling_price ?? 0,
            description: p.description ?? "",
            recommendation: (p.description as string) ?? "",
            photo_base64: p.photo_base64 ?? "",
            page_number: p.page_number ?? 0,
            selected: true,
            tax_rate: 1.08,
          }) as Product
        )
      );
    } catch (e) {
      setError("PDF解析に失敗しました: " + (e as Error).message);
    } finally {
      setParsing(false);
    }
  };

  const handleToggle = (index: number) => {
    setProducts((prev) =>
      prev.map((p, i) => (i === index ? { ...p, selected: !p.selected } : p))
    );
  };

  const handleUpdate = (
    index: number,
    field: keyof Product,
    value: unknown
  ) => {
    setProducts((prev) =>
      prev.map((p, i) => (i === index ? { ...p, [field]: value } : p))
    );
  };

  const handleGenerate = async () => {
    const selected = products.filter((p) => p.selected);
    if (selected.length === 0) return;

    setGenerating(true);
    setError(null);
    try {
      const blob = await generatePop(selectedTemplate, selected);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pop_output.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError("POP生成に失敗しました: " + (e as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  const canGenerate =
    products.some((p) => p.selected) && selectedTemplate !== "";

  return (
    <div className="app">
      <header className="app-header">
        <h1>POP Generator</h1>
        <p className="subtitle">セブンイレブン POP自動生成</p>
      </header>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button className="error-close" onClick={() => setError(null)}>
            &times;
          </button>
        </div>
      )}

      <main className="app-main">
        <PdfUploader onUpload={handleUpload} loading={parsing} />
        <ProductList
          products={products}
          onToggle={handleToggle}
          onUpdate={handleUpdate}
        />
        <TemplateSelector
          templates={templates}
          selected={selectedTemplate}
          onSelect={setSelectedTemplate}
        />
        <PopPreview
          canGenerate={canGenerate}
          onGenerate={handleGenerate}
          generating={generating}
        />
      </main>
    </div>
  );
}

export default App;
