import { List, Table, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

import GlassCard from "../components/ui/GlassCard";
import StatCard from "../components/ui/StatCard";
import { useDiagnoses } from "../hooks/queries/useDiagnoses";
import { useHealth } from "../hooks/queries/useHealth";
import { useLesionFrequencies, useStatsOverview } from "../hooks/queries/useStats";
import { LESION_LABELS } from "../types/diagnosis";

export default function Dashboard() {
  const health = useHealth();
  const overview = useStatsOverview();
  const lesions = useLesionFrequencies();
  const diagnoses = useDiagnoses();

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">糖尿病视网膜病变病灶分割诊断系统</p>
      <div className="content-grid" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
        <StatCard title="总诊断数" value={overview.data?.total_diagnoses ?? "-"} />
        <StatCard title="今日诊断" value={overview.data?.today_diagnoses ?? "-"} />
        <StatCard title="患者总数" value={overview.data?.total_patients ?? "-"} />
        <StatCard
          title="推理模式"
          value={<Tag color={health.data?.model_loaded ? "green" : "gold"}>{health.data?.model_backend ?? "-"}</Tag>}
        />
      </div>
      <div className="content-grid two-column" style={{ marginTop: 16 }}>
        <GlassCard>
          <Typography.Title level={4} style={{ marginTop: 0 }}>
            最近诊断
          </Typography.Title>
          <Table
            rowKey="id"
            pagination={false}
            dataSource={diagnoses.data?.diagnoses.slice(0, 6) ?? []}
            columns={[
              { title: "患者", dataIndex: "patient_name" },
              { title: "评估", dataIndex: "severity" },
              {
                title: "操作",
                render: (_, record) => <Link to={`/diagnose/${record.id}`}>查看</Link>,
              },
            ]}
          />
        </GlassCard>
        <GlassCard>
          <Typography.Title level={4} style={{ marginTop: 0 }}>
            病灶频率
          </Typography.Title>
          <List
            dataSource={lesions.data?.lesion_frequencies ?? []}
            renderItem={(item) => (
              <List.Item>
                <span>{LESION_LABELS[item.lesion_type as keyof typeof LESION_LABELS]}</span>
                <Tag>{item.count} 例 / {item.percentage}%</Tag>
              </List.Item>
            )}
          />
        </GlassCard>
      </div>
    </>
  );
}
