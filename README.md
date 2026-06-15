# 糖尿病视网膜病变病灶分割诊断系统

基于 Attention UNet 的糖尿病视网膜病变病灶分割课程项目。系统面向眼底图像中的 4 类病灶分割任务，支持从图像上传、模型推理、量化报告生成，到 2D/3D 结果展示、患者管理、用户管理的完整闭环。

本项目不是“只训练一个模型”或者“只做一个前端页面”，而是把医学图像分割、结果分析和交互系统整合成了一个可运行、可演示、可扩展的完整作品。

---

## 1. 项目概览

### 1.1 项目目标

系统聚焦糖尿病视网膜病变中的病灶分割任务，对眼底图像中的以下 4 类病灶进行识别与展示：

- `HE`：出血（Hemorrhage）
- `EX`：渗出（Exudate）
- `MA`：微动脉瘤（Microaneurysm）
- `SE`：棉絮斑（Soft Exudate / Cotton Wool Spot）

系统的核心输出包括：

- 四类病灶的分割结果
- 每类病灶的面积占比与数量统计
- 诊断详情页的 2D 病灶轮廓图
- 诊断详情页的 3D 病灶分布展示
- 患者记录、用户角色和统计看板

### 1.2 项目亮点

- 使用 `Attention UNet` 完成四类病灶分割
- 支持 `real / auto / placeholder` 三种推理模式
- 完整前后端闭环：登录、上传、诊断、详情、统计、管理
- 诊断详情页支持 `Three.js` 3D 病灶分布可视化
- Dashboard 支持 `ECharts 3D` 统计展示
- 提供 `scripts/seed.py` 一键初始化演示数据
- 提供 Kaggle 训练脚本和本地推理接入路径

### 1.3 项目定位

这是一个课程项目和展示型系统，重点在于：

- 证明病灶分割模型训练与推理流程真实完成
- 证明分割结果可以落到一个可交互的诊断系统中
- 证明课程作业不仅有模型结果，也有工程化闭环

> 注意：本项目用于教学、演示和课程汇报，不构成临床诊断系统。

---

## 2. 系统功能详解

### 2.1 医生端功能

医生账号登录后，可以使用以下功能：

- 查看 Dashboard 看板
- 新建、编辑、删除患者
- 上传眼底图像并发起诊断
- 查看每条诊断的量化报告、2D 轮廓结果和 3D 分布图
- 查看系统统计信息
- 管理医生/病人账号

### 2.2 病人端功能

病人账号登录后，可以：

- 查看与自己关联的患者资料
- 查看自己的诊断记录
- 查看诊断详情页中的结果图和报告

病人权限受到限制，不能访问医生端的管理功能。

### 2.3 模型推理与结果展示

诊断流程为：

1. 上传眼底图像
2. 后端校验文件格式和大小
3. 进入真实模型推理或 placeholder 占位推理
4. 生成病灶面积、数量、严重程度、病灶位置数据
5. 保存诊断记录与轮廓图
6. 前端展示量化报告、轮廓图和 3D 病灶分布

### 2.4 3D 可视化

系统在诊断详情页使用 Three.js / React Three Fiber 展示病灶三维分布，核心目的是：

- 让二维病灶位置变得更直观
- 帮助用户观察病灶在视野中的相对分布
- 让课堂展示更具解释力和可视性

### 2.5 placeholder 模式

`placeholder` 不是临时 hack，而是架构中的正式能力。它可以在没有真实模型权重时稳定返回演示用诊断结果，从而保证：

- 前端开发可独立推进
- 演示数据链路完整
- 系统在无权重环境下依旧可展示

---

## 3. 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design |
| 3D 前端 | Three.js + React Three Fiber + Drei |
| 图表 | ECharts + echarts-gl |
| 后端 | Flask + Flask-SQLAlchemy + Flask-Migrate + Flask-Cors |
| 数据库 | SQLite |
| 模型推理 | PyTorch（本地 CPU 推理） |
| 图像处理 | Pillow + OpenCV |
| 训练平台 | Kaggle Notebook |
| 测试 | pytest |

---

## 4. 项目结构

项目主要目录如下：

