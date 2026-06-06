import { PRESETS } from "../bento";

interface Props {
  selected: string;
  onSelect: (presetId: string) => void;
}

export default function PresetSelector({ selected, onSelect }: Props) {
  return (
    <div className="preset-selector">
      <span className="preset-label">弁当箱:</span>
      <div className="preset-chips">
        {PRESETS.map((p) => (
          <button
            key={p.id}
            type="button"
            className={`preset-chip ${selected === p.id ? "preset-chip-active" : ""}`}
            onClick={() => onSelect(p.id)}
            title={p.description}
          >
            {p.name}
          </button>
        ))}
      </div>
    </div>
  );
}
