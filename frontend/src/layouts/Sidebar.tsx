import { Activity, BarChart3, FileSearch, Users } from "lucide-react";
import { NavLink } from "react-router-dom";

import "./sidebar.css";

const items = [
  { path: "/", label: "Dashboard", icon: BarChart3 },
  { path: "/diagnose", label: "Diagnose", icon: FileSearch },
  { path: "/patients", label: "Patients", icon: Users },
];

export default function Sidebar() {
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
    </aside>
  );
}