```text
期末二/
├─ backend/                      # Flask 后端
│  ├─ api/                       # 路由层
│  ├─ database/                  # 数据模型
│  ├─ ml/                        # 模型定义与真实推理
│  ├─ services/                  # 业务逻辑层
│  ├─ tests/                     # 后端测试
│  ├─ trained_models/            # 训练得到的模型权重
│  ├─ uploads/                   # 上传图像与轮廓图
│  ├─ app.py                     # Flask 启动入口
│  ├─ config.py                  # 后端配置
│  └─ requirements.txt           # 后端依赖
├─ frontend/                     # React 前端
│  ├─ src/
│  │  ├─ components/             # 通用组件与 3D 组件
│  │  ├─ layouts/                # 布局
│  │  ├─ pages/                  # 页面级组件
│  │  ├─ api/                    # 前端 API 请求层
│  │  ├─ hooks/                  # React Query hooks
│  │  ├─ types/                  # TypeScript 类型
│  │  └─ App.tsx                 # 前端路由入口
│  ├─ package.json               # 前端依赖与脚本
│  └─ vite.config.ts             # 开发服务器配置
├─ scripts/                      # Kaggle 训练脚本与演示脚本
├─ docs/                         # 设计文档、技术方案、展示素材
├─ data/                         # 本地数据或数据集副本
├─ AGENTS.md                     # 项目级 Agent 约束
└─ README.md                     # 当前文档
```

### 4.1 backend 目录说明

- `api/`：只负责解析请求、调用 service、返回 JSON
- `services/`：业务逻辑层，处理认证、患者、诊断、统计、推理调度
- `ml/`：真实模型定义、权重加载、推理与后处理
- `database/`：SQLAlchemy 数据模型

### 4.2 frontend 目录说明

- `pages/`：页面入口，如登录、Dashboard、诊断页、详情页、患者页、用户页
- `components/three/`：3D 视图组件
- `api/`：封装后端接口请求
- `hooks/`：前端数据获取与状态管理

### 4.3 scripts 目录说明

- `kaggle_train.py`：Kaggle patch / hybrid 训练脚本
- `kaggle_train_full_image.py`：Kaggle 全图训练版本
- `postprocess_masks.py`：分割结果后处理脚本
- `seed.py`：演示数据初始化脚本

---

## 5. 快速开始

### 5.1 环境准备

建议使用独立 Python 环境，不要直接使用全局 Python。

可选方案：

- 你已有自己的 conda / venv 环境
- 新建一个专用环境后再安装依赖

示例（conda）：

```powershell
conda create -n dr-seg python=3.11 -y
conda activate dr-seg
```

前端需要 Node.js 环境，建议使用 Node 18 或更高版本。

### 5.2 启动后端

进入后端目录并安装依赖：

```powershell
cd backend
pip install -r requirements.txt
python app.py
```

后端默认运行在：

- `http://127.0.0.1:5000`

健康检查接口：

- `GET /api/health`

示例访问：

- [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health)

### 5.3 启动前端

进入前端目录并启动开发服务器：

```powershell
cd frontend
npm install
npm run dev
```

前端默认运行在：

- `http://127.0.0.1:5173`

Vite 配置中已将 `/api` 代理到后端：

- `/api -> http://127.0.0.1:5000`

### 5.4 初始化演示数据

如果你希望系统启动后就有患者、用户、诊断记录和示例图像，运行：

```powershell
python scripts/seed.py --reset
```

这个脚本会：

- 创建演示医生账号和病人账号
- 创建 3 个患者
- 生成演示用原始图和轮廓图
- 插入诊断记录
- 生成 3D 展示所需的病灶位置数据

### 5.5 演示账号

如果数据库首次初始化，系统会自动创建默认管理员：

- `admin / admin123`

运行 `scripts/seed.py` 后，会再生成以下演示账号：

- 医生：`doctor_demo / doctor123`
- 病人：`patient_li / patient123`
- 病人：`patient_wang / patient123`
- 病人：`patient_zhang / patient123`

---

## 6. 页面与路由

前端主要页面如下：

| 路由 | 页面 | 说明 |
|------|------|------|
| `/login` | Login | 登录页 |
| `/` | Dashboard | 医生看板页 |
| `/diagnose` | Diagnose | 上传图像并诊断 |
| `/diagnose/:id` | DiagnosisDetail | 诊断详情页 |
| `/patients` | Patients | 患者管理页 |
| `/patients/:id` | PatientDetail | 患者详情页 |
| `/users` | Users | 用户管理页 |
| `/my-records` | PatientDetail | 病人查看自己的记录 |

