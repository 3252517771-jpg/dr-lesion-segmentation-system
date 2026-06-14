import { Space } from "antd";

import { LESION_COLORS, LESION_LABELS, LESION_ORDER } from "../../types/diagnosis";

export default function LesionLegend() {
  return (
    <Space wrap>
      {LESION_ORDER.map((lesion) => (
        <span key={lesion} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: 10, background: LESION_COLORS[lesion] }} />
          {LESION_LABELS[lesion]}
        </span>
      ))}
    </Space>
  );
}
