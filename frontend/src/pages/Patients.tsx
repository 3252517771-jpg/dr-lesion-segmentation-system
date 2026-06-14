import { Button, Form, Input, InputNumber, Select, Table } from "antd";
import { Link } from "react-router-dom";

import GlassCard from "../components/ui/GlassCard";
import { useCreatePatient } from "../hooks/mutations/usePatientMutations";
import { usePatients } from "../hooks/queries/usePatients";

export default function Patients() {
  const patients = usePatients();
  const createPatient = useCreatePatient();

  return (
    <>
      <h1 className="page-title">Patients</h1>
      <div className="content-grid two-column">
        <GlassCard>
          <Table
            rowKey="id"
            loading={patients.isLoading}
            dataSource={patients.data?.patients ?? []}
            columns={[
              { title: "病历号", dataIndex: "patient_id" },
              { title: "姓名", dataIndex: "name" },
              { title: "性别", dataIndex: "gender" },
              { title: "年龄", dataIndex: "age" },
              { title: "诊断次数", dataIndex: "diagnosis_count" },
              { title: "操作", render: (_, record) => <Link to={`/patients/${record.id}`}>详情</Link> },
            ]}
          />
        </GlassCard>
        <GlassCard>
          <Form layout="vertical" onFinish={(values) => createPatient.mutate(values)}>
            <Form.Item label="姓名" name="name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item label="病历号" name="patient_id" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item label="性别" name="gender" rules={[{ required: true }]}>
              <Select options={[{ value: "男" }, { value: "女" }]} />
            </Form.Item>
            <Form.Item label="年龄" name="age" rules={[{ required: true }]}>
              <InputNumber min={0} max={150} style={{ width: "100%" }} />
            </Form.Item>
            <Button htmlType="submit" loading={createPatient.isPending}>新增患者</Button>
          </Form>
        </GlassCard>
      </div>
    </>
  );
}