权限规则：

- 医生可访问 Dashboard、Diagnose、Patients、Users 等管理页面
- 病人只能访问与自己关联的数据
- 诊断详情页根据登录身份控制访问范围

---

## 7. 后端核心接口总览

后端统一使用 `/api` 作为前缀。

### 7.1 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/login` | 用户登录 |
| `POST` | `/api/auth/logout` | 用户登出 |
| `GET` | `/api/auth/me` | 获取当前登录用户 |

### 7.2 系统与诊断接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 系统健康检查与模型状态 |
| `POST` | `/api/diagnose` | 上传眼底图并发起诊断 |
| `GET` | `/api/diagnoses` | 获取诊断记录列表 |
| `GET` | `/api/diagnoses/:id` | 获取诊断详情 |

### 7.3 患者与用户接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/patients` | 获取患者列表 |
| `POST` | `/api/patients` | 创建患者 |
| `PUT` | `/api/patients/:id` | 更新患者 |
| `DELETE` | `/api/patients/:id` | 删除患者 |
| `GET` | `/api/users` | 获取用户列表 |
| `POST` | `/api/users` | 创建用户 |
| `PUT` | `/api/users/:id` | 更新用户 |
| `DELETE` | `/api/users/:id` | 删除用户 |

### 7.4 统计与图片接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/stats/overview` | Dashboard 总览统计 |
| `GET` | `/api/stats/lesions` | 病灶频率统计 |
| `GET` | `/api/stats/trend` | 趋势统计 |
| `GET` | `/api/images/<path>` | 获取原图或轮廓图 |

---

## 8. 数据模型说明

系统主要使用 3 张核心表：

### 8.1 Patient

用于保存患者信息：

- `name`
- `gender`
- `age`
- `patient_id`
- `is_deleted`

### 8.2 User

用于保存登录账号：

- `username`
- `display_name`
- `password_hash`
- `role`（`doctor` 或 `patient`）
- `linked_patient_id`
- `is_active`

### 8.3 Diagnosis

用于保存诊断记录：

- `image_path`
- `contour_path`
- `lesion_areas`
- `lesion_counts`
- `lesion_positions`
- `severity`
- `notes`

其中：

- `lesion_areas`：四类病灶面积占比
- `lesion_counts`：四类病灶数量
- `lesion_positions`：3D 展示所用的病灶位置与包围盒信息

---

## 9. 推理模式说明

后端通过 `MODEL_BACKEND` 控制推理模式，可在 `backend/.env` 中配置。

支持以下 3 种模式：

| 模式 | 含义 |
|------|------|
| `real` | 强制使用真实模型权重推理 |
| `placeholder` | 强制使用占位结果推理 |
| `auto` | 优先使用真实模型，失败时自动回退到 placeholder |

### 9.1 默认模型路径

默认权重路径为：

- `backend/trained_models/attention_unet_dr.pth`

### 9.2 推荐配置示例

在 `backend/.env` 中可写入：

```env
DEBUG=true
MODEL_BACKEND=auto
MODEL_PATH=trained_models/attention_unet_dr.pth
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
```

### 9.3 placeholder 模式的作用

当没有真实权重文件、模型尚未训练完成、或前端只需联调时，`placeholder` 模式可以稳定返回一套演示结果，包括：

- 伪造的轮廓图
- 默认病灶面积与数量
- 病灶位置数据
- 默认严重程度

---

## 10. 模型与训练说明

### 10.1 模型说明

项目核心模型为 `Attention UNet`，用于四类病灶的语义分割。

输入与输出特点：

- 输入尺寸：`512 x 512`
- 输出通道：`4`
- 每个输出通道对应一类病灶

### 10.2 训练平台

模型训练不在本地完成，主要在 `Kaggle Notebook` 上进行。

### 10.3 训练脚本

#### `scripts/kaggle_train.py`

主训练脚本，偏 patch / hybrid 训练策略，适合解决小病灶分割与类别不平衡问题。

特点包括：

- Albumentations 数据增强
- patch / lesion crop 采样
- 多类别分割
- 训练历史和验证样本导出
- 后处理联动验证

#### `scripts/kaggle_train_full_image.py`

全图训练版本，作为对照或备选方案使用。

### 10.4 后处理脚本

#### `scripts/postprocess_masks.py`

