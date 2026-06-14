import { Button, Form, Input, Tabs } from "antd";
import { useParams } from "react-router-dom";

import { updateDiagnosisNotes } from "../api/diagnoses";
import DiagnosisReport from "../components/diagnosis/DiagnosisReport";
import LesionContour from "../components/diagnosis/LesionContour";
import GlassCard from "../components/ui/GlassCard";
import { useDiagnosis } from "../hooks/queries/useDiagnoses";

export default function DiagnosisDetail() {
  const params = useParams();
  const diagnosisId = Number(params.id);
  const diagnosis = useDiagnosis(diagnosisId);

  if (diagnosis.isLoading) return <GlassCard>加载中...</GlassCard>;
  if (!diagnosis.data) return <GlassCard>诊断记录不存在</GlassCard>;

  return (
    <>
      <h1 className="page-title">Diagnosis Detail</h1>
      <div className="content-grid two-column">
        <GlassCard>
          <DiagnosisReport diagnosis={diagnosis.data} />
          <Form
            layout="vertical"
            style={{ marginTop: 18 }}
            initialValues={{ notes: diagnosis.data.notes }}
            onFinish={async (values) => {
              await updateDiagnosisNotes(diagnosisId, values.notes);
              diagnosis.refetch();
            }}
          >
            <Form.Item label="备注" name="notes">
              <Input.TextArea rows={3} />
            </Form.Item>
            <Button htmlType="submit">保存备注</Button>
          </Form>
        </GlassCard>
        <GlassCard>
          <Tabs
            items={[
              { key: "contour", label: "病灶图", children: <LesionContour imageUrl={diagnosis.data.contour_url} /> },
              { key: "original", label: "原图", children: <LesionContour imageUrl={diagnosis.data.image_url} /> },
              { key: "three", label: "3D 分布", children: <div>3D 组件将在 M7 接入</div> },
            ]}
          />
        </GlassCard>
      </div>
    </>
  );
}
