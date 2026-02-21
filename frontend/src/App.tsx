import { useEffect, useState } from "react";
import "./App.css";
import PdfUploader from "./components/PdfUploader";
import ProductList, { Product } from "./components/ProductList";
import TemplateSelector, { Template } from "./components/TemplateSelector";
import PopPreview from "./components/PopPreview";
import { parsePdf, getTemplates, generatePop } from "./api/client";

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [parsing, setParsing] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    getTemplates().then((data) => {
      setTemplates(data.templates);
      if (data.templates.length > 0) {
        setSelectedTemplate(data.templates[0].template_id);
      }
    });
  }, []);

  const handleUpload = async (file: File) => {
    setParsing(true);
    try {
      const data = await parsePdf(file);
      setProducts(
        data.products.map((p: Omit<Product, "selected" | "tax_rate">) => ({
          ...p,
          selected: true,
          tax_rate: 1.08,
        }))
      );
    } catch (e) {
      alert("PDF解析に失敗しました: " + (e as Error).message);
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
    try {
      const blob = await generatePop(selectedTemplate, selected);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pop_output.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("POP生成に失敗しました: " + (e as Error).message);
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
