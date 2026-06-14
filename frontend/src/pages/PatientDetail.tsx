import { Table, Tag } from "antd";
import { Link, useParams } from "react-router-dom";

import GlassCard from "../components/ui/GlassCard";
import { useCurrentUser } from "../hooks/queries/useAuth";
import { useDiagnoses } from "../hooks/queries/useDiagnoses";
import { usePatient } from "../hooks/queries/usePatients";

export default function PatientDetail() {
  const currentUser = useCurrentUser();
  const routePatientId = Number(useParams().id);
  const patientId =
    Number.isFinite(routePatientId) && routePatientId > 0
      ? routePatientId
      : currentUser.data?.linked_patient_id ?? Number.NaN;
  const patient = usePatient(patientId);
  const diagnoses = useDiagnoses(patientId);

  if (currentUser.isLoading) return <GlassCard>正在验证登录状态...</GlassCard>;
  if (!Number.isFinite(patientId)) return <GlassCard>当前账号没有关联患者</GlassCard>;
  if (patient.isLoading) return <GlassCard>患者信息加载中...</GlassCard>;
  if (!patient.data) return <GlassCard>患者不存在或无权访问</GlassCard>;

  return (
    <>
      <h1 className="page-title">{patient.data.name}</h1>
      <p className="page-subtitle">
        {patient.data.patient_id} / {patient.data.gender} / {patient.data.age} 岁
        {currentUser.data?.role === "patient" ? <Tag style={{ marginLeft: 10 }}>病人视图</Tag> : null}
      </p>
      <GlassCard>
        <Table
          rowKey="id"
          loading={diagnoses.isLoading}
          dataSource={diagnoses.data?.diagnoses ?? []}
          pagination={{ pageSize: 8 }}
          columns={[
            { title: "时间", dataIndex: "created_at", render: (value: string) => new Date(value).toLocaleString() },
            { title: "评估", dataIndex: "severity" },
            { title: "HE", render: (_, record) => `${record.lesion_areas.HE}%` },
            { title: "EX", render: (_, record) => `${record.lesion_areas.EX}%` },
            { title: "MA", render: (_, record) => `${record.lesion_areas.MA}%` },
            { title: "SE", render: (_, record) => `${record.lesion_areas.SE}%` },
            { title: "操作", render: (_, record) => <Link to={`/diagnose/${record.id}`}>查看</Link> },
          ]}
        />
      </GlassCard>
    </>
  );
}
