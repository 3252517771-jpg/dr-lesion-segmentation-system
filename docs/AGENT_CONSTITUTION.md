# 糖尿病视网膜病变病灶分割系统 · Agent 宪法（员工手册）

> 生效日期：2026-06-13
> 适用范围：任何AI代理首次进入 `期末二` 项目时
> 本文件仅 500 余字，阅读耗时＜2 分钟，但每条都是红线。

---

## 一、项目身份卡

| 属性 | 值 |
|------|------|
| 项目名 | 糖尿病视网膜病变病灶分割诊断系统（DR Lesion Segmentation） |
| 课程 | 医学图像分割 |
| 技术栈后端 | Flask + SQLAlchemy + SQLite + PyTorch（CPU 推理） |
| 技术栈前端 | React 18 + TS + Vite + Ant Design + Three.js（R3F）+ ECharts（echarts-gl） |
| 训练平台 | Kaggle Notebook（P100 GPU） |
| 推理平台 | 本地 CPU（Intel i5-13420H） |
| 核心文档 | 见第五条引用 |

---

## 二、执行铁律（按优先级排列）

### 原则1：架构 > 设计 > 样式

改代码前必须先确认：
1. 这个改动是否符合三层分层（`api/` → `services/` → `ml/`）
2. 是否违反模块依赖规则（API 层不能直接调 ML 层，必须通过 services）
3. 前端是否保持毛玻璃风格一致
4. 再谈样式细节

违反任意一条 → 退回重写。

### 原则2：Placeholder 是一等公民

- 无真实模型时，placeholder 模式必须稳定返回假诊断数据
- 演示数据脚本依赖 placeholder 模式生成闭环结果
- 前端必须能感知当前推理模式并显示提示
- **不是临时 hack，是项目架构的一部分**

### 原则3：一文件一职责

- 一个 `.tsx` 文件只导出一个组件
- 一个 `.py` 文件只负责一个功能点（不把 model 定义 + 推理 + 后处理塞一起）
- 超过 300 行的组件必须拆解

### 原则4：保持后端分层边界

```
API（只解析请求/返回 JSON）
    → Services（业务逻辑、推理调度）
        → ML（模型定义、推理、后处理）

禁止：
- API 直接调用 ML 层
- Services 返回 Response 对象
- ML 层反向导入 API/Service
```

---

## 三、项目边界（红线清单）

### ✅ 这个项目要做

- 1 个 Attention UNet 病灶分割模型（4 类：HE/EX/MA/SE）
- 1 个 Flask 后端（上传/诊断/患者/统计/图片服务）
- 1 个 React 前端（Dashboard / Diagnose / DiagnosisDetail / Patients / PatientDetail）
- Three.js 精简球体病灶分布（仅详情页）
- ECharts 3D 统计图表（Dashboard）
- 诊断结果以量化报告为主、病灶轮廓图为辅
- 完整的 placeholder 推理回退机制
- Kaggle 训练脚本（可独立运行）

### ❌ 这个项目明确不做

- 用户登录/注册/权限体系（单机演示，不做认证）
- 分类任务（不做 DR 0-4 分级预测，只做分割）
- 模型训练在本机运行（只在 Kaggle 上训）
- 分布式/远程推理服务
- 移动端适配
- 实时视频流诊断
- Docker 容器化部署

**任何AI建议做上述"不做"清单中的内容 → 直接否决，不予讨论。**

---

## 四、代码规范

### 命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件名 | PascalCase | `DiagnosisReport.tsx` |
| 普通函数/变量 | camelCase | `getLesionStats` |
| 常量/枚举 | UPPER_SNAKE | `LESION_COLORS` |
| 后端路由 | snake_case | `/api/diagnoses` |
| 数据库表/字段 | snake_case | `lesion_areas`, `contour_path` |
| 文件/文件夹（后端） | snake_case | `inference_service.py` |
| 文件/文件夹（前端） | kebab-case | `diagnosis-report.tsx` |
| Python 类 | PascalCase | `AttentionUNet`, `InferenceService` |
| 接口类型 | PascalCase + 无I前缀 | `DiagnosisResult`, `PatientInfo` |

### 受保护文件（修改必须确认）

