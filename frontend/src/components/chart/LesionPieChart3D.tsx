import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts";
import "echarts-gl";

import type { LesionFrequency } from "../../types/stats";
import GlassCard from "../ui/GlassCard";
import {
  buildPieSlices,
  createPieParametricEquation,
  formatArea,
  formatPercent,
  getOrderedFrequencyData,
  getTooltipPayload,
  hasFrequencySignal,
} from "./chart-utils";
import "./chart-frame.css";

interface LesionPieChart3DProps {
  data?: LesionFrequency[];
  loading?: boolean;
}

export default function LesionPieChart3D({ data, loading = false }: LesionPieChart3DProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const chartData = useMemo(() => getOrderedFrequencyData(data), [data]);
  const slices = useMemo(() => buildPieSlices(chartData), [chartData]);
  const hasData = hasFrequencySignal(chartData);

  useEffect(() => {
    if (!chartRef.current || !hasData) return undefined;

    const chart = echarts.init(chartRef.current);
    const resizeObserver = new ResizeObserver(() => chart.resize());
    resizeObserver.observe(chartRef.current);

    chart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        formatter: (params: unknown) => {
          const payload = getTooltipPayload(params);
          const slice = slices.find((item) => item.label === payload.seriesName);
          if (!slice) return "";
          return `${payload.marker ?? ""}${slice.label}<br/>病灶总数：${slice.totalCount} 处<br/>构成占比：${formatPercent(
            slice.ratio * 100,
          )}<br/>出现记录：${slice.count} 条<br/>面积合计：${formatArea(slice.totalArea)}`;
        },
      },
      xAxis3D: { min: -1.35, max: 1.35, show: false },
      yAxis3D: { min: -1.35, max: 1.35, show: false },
      zAxis3D: { min: -0.1, max: 0.34, show: false },
      grid3D: {
        show: false,
        boxHeight: 18,
        environment: "#f8fbff",
        viewControl: {
          alpha: 36,
          beta: 22,
          distance: 196,
          rotateSensitivity: 1.2,
          zoomSensitivity: 1,
        },
        light: {
          main: { intensity: 1.45, shadow: true, alpha: 36, beta: 18 },
          ambient: { intensity: 0.45 },
        },
        postEffect: {
          enable: true,
          bloom: { enable: false },
          SSAO: { enable: true, radius: 2, intensity: 1.2 },
        },
      },
      series: slices
        .filter((slice) => slice.ratio > 0 && slice.totalCount > 0)
        .map((slice) => ({
          name: slice.label,
          type: "surface",
          parametric: true,
          wireframe: { show: false },
          silent: false,
          itemStyle: {
            color: slice.color,
            opacity: 0.9,
          },
          parametricEquation: createPieParametricEquation(slice.startRatio, slice.endRatio, 0.18 + slice.ratio * 0.16),
        })),
    });

    return () => {
      resizeObserver.disconnect();
      chart.dispose();
    };
  }, [hasData, slices]);

  return (
    <GlassCard className="chart-frame">
      <div className="chart-frame__title">
        <div>
          <h2 className="chart-frame__heading">3D 病灶数量构成</h2>
          <span className="chart-frame__meta">按真实病灶总个数计算构成比例，不使用模板占比。</span>
        </div>
      </div>
      {loading ? (
        <div className="chart-frame__empty">
          <div>
            <strong>正在加载构成数据</strong>
            <span>请稍候</span>
          </div>
        </div>
      ) : hasData ? (
        <>
          <div ref={chartRef} className="chart-frame__surface" />
          <div className="chart-frame__legend">
            {slices.map((slice) => (
              <span key={slice.lesion} className="chart-frame__legend-item">
                <span className="chart-frame__dot" style={{ background: slice.color }} />
                {slice.label} {slice.totalCount} 处 / {formatPercent(slice.ratio * 100)}
              </span>
            ))}
          </div>
        </>
      ) : (
        <div className="chart-frame__empty">
          <div>
            <strong>暂无病灶构成数据</strong>
            <span>完成诊断后这里会显示 3D 构成图</span>
          </div>
        </div>
      )}
    </GlassCard>
  );
}
