import type { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
}

export default function GlassCard({ children, className }: GlassCardProps) {
  return (
    <section
      className={className}
      style={{
        padding: 20,
        border: "1px solid var(--glass-border)",
        borderRadius: 8,
        background: "var(--glass-bg)",
        boxShadow: "var(--glass-shadow)",
        backdropFilter: "var(--glass-blur)",
      }}
    >
      {children}
    </section>
  );
}
