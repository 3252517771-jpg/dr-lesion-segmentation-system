import { Button, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Table, message } from "antd";
import { Edit3, Plus, Search, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import GlassCard from "../components/ui/GlassCard";
import { useCreatePatient, useDeletePatient, useUpdatePatient } from "../hooks/mutations/usePatientMutations";
import { usePatients } from "../hooks/queries/usePatients";
import type { Patient, PatientCreate } from "../types/patient";

const genderOptions = [
  { value: "male", label: "男" },
  { value: "female", label: "女" },
];

export default function Patients() {
  const [form] = Form.useForm<PatientCreate>();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null);
  const patients = usePatients({ page, size: 10, search });
  const createPatient = useCreatePatient();
  const updatePatient = useUpdatePatient();
  const deletePatient = useDeletePatient();
  const modalTitle = editingPatient ? "编辑患者" : "新增患者";

  function openCreateModal() {
    setEditingPatient(null);
    form.resetFields();
    form.setFieldsValue({ gender: "female" });
    setModalOpen(true);
  }

  function openEditModal(patient: Patient) {
    setEditingPatient(patient);
    form.setFieldsValue({
      name: patient.name,
      patient_id: patient.patient_id,
      gender: patient.gender,
      age: patient.age,
    });
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setEditingPatient(null);
    form.resetFields();
  }

  async function handleSubmit(values: PatientCreate) {
    if (editingPatient) {
      await updatePatient.mutateAsync({ id: editingPatient.id, data: values });
      message.success("患者信息已更新");
    } else {
      await createPatient.mutateAsync(values);
      message.success("患者已创建");
    }
    closeModal();
  }

  const columns = useMemo(
    () => [
      { title: "病历号", dataIndex: "patient_id" },
      { title: "姓名", dataIndex: "name" },
      { title: "性别", dataIndex: "gender", render: (value: string) => (value === "male" ? "男" : value === "female" ? "女" : value) },
      { title: "年龄", dataIndex: "age" },
      { title: "诊断次数", dataIndex: "diagnosis_count" },
      {
        title: "操作",
        render: (_: unknown, record: Patient) => (
          <Space>
            <Link to={`/patients/${record.id}`}>详情</Link>
            <Button size="small" icon={<Edit3 size={14} />} onClick={() => openEditModal(record)}>
              编辑
            </Button>
            <Popconfirm
              title="删除患者"
              description="删除后该患者的诊断记录也会隐藏，确认继续？"
              onConfirm={async () => {
                await deletePatient.mutateAsync(record.id);
                message.success("患者已删除");
              }}
            >
              <Button size="small" danger icon={<Trash2 size={14} />}>
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [deletePatient],
  );

  return (
    <>
      <div className="page-heading-row">
        <div>
          <h1 className="page-title">Patients</h1>
          <p className="page-subtitle">维护患者档案，所有修改实时同步到后台数据库</p>
        </div>
        <Button type="primary" icon={<Plus size={16} />} onClick={openCreateModal}>
          新增患者
        </Button>
      </div>
      <GlassCard>
        <Space style={{ marginBottom: 16 }}>
          <Input.Search
            allowClear
            placeholder="搜索姓名或病历号"
            enterButton={<Search size={16} />}
            onSearch={(value) => {
              setPage(1);
              setSearch(value);
            }}
            style={{ width: 320 }}
          />
        </Space>
        <Table
          rowKey="id"
          loading={patients.isLoading}
          dataSource={patients.data?.patients ?? []}
          columns={columns}
          pagination={{
            current: patients.data?.page ?? page,
            pageSize: patients.data?.size ?? 10,
            total: patients.data?.total ?? 0,
            onChange: setPage,
          }}
        />
      </GlassCard>
      <Modal
        title={modalTitle}
        open={modalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createPatient.isPending || updatePatient.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item label="姓名" name="name" rules={[{ required: true, message: "请输入姓名" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="病历号" name="patient_id" rules={[{ required: true, message: "请输入病历号" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="性别" name="gender" rules={[{ required: true, message: "请选择性别" }]}>
            <Select options={genderOptions} />
          </Form.Item>
          <Form.Item label="年龄" name="age" rules={[{ required: true, message: "请输入年龄" }]}>
            <InputNumber min={0} max={150} style={{ width: "100%" }} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
