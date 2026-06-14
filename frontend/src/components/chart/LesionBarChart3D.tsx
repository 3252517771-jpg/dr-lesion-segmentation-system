import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts";
import "echarts-gl";

import type { LesionFrequency } from "../../types/stats";
import GlassCard from "../ui/GlassCard";
import { formatArea, formatPercent, getOrderedFrequencyData, hasFrequencySignal } from "./chart-utils";
import "./chart-frame.css";

interface LesionBarChart3DProps {
  data?: LesionFrequency[];
  loading?: boolean;
}

export default function LesionBarChart3D({ data, loading = false }: LesionBarChart3DProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const chartData = useMemo(() => getOrderedFrequencyData(data), [data]);
  const hasData = hasFrequencySignal(chartData);

  useEffect(() => {
    if (!chartRef.current || !hasData) return undefined;

    const chart = echarts.init(chartRef.current);
    const resizeObserver = new ResizeObserver(() => chart.resize());
    resizeObserver.observe(chartRef.current);

    chart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        formatter: (params: unknown) => {
          const value = (params as { value?: [string, string, number, number, number, number] }).value;
          if (!value) return "";
          return `${value[0]}<br/>病灶总数：${value[2]} 处<br/>出现记录：${value[3]} 条<br/>覆盖比例：${formatPercent(
            value[4],
          )}<br/>面积合计：${formatArea(value[5])}`;
        },
      },
      xAxis3D: {
        type: "category",
        name: "",
        data: chartData.map((item) => item.label),
        axisLabel: { color: "#506078", interval: 0 },
        axisLine: { lineStyle: { color: "rgba(80, 96, 120, 0.42)" } },
      },
      yAxis3D: {
        type: "category",
        name: "",
        data: ["病灶总数"],
        axisLabel: { color: "#506078" },
        axisLine: { lineStyle: { color: "rgba(80, 96, 120, 0.32)" } },
      },
      zAxis3D: {
        type: "value",
        name: "数量",
        minInterval: 1,
        axisLabel: { color: "#506078" },
        axisLine: { lineStyle: { color: "rgba(80, 96, 120, 0.32)" } },
        splitLine: { lineStyle: { color: "rgba(80, 96, 120, 0.12)" } },
      },
      grid3D: {
        boxWidth: 104,
        boxDepth: 28,
        boxHeight: 72,
        top: -12,
        viewControl: {
          projection: "perspective",
          alpha: 24,
          beta: -36,
          distance: 168,
          autoRotate: true,
          autoRotateSpeed: 2.6,
        },
        light: {
          main: { intensity: 1.35, shadow: true, alpha: 34, beta: 24 },
          ambient: { intensity: 0.5 },
        },
        axisPointer: { show: false },
        environment: "#f8fbff",
      },
      series: [
        {
          type: "bar3D",
          name: "病灶数量",
          barSize: 18,
          bevelSize: 0.28,
          bevelSmoothness: 4,
          shading: "lambert",
          label: {
            show: true,
            formatter: (params: { value: [string, string, number, number, number, number] }) => `${params.value[2]}`,
            color: "#14213d",
            distance: 2,
            fontWeight: 700,
          },
          data: chartData.map((item) => ({
            value: [item.label, "病灶总数", item.totalCount, item.count, item.percentage, item.totalArea],
            itemStyle: {
              color: item.color,
              opacity: 0.92,
            },
          })),
        },
      ],
    });

    return () => {
      resizeObserver.disconnect();
      chart.dispose();
    };
  }, [chartData, hasData]);

  return (
    <GlassCard className="chart-frame">
      <div className="chart-frame__title">
        <div>
          <h2 className="chart-frame__heading">3D 病灶数量分布</h2>
          <span className="chart-frame__meta">柱高表示当前诊断记录内各类病灶总个数，覆盖率作为辅助信息。</span>
        </div>
      </div>
      {loading ? (
        <div className="chart-frame__empty">
          <div>
            <strong>正在加载统计数据</strong>
            <span>请稍候</span>
          </div>
        </div>
      ) : hasData ? (
        <>
          <div ref={chartRef} className="chart-frame__surface is-tall" />
          <div className="chart-frame__legend">
            {chartData.map((item) => (
              <span key={item.lesion} className="chart-frame__legend-item">
                <span className="chart-frame__dot" style={{ background: item.color }} />
                {item.label} {item.totalCount} 处 / 覆盖 {formatPercent(item.percentage)}
              </span>
            ))}
          </div>
        </>
      ) : (
        <div className="chart-frame__empty">
          <div>
            <strong>暂无病灶数量数据</strong>
            <span>完成诊断后这里会显示 3D 统计柱状图</span>
          </div>
        </div>
      )}
    </GlassCard>
  );
}
