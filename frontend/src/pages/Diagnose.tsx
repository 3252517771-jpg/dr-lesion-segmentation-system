import { Button, Form, Input, InputNumber, Select, Upload, message } from "antd";
import type { UploadFile } from "antd";
import { UploadCloud } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import DiagnosisReport from "../components/diagnosis/DiagnosisReport";
import LesionContour from "../components/diagnosis/LesionContour";
import GlassCard from "../components/ui/GlassCard";
import { useDiagnose } from "../hooks/mutations/useDiagnose";
import { useCreatePatient } from "../hooks/mutations/usePatientMutations";
import { usePatients } from "../hooks/queries/usePatients";
import type { DiagnosisResult } from "../types/diagnosis";

const { Dragger } = Upload;

export default function Diagnose() {
  const [form] = Form.useForm();
  const patients = usePatients();
  const diagnose = useDiagnose();
  const createPatient = useCreatePatient();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [result, setResult] = useState<{ diagnosis: DiagnosisResult; mode: string } | null>(null);

  const patientOptions = useMemo(
    () => patients.data?.patients.map((patient) => ({ value: patient.id, label: `${patient.name} (${patient.patient_id})` })) ?? [],
    [patients.data],
  );

  async function handleCreatePatient(values: { name: string; gender: string; age: number; patient_id: string }) {
    const patient = await createPatient.mutateAsync(values);
    form.setFieldValue("patient_id", patient.id);
    message.success("患者已创建");
  }

  async function handleDiagnose() {
    const patientId = form.getFieldValue("patient_id");
    const file = fileList[0]?.originFileObj;
    if (!patientId || !file) {
      message.warning("请选择患者并上传图片");
      return;
    }
    const response = await diagnose.mutateAsync({ patientId, file });
    setResult(response);
    message.success("诊断完成");
  }

  return (
    <>
      <h1 className="page-title">Diagnose</h1>
      <p className="page-subtitle">上传眼底图像，生成四类病灶量化报告</p>
      <div className="content-grid two-column">
        <GlassCard>
          <Form form={form} layout="vertical">
            <Form.Item label="选择患者" name="patient_id">
              <Select options={patientOptions} loading={patients.isLoading} placeholder="选择已有患者" />
            </Form.Item>
            <Dragger
              maxCount={1}
              accept=".jpg,.jpeg,.png,.bmp,.webp"
              fileList={fileList}
              beforeUpload={() => false}
              onChange={({ fileList: next }) => setFileList(next)}
            >
              <p>
                <UploadCloud size={32} />
              </p>
              <p>拖拽或点击上传眼底图片</p>
            </Dragger>
            <Button
              type="primary"
              size="large"
              block
              style={{ marginTop: 18 }}
              loading={diagnose.isPending}
              onClick={handleDiagnose}
            >
              开始诊断
            </Button>
          </Form>
        </GlassCard>
        <GlassCard>
          <Form layout="vertical" onFinish={handleCreatePatient}>
            <Form.Item label="姓名" name="name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item label="病历号" name="patient_id" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item label="性别" name="gender" rules={[{ required: true }]}>
              <Select options={[{ value: "男" }, { value: "女" }]} />
            </Form.Item>
            <Form.Item label="年龄" name="age" rules={[{ required: true }]}>
              <InputNumber min={0} max={150} style={{ width: "100%" }} />
            </Form.Item>
            <Button htmlType="submit" loading={createPatient.isPending}>创建患者</Button>
          </Form>
        </GlassCard>
      </div>
      {result ? (
        <div className="content-grid two-column" style={{ marginTop: 16 }}>
          <GlassCard>
            <DiagnosisReport diagnosis={result.diagnosis} mode={result.mode} />
            <Link to={`/diagnose/${result.diagnosis.id}`}>查看完整详情</Link>
          </GlassCard>
          <GlassCard>
            <LesionContour imageUrl={result.diagnosis.contour_url} />
          </GlassCard>
        </div>
      ) : null}
    </>
  );
}
