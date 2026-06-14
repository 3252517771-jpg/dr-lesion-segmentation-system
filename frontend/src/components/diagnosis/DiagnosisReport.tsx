import { Descriptions, Tag, Typography } from "antd";

import { LESION_LABELS, LESION_ORDER, type DiagnosisResult } from "../../types/diagnosis";
import LesionLegend from "./LesionLegend";

interface DiagnosisReportProps {
  diagnosis: DiagnosisResult;
  mode?: string;
}

function severityColor(severity: string) {
  if (severity.includes("重度")) return "red";
  if (severity.includes("中度")) return "orange";
  if (severity.includes("轻度")) return "gold";
  return "green";
}

export default function DiagnosisReport({ diagnosis, mode }: DiagnosisReportProps) {
  return (
    <div>
      <Typography.Title level={4} style={{ marginTop: 0 }}>
        量化诊断报告
      </Typography.Title>
      <LesionLegend />
      <Descriptions bordered column={1} size="middle" style={{ marginTop: 16 }}>
        <Descriptions.Item label="患者">{diagnosis.patient_name || `#${diagnosis.patient_id}`}</Descriptions.Item>
        <Descriptions.Item label="综合评估">
          <Tag color={severityColor(diagnosis.severity)}>{diagnosis.severity}</Tag>
          {mode ? <Tag>{mode}</Tag> : null}
        </Descriptions.Item>
        {LESION_ORDER.map((lesion) => (
          <Descriptions.Item key={lesion} label={LESION_LABELS[lesion]}>
            {diagnosis.lesion_counts[lesion]} 处 / {diagnosis.lesion_areas[lesion].toFixed(4)}%
          </Descriptions.Item>
        ))}
      </Descriptions>
    </div>
  );
}
