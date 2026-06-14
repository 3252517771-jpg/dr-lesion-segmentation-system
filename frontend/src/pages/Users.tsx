import { Button, Form, Input, Modal, Popconfirm, Select, Space, Switch, Table, Tag, message } from "antd";
import { Edit3, Plus, Search, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import GlassCard from "../components/ui/GlassCard";
import { useCreateUser, useDeleteUser, useUpdateUser } from "../hooks/mutations/useUserMutations";
import { usePatients } from "../hooks/queries/usePatients";
import { useUsers } from "../hooks/queries/useUsers";
import type { User, UserCreate, UserRole } from "../types/user";

const roleOptions = [
  { value: "doctor", label: "医生" },
  { value: "patient", label: "病人" },
];

export default function Users() {
  const [form] = Form.useForm<UserCreate>();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedRole, setSelectedRole] = useState<UserRole>("doctor");
  const users = useUsers({ page, size: 10, search });
  const patients = usePatients({ size: 100 });
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const patientOptions = useMemo(
    () => patients.data?.patients.map((patient) => ({ value: patient.id, label: `${patient.name} (${patient.patient_id})` })) ?? [],
    [patients.data],
  );

  function openCreateModal() {
    setEditingUser(null);
    setSelectedRole("doctor");
    form.resetFields();
    form.setFieldsValue({ role: "doctor", is_active: true });
    setModalOpen(true);
  }

  function openEditModal(user: User) {
    setEditingUser(user);
    setSelectedRole(user.role);
    form.setFieldsValue({
      username: user.username,
      display_name: user.display_name,
      role: user.role,
      linked_patient_id: user.linked_patient_id,
      is_active: user.is_active,
      password: "",
    });
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setEditingUser(null);
    form.resetFields();
  }

  async function handleSubmit(values: UserCreate) {
    const payload = {
      ...values,
      linked_patient_id: values.role === "patient" ? values.linked_patient_id : null,
    };
    if (editingUser) {
      const { password, ...rest } = payload;
      await updateUser.mutateAsync({
        id: editingUser.id,
        data: password ? payload : rest,
      });
      message.success("用户信息已更新");
    } else {
      await createUser.mutateAsync(payload);
      message.success("用户已创建");
    }
    closeModal();
  }

  const columns = useMemo(
    () => [
      { title: "用户名", dataIndex: "username" },
      { title: "显示名称", dataIndex: "display_name" },
      {
        title: "角色",
        dataIndex: "role",
        render: (value: UserRole) => <Tag color={value === "doctor" ? "blue" : "green"}>{value === "doctor" ? "医生" : "病人"}</Tag>,
      },
      { title: "关联患者", dataIndex: "linked_patient_name", render: (value: string | null) => value || "-" },
      { title: "状态", dataIndex: "is_active", render: (value: boolean) => <Tag color={value ? "success" : "default"}>{value ? "启用" : "停用"}</Tag> },
      {
        title: "操作",
        render: (_: unknown, record: User) => (
          <Space>
            <Button size="small" icon={<Edit3 size={14} />} onClick={() => openEditModal(record)}>
              编辑
            </Button>
            <Popconfirm
              title="删除用户"
              description="确认删除该登录账号？"
              onConfirm={async () => {
                await deleteUser.mutateAsync(record.id);
                message.success("用户已删除");
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
    [deleteUser],
  );

  return (
    <>
      <div className="page-heading-row">
        <div>
          <h1 className="page-title">Users</h1>
          <p className="page-subtitle">管理医生和病人登录账号，病人账号需关联患者档案</p>
        </div>
        <Button type="primary" icon={<Plus size={16} />} onClick={openCreateModal}>
          新增用户
        </Button>
      </div>
      <GlassCard>
        <Space style={{ marginBottom: 16 }}>
          <Input.Search
            allowClear
            placeholder="搜索用户名或显示名称"
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
          loading={users.isLoading}
          dataSource={users.data?.users ?? []}
          columns={columns}
          pagination={{
            current: users.data?.page ?? page,
            pageSize: users.data?.size ?? 10,
            total: users.data?.total ?? 0,
            onChange: setPage,
          }}
        />
      </GlassCard>
      <Modal
        title={editingUser ? "编辑用户" : "新增用户"}
        open={modalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createUser.isPending || updateUser.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item label="用户名" name="username" rules={[{ required: true, message: "请输入用户名" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="显示名称" name="display_name" rules={[{ required: true, message: "请输入显示名称" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="密码" name="password" rules={editingUser ? [] : [{ required: true, message: "请输入密码" }]}>
            <Input.Password placeholder={editingUser ? "留空则不修改密码" : undefined} />
          </Form.Item>
          <Form.Item label="角色" name="role" rules={[{ required: true, message: "请选择角色" }]}>
            <Select
              options={roleOptions}
              onChange={(role: UserRole) => {
                setSelectedRole(role);
                if (role === "doctor") form.setFieldValue("linked_patient_id", null);
              }}
            />
          </Form.Item>
          {selectedRole === "patient" ? (
            <Form.Item label="关联患者" name="linked_patient_id" rules={[{ required: true, message: "请选择关联患者" }]}>
              <Select showSearch optionFilterProp="label" loading={patients.isLoading} options={patientOptions} />
            </Form.Item>
          ) : null}
          <Form.Item label="账号状态" name="is_active" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