用于对模型预测掩码做后处理，主要包含：

- 构建眼底 ROI
- 连通域过滤
- 小噪声去除
- 边缘噪声过滤

这个脚本对于稳定病灶轮廓和 3D 展示质量很重要。

### 10.5 训练产物

训练通常会导出：

- 模型权重 `.pth`
- 训练历史 `.json`
- loss 曲线
- Dice 柱状图
- 验证样本图

将最终权重放入：

- `backend/trained_models/attention_unet_dr.pth`

即可接入本地真实推理。

---

## 11. 演示数据与课堂展示

### 11.1 `scripts/seed.py` 的作用

这个脚本是演示数据初始化脚本，不负责训练，也不负责真实模型推理。它的作用是：

- 快速生成一套课堂展示可用的数据闭环
- 自动创建账号、患者、诊断记录和示例图像
- 让系统在第一次启动后就能展示完整流程

### 11.2 推荐课堂演示顺序

如果你要进行课堂汇报或系统演示，建议按下面顺序操作：

1. 启动后端
2. 启动前端
3. 运行 `scripts/seed.py --reset`
4. 使用 `doctor_demo / doctor123` 登录
5. 展示 Dashboard
6. 进入诊断详情页
7. 展示 2D 轮廓图和 3D 病灶分布
8. 切换到 Patients / Users 页面说明系统闭环

### 11.3 展示素材目录

课堂汇报相关素材和设计文档主要位于：

- [docs/presentation-assets](docs/presentation-assets)
- [docs/superpowers/specs/2026-06-15-html-class-presentation-design.md](docs/superpowers/specs/2026-06-15-html-class-presentation-design.md)

---

## 12. 测试说明

后端测试位于：

- `backend/tests/`

当前主要测试文件包括：

- `test_auth_users.py`
- `test_patients.py`
- `test_diagnoses.py`
- `test_health.py`
- `test_inference_api.py`
- `test_ml.py`
- `test_seed_script.py`

运行方式：

```powershell
cd backend
pytest tests
```

---

## 13. 常见问题

### 13.1 为什么系统能跑，但没有真实模型效果？

因为当前可能处于 `placeholder` 模式，或者权重文件不存在。请检查：

- `backend/config.py` 中的默认配置
- `backend/.env` 中的 `MODEL_BACKEND`
- `backend/trained_models/attention_unet_dr.pth` 是否存在

### 13.2 为什么 3D 页面可以显示，但和真实病灶不完全一致？

3D 展示依赖 `lesion_positions` 数据和前端映射逻辑。如果处于 placeholder 模式，位置数据是演示数据，不代表真实分割结果。

### 13.3 为什么建议运行 seed 脚本？

因为空数据库下虽然系统可以启动，但没有用户、患者和诊断记录，不利于演示和联调。

### 13.4 本项目能直接用于临床吗？

不能。本项目是课程设计和演示系统，不是经过临床验证的医疗软件。

---

## 14. 文档导航

项目中已有的重要文档如下：

- [docs/design/2026-06-13-dr-lesion-segmentation-design.md](docs/design/2026-06-13-dr-lesion-segmentation-design.md)
  - 总体设计文档
- [docs/前端技术方案与实施计划.md](<docs/前端技术方案与实施计划.md>)
  - 前端结构与实施方案
- [docs/后端技术方案.md](<docs/后端技术方案.md>)
  - 后端结构与 API 方案
- [docs/数据库设计.md](<docs/数据库设计.md>)
  - 数据模型设计
- [docs/presentation-assets](docs/presentation-assets)
  - 课堂汇报素材

---

## 15. 当前限制与后续方向

### 15.1 当前限制

- 本地推理主要为 CPU 环境
- 训练依赖 Kaggle，不在本地训练
- 角色体系只保留医生/病人的最小闭环
- 不包含注册找回密码、移动端适配、Docker 化部署
- 真实模型效果依赖最终导入的权重质量

### 15.2 后续可扩展方向

- 提升小病灶类别分割效果
- 增强真实病例下的 3D 展示一致性
- 补充更多统计分析维度
- 增加更完整的部署与运维说明

---

## 16. 一句话总结

这是一个把 `Attention UNet 病灶分割`、`Flask + React 系统闭环`、`2D/3D 结果展示` 融合在一起的医学图像分割课程项目，既能展示模型训练成果，也能展示完整系统能力。
