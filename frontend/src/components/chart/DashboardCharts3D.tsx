import type { LesionFrequency, TrendPoint } from "../../types/stats";
import LesionBarChart3D from "./LesionBarChart3D";
import LesionPieChart3D from "./LesionPieChart3D";
import LesionTrendChart3D from "./LesionTrendChart3D";

interface DashboardCharts3DProps {
  frequencies: LesionFrequency[];
  frequenciesLoading: boolean;
  trend: TrendPoint[];
  trendLoading: boolean;
}

export default function DashboardCharts3D({
  frequencies,
  frequenciesLoading,
  trend,
  trendLoading,
}: DashboardCharts3DProps) {
  return (
    <>
      <div className="dashboard-main-chart">
        <LesionBarChart3D data={frequencies} loading={frequenciesLoading} />
      </div>

      <div className="dashboard-grid dashboard-chart-row" style={{ marginTop: 16 }}>
        <LesionPieChart3D data={frequencies} loading={frequenciesLoading} />
        <LesionTrendChart3D data={trend} loading={trendLoading} />
      </div>
    </>
  );
}
