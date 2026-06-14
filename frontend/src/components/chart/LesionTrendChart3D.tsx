import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts";
import "echarts-gl";

import { LESION_COLORS, LESION_LABELS, LESION_ORDER } from "../../types/diagnosis";
import type { TrendPoint } from "../../types/stats";
import GlassCard from "../ui/GlassCard";
import { compactDate, formatArea, getTooltipPayload, hasTrendSignal } from "./chart-utils";
import "./chart-frame.css";

interface LesionTrendChart3DProps {
  data?: TrendPoint[];
  loading?: boolean;
}

export default function LesionTrendChart3D({ data = [], loading = false }: LesionTrendChart3DProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const hasData = hasTrendSignal(data);
  const dates = useMemo(() => data.map((item) => compactDate(item.date)), [data]);

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
          const value = payload.value as [string, string, number] | undefined;
          if (!value) return "";
          return `${payload.marker ?? ""}${value[0]}<br/>${value[1]}：${formatArea(value[2])}`;
        },
      },
      legend: {
        top: 0,
        right: 0,
        textStyle: { color: "#506078" },
        itemWidth: 9,
        itemHeight: 9,
      },
      xAxis3D: {
        type: "category",
        name: "日期",
        data: dates,
        axisLabel: { color: "#506078", interval: Math.ceil(dates.length / 6) },
        axisLine: { lineStyle: { color: "rgba(80, 96, 120, 0.35)" } },
      },
      yAxis3D: {
        type: "category",
        name: "病灶",
        data: LESION_ORDER.map((lesion) => LESION_LABELS[lesion]),
        axisLabel: { color: "#506078" },
        axisLine: { lineStyle: { color: "rgba(80, 96, 120, 0.35)" } },
      },
      zAxis3D: {
        type: "value",
        name: "面积%",
        axisLabel: { color: "#506078" },
        axisLine: { lineStyle: { color: "rgba(80, 96, 120, 0.35)" } },
        splitLine: { lineStyle: { color: "rgba(80, 96, 120, 0.12)" } },
      },
      grid3D: {
        boxWidth: 104,
        boxDepth: 66,
        boxHeight: 66,
        top: -28,
        environment: "#f8fbff",
        viewControl: {
          alpha: 24,
          beta: -42,
          distance: 158,
          rotateSensitivity: 1.2,
          zoomSensitivity: 1,
        },
        light: {
          main: { intensity: 1.25, alpha: 32, beta: 22 },
          ambient: { intensity: 0.55 },
        },
        axisPointer: { show: false },
      },
      series: LESION_ORDER.map((lesion) => ({
        type: "line3D",
        name: LESION_LABELS[lesion],
        data: data.map((point) => [compactDate(point.date), LESION_LABELS[lesion], Number(point[lesion] ?? 0)]),
        lineStyle: {
          width: 4,
          color: LESION_COLORS[lesion],
        },
        itemStyle: {
          color: LESION_COLORS[lesion],
        },
      })),
    });

    return () => {
      resizeObserver.disconnect();
      chart.dispose();
    };
  }, [data, dates, hasData]);

  return (
    <GlassCard className="chart-frame">
      <div className="chart-frame__title">
        <div>
          <h2 className="chart-frame__heading">3D 病灶面积趋势</h2>
          <span className="chart-frame__meta">近 30 天各类病灶平均面积占比变化。</span>
        </div>
      </div>
      {loading ? (
        <div className="chart-frame__empty">
          <div>
            <strong>正在加载趋势数据</strong>
            <span>请稍候</span>
          </div>
        </div>
      ) : hasData ? (
        <div ref={chartRef} className="chart-frame__surface" />
      ) : (
        <div className="chart-frame__empty">
          <div>
            <strong>暂无趋势数据</strong>
            <span>完成诊断后这里会显示 3D 趋势图</span>
          </div>
        </div>
      )}
    </GlassCard>
  );
}
