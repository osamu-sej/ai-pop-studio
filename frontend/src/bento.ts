// 弁当箱のレイアウトプリセット定義。
// 各プリセットは CSS Grid で配置する（grid-template-areas のトークン = 仕切りの id）。
// BentoBox 側でインラインスタイルとして適用する。

export interface Compartment {
  id: string; // grid-area トークンも兼ねる（半角英数）
  label: string; // 仕切りの役割名
  hint: string; // 入れる料理の例
}

export interface BentoPreset {
  id: string;
  name: string;
  description: string;
  columns: string; // grid-template-columns
  rows: string; // grid-template-rows
  areas: string; // grid-template-areas
  aspectRatio: string; // 弁当箱の縦横比
  compartments: Compartment[];
}

export const PRESETS: BentoPreset[] = [
  {
    id: "makunouchi",
    name: "幕の内（6仕切り）",
    description: "ご飯・主菜・副菜3種・香の物",
    columns: "1.3fr 1fr 1fr",
    rows: "1fr 1fr 1fr",
    areas: `
      "rice main main"
      "rice side1 side2"
      "rice side3 pickles"
    `,
    aspectRatio: "3 / 2",
    compartments: [
      { id: "rice", label: "ご飯", hint: "白米・炊き込みご飯など" },
      { id: "main", label: "主菜", hint: "焼き魚・唐揚げなど" },
      { id: "side1", label: "副菜1", hint: "卵焼き・煮物など" },
      { id: "side2", label: "副菜2", hint: "和え物・揚げ物など" },
      { id: "side3", label: "副菜3", hint: "サラダ・酢の物など" },
      { id: "pickles", label: "香の物", hint: "漬物・梅干しなど" },
    ],
  },
  {
    id: "shokado",
    name: "松花堂（4仕切り）",
    description: "十字に区切った2×2の和の器",
    columns: "1fr 1fr",
    rows: "1fr 1fr",
    areas: `
      "main rice"
      "nimono kobachi"
    `,
    aspectRatio: "1 / 1",
    compartments: [
      { id: "main", label: "主菜", hint: "焼き魚・天ぷらなど" },
      { id: "rice", label: "ご飯", hint: "白米・赤飯など" },
      { id: "nimono", label: "煮物", hint: "炊き合わせなど" },
      { id: "kobachi", label: "小鉢", hint: "お造り・和え物など" },
    ],
  },
  {
    id: "split2",
    name: "2分割",
    description: "ご飯とおかずのシンプル弁当",
    columns: "1fr 1fr",
    rows: "1fr",
    areas: `"rice main"`,
    aspectRatio: "3 / 2",
    compartments: [
      { id: "rice", label: "ご飯", hint: "白米・のり弁など" },
      { id: "main", label: "おかず", hint: "メインのおかず" },
    ],
  },
  {
    id: "split3",
    name: "3分割",
    description: "横並びの3マス",
    columns: "1fr 1fr 1fr",
    rows: "1fr",
    areas: `"rice main side"`,
    aspectRatio: "5 / 2",
    compartments: [
      { id: "rice", label: "ご飯", hint: "白米など" },
      { id: "main", label: "主菜", hint: "メインのおかず" },
      { id: "side", label: "副菜", hint: "サブのおかず" },
    ],
  },
  {
    id: "jubako9",
    name: "重箱（9マス）",
    description: "おせち風の3×3マス",
    columns: "1fr 1fr 1fr",
    rows: "1fr 1fr 1fr",
    areas: `
      "c1 c2 c3"
      "c4 c5 c6"
      "c7 c8 c9"
    `,
    aspectRatio: "1 / 1",
    compartments: Array.from({ length: 9 }, (_, i) => ({
      id: `c${i + 1}`,
      label: `${i + 1}`,
      hint: "お好みの具材",
    })),
  },
];

export const DEFAULT_PRESET_ID = "makunouchi";

export function getPreset(id: string): BentoPreset {
  return PRESETS.find((p) => p.id === id) ?? PRESETS[0];
}
