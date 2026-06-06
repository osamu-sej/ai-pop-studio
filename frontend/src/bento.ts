// 幕の内弁当の仕切り定義。
// grid-template-areas で配置する（App.css 側と area 名を一致させる）。

export interface Compartment {
  id: string;
  label: string; // 仕切りの役割名
  hint: string; // 入れる料理の例
}

export const COMPARTMENTS: Compartment[] = [
  { id: "rice", label: "ご飯", hint: "白米・炊き込みご飯など" },
  { id: "main", label: "主菜", hint: "焼き魚・唐揚げなど" },
  { id: "side1", label: "副菜1", hint: "卵焼き・煮物など" },
  { id: "side2", label: "副菜2", hint: "和え物・揚げ物など" },
  { id: "side3", label: "副菜3", hint: "サラダ・酢の物など" },
  { id: "pickles", label: "香の物", hint: "漬物・梅干しなど" },
];
