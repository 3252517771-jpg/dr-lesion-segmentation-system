import { Typography } from "antd";
import type { ReactNode } from "react";

import GlassCard from "./GlassCard";

interface StatCardProps {
  title: string;
  value: ReactNode;
}

export default function StatCard({ title, value }: StatCardProps) {
  return (
    <GlassCard>
      <Typography.Text type="secondary">{title}</Typography.Text>
      <div style={{ marginTop: 8, fontSize: 30, fontWeight: 800 }}>{value}</div>
    </GlassCard>
  );
}
