import { Button, Typography } from "antd";
import { Activity, BarChart3, FileSearch, LogOut, UserCog, Users } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { useLogout } from "../hooks/mutations/useAuthMutations";
import { useCurrentUser } from "../hooks/queries/useAuth";
import "./sidebar.css";

const doctorItems = [
  { path: "/", label: "Dashboard", icon: BarChart3 },
  { path: "/diagnose", label: "Diagnose", icon: FileSearch },
  { path: "/patients", label: "Patients", icon: Users },
  { path: "/users", label: "Users", icon: UserCog },
];

const patientItems = [{ path: "/my-records", label: "My Records", icon: FileSearch }];

export default function Sidebar() {
  const navigate = useNavigate();
  const currentUser = useCurrentUser();
  const logout = useLogout();
  const items = currentUser.data?.role === "patient" ? patientItems : doctorItems;

  async function handleLogout() {
    await logout.mutateAsync();
    navigate("/login", { replace: true });
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <Activity size={24} />
        <span>DR Seg</span>
      </div>
      <nav>
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink key={item.path} to={item.path} end={item.path === "/"} className="nav-item">
              <Icon size={19} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
      <div className="sidebar-user">
        <Typography.Text strong>{currentUser.data?.display_name}</Typography.Text>
        <Typography.Text type="secondary">{currentUser.data?.role === "doctor" ? "医生" : "病人"}</Typography.Text>
        <Button icon={<LogOut size={16} />} onClick={handleLogout} loading={logout.isPending}>
          退出
        </Button>
      </div>
    </aside>
  );
}
