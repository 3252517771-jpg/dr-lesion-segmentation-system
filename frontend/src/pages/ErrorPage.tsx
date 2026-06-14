import { Button, Result } from "antd";
import { Link } from "react-router-dom";

export default function ErrorPage() {
  return (
    <Result
      status="404"
      title="页面不存在"
      subTitle="请返回系统首页继续操作"
      extra={<Button type="primary"><Link to="/">返回首页</Link></Button>}
    />
  );
}
