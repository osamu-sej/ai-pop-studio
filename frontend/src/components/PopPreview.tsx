type Props = {
  canGenerate: boolean;
  onGenerate: () => void;
  generating: boolean;
};

export default function PopPreview({
  canGenerate,
  onGenerate,
  generating,
}: Props) {
  return (
    <section className="generate-section">
      <h2>4. POP生成</h2>
      <button
        className="generate-btn"
        disabled={!canGenerate || generating}
        onClick={onGenerate}
      >
        {generating ? "生成中..." : "POP生成・ダウンロード"}
      </button>
    </section>
  );
}
