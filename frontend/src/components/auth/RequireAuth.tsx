import { Spin } from "antd";
import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import GlassCard from "../ui/GlassCard";
import { useCurrentUser } from "../../hooks/queries/useAuth";
import type { UserRole } from "../../types/user";

interface RequireAuthProps {
  children: ReactNode;
  roles?: UserRole[];
}

export default function RequireAuth({ children, roles }: RequireAuthProps) {
  const location = useLocation();
  const currentUser = useCurrentUser();

  if (currentUser.isLoading) {
    return (
      <div style={{ padding: 28 }}>
        <GlassCard>
          <Spin /> 正在验证登录状态...
        </GlassCard>
      </div>
    );
  }

  if (!currentUser.data) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (roles && !roles.includes(currentUser.data.role)) {
    return <Navigate to={currentUser.data.role === "patient" ? "/my-records" : "/"} replace />;
  }

  return children;
}
