import { Table } from "antd";
import { Link, useParams } from "react-router-dom";

import GlassCard from "../components/ui/GlassCard";
import { useDiagnoses } from "../hooks/queries/useDiagnoses";
import { usePatient } from "../hooks/queries/usePatients";

export default function PatientDetail() {
  const patientId = Number(useParams().id);
  const patient = usePatient(patientId);
  const diagnoses = useDiagnoses(patientId);

  if (patient.isLoading) return <GlassCard>加载中...</GlassCard>;
  if (!patient.data) return <GlassCard>患者不存在</GlassCard>;

  return (
    <>
      <h1 className="page-title">{patient.data.name}</h1>
      <p className="page-subtitle">
        {patient.data.patient_id} / {patient.data.gender} / {patient.data.age} 岁
      </p>
      <GlassCard>
        <Table
          rowKey="id"
          loading={diagnoses.isLoading}
          dataSource={diagnoses.data?.diagnoses ?? []}
          columns={[
            { title: "时间", dataIndex: "created_at" },
            { title: "评估", dataIndex: "severity" },
            { title: "HE", render: (_, record) => `${record.lesion_areas.HE}%` },
            { title: "EX", render: (_, record) => `${record.lesion_areas.EX}%` },
            { title: "操作", render: (_, record) => <Link to={`/diagnose/${record.id}`}>查看</Link> },
          ]}
        />
      </GlassCard>
    </>
  );
}
