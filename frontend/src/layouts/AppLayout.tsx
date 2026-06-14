import { Layout } from "antd";
import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";

const { Content } = Layout;

export default function AppLayout() {
  return (
    <Layout style={{ minHeight: "100vh", background: "transparent" }}>
      <Sidebar />
      <Layout style={{ background: "transparent" }}>
        <Content style={{ padding: 28, overflow: "auto" }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
