import { Suspense, lazy } from "react";
import { Table, Tag, type TableColumnsType } from "antd";
import { Link } from "react-router-dom";

import GlassCard from "../components/ui/GlassCard";
import StatCard from "../components/ui/StatCard";
import { useDiagnoses } from "../hooks/queries/useDiagnoses";
import { useHealth } from "../hooks/queries/useHealth";
import { useLesionFrequencies, useStatsOverview, useTrend } from "../hooks/queries/useStats";
import { LESION_COLORS, LESION_LABELS, type DiagnosisResult, type LesionKey } from "../types/diagnosis";
import "./dashboard.css";

const DashboardCharts3D = lazy(() => import("../components/chart/DashboardCharts3D"));

function isLesionKey(value: string): value is LesionKey {
  return Object.prototype.hasOwnProperty.call(LESION_LABELS, value);
}

const diagnosisColumns: TableColumnsType<DiagnosisResult> = [
  { title: "患者", dataIndex: "patient_name" },
  { title: "评估", dataIndex: "severity" },
  {
    title: "操作",
    render: (_, record) => <Link to={`/diagnose/${record.id}`}>查看</Link>,
  },
];

export default function Dashboard() {
  const health = useHealth();
  const overview = useStatsOverview();
  const lesions = useLesionFrequencies();
  const trend = useTrend(30);
  const diagnoses = useDiagnoses();
  const frequencies = lesions.data?.lesion_frequencies ?? [];

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">糖尿病视网膜病变病灶分割诊断系统</p>

      <div className="dashboard-grid dashboard-stats">
        <StatCard title="总诊断数" value={overview.data?.total_diagnoses ?? "-"} />
        <StatCard title="今日诊断" value={overview.data?.today_diagnoses ?? "-"} />
        <StatCard title="患者总数" value={overview.data?.total_patients ?? "-"} />
        <StatCard
          title="推理模式"
          value={<Tag color={health.data?.model_loaded ? "green" : "gold"}>{health.data?.model_backend ?? "-"}</Tag>}
        />
      </div>

      <Suspense
        fallback={
          <GlassCard className="dashboard-chart-loading">
            <strong>正在加载 3D 统计图表</strong>
            <span>首次进入 Dashboard 时会按需载入 ECharts GL</span>
          </GlassCard>
        }
      >
        <DashboardCharts3D
          frequencies={frequencies}
          frequenciesLoading={lesions.isLoading}
          trend={trend.data?.trend ?? []}
          trendLoading={trend.isLoading}
        />
      </Suspense>

      <div className="dashboard-recent">
        <GlassCard>
          <div className="dashboard-card-title">
            <h2>最近诊断</h2>
            <span>展示最新 6 条诊断记录</span>
          </div>
          <Table
            rowKey="id"
            pagination={false}
            loading={diagnoses.isLoading}
            dataSource={diagnoses.data?.diagnoses.slice(0, 6) ?? []}
            columns={diagnosisColumns}
          />
        </GlassCard>
      </div>

      <div className="dashboard-recent">
        <GlassCard>
          <div className="dashboard-card-title">
            <h2>病灶统计明细</h2>
            <span>总数、覆盖率和面积均来自统计接口</span>
          </div>
          <div className="dashboard-frequency-list">
            {frequencies.map((item) => {
              const lesion = isLesionKey(item.lesion_type) ? item.lesion_type : "HE";
              return (
                <div key={item.lesion_type} className="dashboard-frequency-item">
                  <div className="dashboard-frequency-label">
                    <span className="dashboard-frequency-dot" style={{ background: LESION_COLORS[lesion] }} />
                    {LESION_LABELS[lesion]}
                  </div>
                  <div className="dashboard-frequency-value">{item.total_count}</div>
                  <div className="dashboard-frequency-meta">
                    {item.count} 条记录 / 覆盖 {item.percentage.toFixed(2)}% / 面积 {item.total_area.toFixed(4)}%
                  </div>
                </div>
              );
            })}
          </div>
        </GlassCard>
      </div>
    </>
  );
}