| 文件 | 原因 |
|------|------|
| `backend/ml/model.py` | Attention UNet 模型定义，改错影响整个推理 |
| `backend/ml/inference.py` | 推理管线，所有诊断依赖 |
| `backend/services/inference_service.py` | 推理调度 + MODEL_BACKEND 切换逻辑 |
| `frontend/src/pages/DiagnosisDetail.tsx` | 量化报告 + 3D 展示核心页面 |
| `frontend/src/components/three/LesionSphere.tsx` | Three.js 球体病灶展示组件 |
| `backend/database/models.py` | 数据模型，改错影响全系统 |

### 危险操作（必须提问确认）

1. **注入新前端框架/库**（超出 React + Ant Design + R3F + ECharts 的技术栈）
2. **修改目录结构**（`api/` / `services/` / `ml/` 三层划分是定死的）
3. **改动推理模式切换逻辑**（auto/placeholder/real 三种模式的回退顺序）
4. **删除或重命名生成的文件路径**（上传目录/轮廓图目录的命名规范）
5. **修改 DDR 数据集的标注类别名称或颜色映射**（前端后端一致）

---

## 五、交付验证标准

### 完成后自问 3 个问题

1. **能跑吗？** → `npm run dev` 无报错 / `python app.py` 能正常启动
2. **符合规范吗？** → 目录放对了吗？命名规范了吗？引用正确的类型了吗？
3. **引用文档了吗？** → 是否参照设计文档中的定义？不要凭记忆写代码。

### 提交前 3 不提交

- ❌ 有 `console.log` / `print` 调试代码 → 删干净再提交
- ❌ 有 `any` 类型（前端）或未定义变量 → 必须定义类型
- ❌ 有未处理的边界情况（空数据/加载中/错误）→ 必须处理

---

## 六、核心引用文档

| 文档 | 作用 | 必须阅读时机 |
|------|------|------------|
| `docs/design/2026-06-13-dr-lesion-segmentation-design.md` | 功能定义、架构决策、UI 布局 | 每次进入项目 |
| `docs/前端技术方案与实施计划.md` | 目录结构、组件边界、接口协议、Sprint 计划 | 改前端代码前 |
| `docs/后端技术方案.md` | API 清单、ML 推理管线、目录结构 | 改后端代码前 |
| `docs/数据库设计.md` | 表结构、字段定义、TypeScript 类型 | 建模型/类型前 |

---

## 七、阶段里程碑提交规则

### 7.1 规则（不可跳过）

每个明确的完成节点，必须走完以下流程才能进入下一个阶段：

```
阶段性任务完成
        ↓
[代理人] 自检：npm run dev 无报错 + python app.py 启动正常
        ↓
[代理人] 准备提交清单（改了哪些文件 + 完成了什么 + 还有哪些已知问题）
        ↓
[人] 确认：人工验收，认为可以提交
        ↓
[代理人] 记录存档：更新 memory/YYYY-MM-DD.md 记录本次阶段完成的内容
        ↓
[代理人] 提交 git：git add → git commit -m "清晰描述性信息" → git push
        ↓
进入下一阶段
```

### 7.2 里程碑节点

| # | 里程碑节点 | 预计产出 |
|---|----------|---------|
| M1 | 后端 Flask 脚手架 | Flask app 启动，健康检查接口可用 |
| M2 | 数据库模型 + 迁移 | Patient / Diagnosis 表创建，CRUD 接口可用 |
| M3 | ML 推理层（含 placeholder） | Attention UNet 定义 + 推理管线 + placeholder 模式可用 |
| M4 | 前端项目骨架 | Vite + React + Ant Design 初始化，路由搭建 |
| M5 | 前端核心页面 | Dashboard / Diagnose / DiagnosisDetail / Patients 可展示 |
| M6 | 前后端联调 | 上传 → 推理 → 报告展示 全链路跑通 |
| M7 | Three.js 3D 组件 | 诊断详情页 3D 球体病灶展示可交互 |
| M8 | ECharts 3D Dashboard | 统计看板 3D 图表渲染正常 |
| M9 | Kaggle 训练脚本 | Notebook 完整可运行，模型正确导出 |
| M10 | 演示数据 + 测试 | seed 脚本可生成演示数据，pytest 通过 |

---

**宪法到此结束。如果你看不懂以上任何一条 → 先读文档，再动手。**
