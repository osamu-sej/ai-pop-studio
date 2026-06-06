import { useState } from "react";
import type { StoredImage } from "../api/client";
import { COMPARTMENTS } from "../bento";
import { DRAG_MIME } from "../dnd";

interface Props {
  // 仕切りID -> 画像ID
  layout: Record<string, string>;
  imagesById: Record<string, StoredImage>;
  onDrop: (compartmentId: string, imageId: string, fromCompartment?: string) => void;
  onClear: (compartmentId: string) => void;
}

export default function BentoBox({ layout, imagesById, onDrop, onClear }: Props) {
  const [dragOver, setDragOver] = useState<string | null>(null);

  return (
    <div className="bento-wrap">
      <div className="bento-box">
        {COMPARTMENTS.map((c) => {
          const imageId = layout[c.id];
          const image = imageId ? imagesById[imageId] : undefined;
          const isOver = dragOver === c.id;
          return (
            <div
              key={c.id}
              className={`compartment compartment-${c.id} ${isOver ? "compartment-over" : ""} ${
                image ? "compartment-filled" : ""
              }`}
              onDragOver={(e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = "copy";
                if (dragOver !== c.id) setDragOver(c.id);
              }}
              onDragLeave={() => setDragOver((prev) => (prev === c.id ? null : prev))}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(null);
                const droppedId = e.dataTransfer.getData(DRAG_MIME);
                if (!droppedId) return;
                const from = e.dataTransfer.getData("text/x-from-compartment");
                onDrop(c.id, droppedId, from || undefined);
              }}
            >
              {image ? (
                <div
                  className="compartment-image"
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData(DRAG_MIME, image.id);
                    e.dataTransfer.setData("text/x-from-compartment", c.id);
                    e.dataTransfer.effectAllowed = "move";
                  }}
                >
                  <img src={image.url} alt={image.prompt} draggable={false} />
                  <button
                    className="compartment-clear"
                    onClick={() => onClear(c.id)}
                    title="この仕切りを空にする"
                    aria-label="この仕切りを空にする"
                  >
                    ×
                  </button>
                </div>
              ) : (
                <div className="compartment-placeholder">
                  <span className="compartment-label">{c.label}</span>
                  <span className="compartment-hint">{c.hint}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
