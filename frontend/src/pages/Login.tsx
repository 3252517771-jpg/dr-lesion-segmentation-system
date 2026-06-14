import { Alert, Button, Form, Input, Typography, message } from "antd";
import { Activity, LockKeyhole, UserRound } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import GlassCard from "../components/ui/GlassCard";
import { useLogin } from "../hooks/mutations/useAuthMutations";
import "./login.css";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useLogin();
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? "/";

  async function handleLogin(values: { username: string; password: string }) {
    try {
      const user = await login.mutateAsync(values);
      message.success(`欢迎，${user.display_name}`);
      navigate(user.role === "patient" ? "/my-records" : from, { replace: true });
    } catch {
      message.error("用户名或密码错误");
    }
  }

  return (
    <main className="login-page">
      <GlassCard className="login-card">
        <div className="login-brand">
          <Activity size={30} />
          <div>
            <Typography.Title level={2}>DR Lesion Segmentation</Typography.Title>
            <Typography.Text type="secondary">糖尿病视网膜病变病灶分割诊断系统</Typography.Text>
          </div>
        </div>
        <Alert
          type="info"
          showIcon
          message="默认医生账号：admin / admin123"
          description="医生可管理患者、用户和诊断；病人账号只能查看关联患者的诊断记录。"
          style={{ marginBottom: 18 }}
        />
        <Form layout="vertical" onFinish={handleLogin} initialValues={{ username: "admin", password: "admin123" }}>
          <Form.Item label="用户名" name="username" rules={[{ required: true, message: "请输入用户名" }]}>
            <Input prefix={<UserRound size={16} />} autoComplete="username" />
          </Form.Item>
          <Form.Item label="密码" name="password" rules={[{ required: true, message: "请输入密码" }]}>
            <Input.Password prefix={<LockKeyhole size={16} />} autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" size="large" block loading={login.isPending}>
            登录
          </Button>
        </Form>
      </GlassCard>
    </main>
  );
}
