# 糖尿病视网膜病变病灶分割诊断系统 — 设计文档

> 项目：期末二
> 日期：2026-06-13
> 课程：医学图像分割
> 作者：小洋裙

---

## 1. 项目概述

### 1.1 目标

构建一个基于 Attention UNet 的糖尿病视网膜病变（DR）病灶分割诊断系统。系统接收眼底图像，自动分割出出血（HE）、渗出（EX）、微动脉瘤（MA）、棉絮斑（SE）四类病灶，输出量化诊断报告与可视化结果。

### 1.2 与上一版本（期末）的区别

| 维度 | 期末（分类） | 期末二（分割） |
|------|-------------|---------------|
| 任务 | DR 0-4 级分类 | 病灶分割 |
| 模型 | EfficientNet-B0 | Attention UNet |
| 推理结果 | 五类概率 + 热力图 | 病灶掩码 + 面积占比 + 数量 |
| 核心展示 | 分级结果 | 量化诊断报告 |
| 可视化 | Grad-CAM 热力图 | 病灶轮廓图 + Three.js 3D 展示 |
| 统计 | 等级分布 | 病灶频率分布 |
| 数据集 | APTOS 2019 | DDR |

### 1.3 技术栈

```
训练平台     Kaggle Notebook（Tesla P100 GPU）
推理平台     本地 CPU（Intel i5-13420H）
后端         Flask + SQLAlchemy + SQLite
前端         React + TypeScript + Ant Design + Recharts
3D 可视化    Three.js（React Three Fiber）+ ECharts + echarts-gl
深度学习     PyTorch
```

---

## 2. 数据

### 2.1 数据集：DDR

DDR（Dataset of Diabetic Retinopathy）是目前公开的 DR 数据集之一，包含 DR 分级与病灶分割标注。

- 总图像量：13,673 张（分割子集 ~750+ 张）
- 分割标注类别：
  - **HE** — Hemorrhage（出血）
  - **EX** — Exudate（渗出）
  - **MA** — Microaneurysm（微动脉瘤）
  - **SE** — Soft Exudate / Cotton Wool Spot（棉絮斑）
- 来源：Kaggle 可直接下载

### 2.2 数据预处理

- Resize 统一到 512×512
- CLAHE（对比度受限自适应直方图均衡化）增强
- 归一化到 [0, 1]
- 每个病灶类别独立处理为二值掩码 → 4 通道输出

### 2.3 数据增强

- 随机水平/垂直翻转
- 随机旋转（±15°）
- 随机弹性变形
- 随机亮度和对比度调整

---

## 3. 模型：Attention UNet

### 3.1 架构概述

Attention UNet 在标准 UNet 基础上引入注意力门控（Attention Gate），在跳跃连接处自动学习关注重要区域、抑制无关背景。

```
输入 (512×512×3)
  ↓
Encoder（4 层下采样，每层 Conv + BN + ReLU + MaxPool）
  ↓
Bridge（底部卷积层）
  ↓
Decoder（4 层上采样，每层通过 Attention Gate 融合跳跃连接）
  ↓
输出 (512×512×4) —— 每通道对应一类病灶
```

### 3.2 损失函数

- Dice Loss + Binary Cross-Entropy Loss 联合
- `Loss = DiceLoss(mask, pred) + BCEWithLogitsLoss(pred, mask)`

### 3.3 评估指标

- Dice Coefficient（每类分别计算）
- IoU（每类分别计算）
- Pixel Accuracy

### 3.4 训练配置

- 优化器：Adam（lr=1e-4）
- Batch Size：16（Kaggle P100）
- Epochs：50-100
- 学习率衰减：ReduceLROnPlateau
- 早停：10 epochs 无改善

---

## 3.5 Kaggle Notebook 详细操作说明

### 3.5.1 前提

- 注册 Kaggle 账号（kaggle.com）
- 建议绑定手机号（部分 GPU 需要手机验证才能启用）
- 每周免费 30 小时 GPU 额度

### 3.5.2 创建 Notebook

1. 登录 Kaggle，点击左侧 **Code** → **New Notebook**
2. 选择 **Notebook**（而非 Dataset Notebook）
3. Notebook 命名：`dr-attention-unet-segmentation`

### 3.5.3 添加数据集

1. 在 Notebook 编辑界面右侧，点击 **Add Data**
2. 搜索 `DDR-Segmentation`（作者 sunfish141）
3. 选中并点击 **Add**（数据集会自动挂载到 `/kaggle/input/ddr-segmentation/`）
4. 可选：同时搜索并添加 `ddrdataset`（DDR 完整数据集）

### 3.5.4 启用 GPU

1. 右侧面板 **Session options** → **Accelerator** → 选择 **GPU T4 x2** 或 **GPU P100**
2. **注意**：GPU 选项为灰色表示需要手机验证，按提示绑定手机号即可
3. 确认 **Internet** 开关为 **On**（训练时需要下载预训练权重）

### 3.5.5 Notebook Cell 编写顺序

**Cell 1：安装依赖**
```python
!pip install torch torchvision torchaudio --quiet
!pip install timm opencv-python matplotlib scikit-learn scikit-image albumentations tqdm --quiet
```

**Cell 2：导入库**
```python
import os, numpy as np, cv2, torch, torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import albumentations as A
from albumentations.pytorch import ToTensorV2
import matplotlib.pyplot as plt
from tqdm import tqdm
# ... 所有依赖
```

**Cell 3：数据集路径配置**
```python
DATA_DIR = "/kaggle/input/ddr-segmentation"
TRAIN_IMG = os.path.join(DATA_DIR, "train/image")
TRAIN_MASK = os.path.join(DATA_DIR, "train/mask")
VAL_IMG = os.path.join(DATA_DIR, "valid/image")
VAL_MASK = os.path.join(DATA_DIR, "valid/mask")
```

**Cell 4：定义 Attention UNet 模型**
- 包含 DoubleConv、Down、Up、AttentionGate、OutConv 等子模块
- 完整模型定义代码（约 150 行）

**Cell 5：数据加载器 + 数据增强**
```python
# 使用 Albumentations 做增强
train_transform = A.Compose([
    A.Resize(512, 512),
    A.RandomRotate90(),
    A.Flip(),
    A.ElasticTransform(alpha=1, sigma=50),
    A.RandomBrightnessContrast(),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2(),
])
```

**Cell 6：训练循环**
```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = AttentionUNet(n_channels=3, n_classes=4).to(device)
criterion = CombinedLoss(dice_weight=0.5, bce_weight=0.5)  # Dice + BCE
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)

for epoch in range(100):
    # train loop + val loop
    # 每 epoch 计算 Dice / IoU
    # 保存 best model
```

**Cell 7：保存模型**
```python
torch.save(model.state_dict(), "/kaggle/working/attention_unet_dr.pth")
print("模型已保存")
```

**Cell 8：可视化验证（可选）**
```python
# 选几张验证集图片，显示原图 + 分割掩码对比
```

### 3.5.6 下载训练产物

训练完成后，Kaggle Notebook 的 **Output** 标签页中会列出 `/kaggle/working/` 下的所有文件：

| 产物 | 路径 | 说明 |
|------|------|------|
| 模型权重 | `attention_unet_dr.pth` | 最终训练好的模型，下载后放入 `backend/trained_models/` |
| 训练日志 | （可选） | 每 epoch 的 loss 和 Dice 记录 |

**下载操作：**
1. 在 Notebook 右侧 **Output** 区域，勾选文件
2. 点击 **Download**（或右键文件 → Download）
3. 将 `.pth` 文件放入本地项目的 `backend/trained_models/` 目录

### 3.5.7 常见问题

| 问题 | 解决方案 |
|------|----------|
| GPU 选项灰色 | 绑定手机号（Profile → Phone Verification） |
| 运行提示 quota 不足 | 关闭闲置 notebook 释放额度，或等下周刷新 |
| 训练到一半断开 | Kaggle 单次最长 9 小时，断后重开 notebook → 勾选 Output 的模型文件 → 继续训练（加载 checkpoint） |
| 数据加载慢 | 确保使用 Kaggle 内置 Dataset（不要从外部上传） |
| Internet 打不开 | Session options 中确认 Internet 开关为 On |

---

## 4. 推理管线

```
上传眼底图
    ↓
ImageService 校验（格式 jpg/png/bmp/webp，最大 10MB）
    ↓
Resize 到 512×512 + 归一化
    ↓
Attention UNet 前向推理（CPU）
    ↓
Sigmoid → 阈值 0.5 → 二值掩码（4 通道）
    ↓
恢复到原图尺寸
    ↓
连通域分析 → 计算各病灶面积占比、检出数量
    ↓
生成病灶轮廓叠加图（保存 PNG）
    ↓
返回 JSON（报告数据 + 图片路径）
```

### 4.1 模型加载策略

沿用上版本的 `MODEL_BACKEND=auto|placeholder|real` 模式：

- **placeholder**：无条件返回预设假数据，用于前端开发调试
- **real**：强制加载真实 `.pth` 文件，失败则报错
- **auto**：优先加载真实模型，失败时自动回退到 placeholder

---

## 5. 产物输出

### 5.1 量化诊断报告（主要展示）

```
🩺 诊断报告 —— 糖尿病视网膜病变病灶分析
────────────────────────────────────
患者：XXX    检查时间：2026-06-13 21:19

各病灶检测结果：
  🔴 出血（HE）      ：检出 15 处 | 面积 3.2%
  🟡 渗出（EX）      ：检出 7 处  | 面积 1.8%
  🟢 微动脉瘤（MA）  ：检出 28 处 | 面积 0.6%
  🔵 棉絮斑（SE）    ：检出 2 处  | 面积 0.9%

综合评估：中度 NPDR（基于病灶面积与数量）
────────────────────────────────────
```

### 5.2 病灶轮廓叠加图（辅助展示）

- 在原图上画各病灶彩色轮廓线，不遮挡原图细节
- 四类病灶分别用红/黄/绿/蓝标注
- 默认折叠，用户可点击展开查看

### 5.3 Three.js 3D 病灶分布（详情页展示）

- 半透明灰色球体模拟眼球
- 病灶在球面以彩色方块标注
- 鼠标拖拽旋转、滚轮缩放
- 精简版实现，代码量控制在 200 行以内

### 5.4 ECharts 3D 统计图表（Dashboard）

- 病灶频率分布（3D 柱状图）
- 病灶面积占比趋势（3D 折线图）
- 使用 echarts-gl 插件

---

## 6. 系统架构

### 6.1 目录结构

```
期末二/
├── backend/
│   ├── api/                 # Blueprint：auth / health / users / patients / diagnoses / stats / images
│   ├── database/            # SQLAlchemy 模型
│   ├── ml/                  # Attention UNet 定义 + 推理 + 工具函数
│   │   ├── model.py         # Attention UNet 模型定义
│   │   ├── inference.py     # 推理管线
│   │   ├── utils.py         # 后处理工具
│   │   └── config.py        # 配置
│   ├── services/            # 业务逻辑
│   ├── tests/               # 测试用例
│   ├── app.py               # Flask 入口
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/             # 请求函数
│   │   ├── components/
│   │   │   └── three/       # Three.js 3D 组件
│   │   ├── hooks/           # TanStack Query hooks
│   │   ├── layouts/         # 全局布局
│   │   ├── pages/           # 页面
│   │   ├── styles/          # 毛玻璃风格 token
│   │   ├── types/           # TypeScript 类型
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── scripts/                 # Kaggle 训练脚本 + API 测试脚本
├── docs/design/             # 设计文档
└── README.md
```

### 6.2 数据流

```
[前端] Diagnose 页 → 上传图片 → [后端] API
    ↓
[后端] ImageService 校验 → InferenceService 推理
    ↓
[后端] 保存诊断结果 + 生成轮廓图 → 返回 JSON
    ↓
[前端] 渲染量化报告（主） + 轮廓图（辅）
    ↓
[前端] 详情页 → Three.js 3D 展示
    ↓
[Dashboard] ECharts 3D 统计图表
```

### 6.3 API 接口列表

| 方法 | 路由 | 说明 |
|------|------|------|
| POST | /api/auth/login | 医生/病人登录 |
| POST | /api/auth/logout | 退出登录 |
| GET | /api/auth/me | 当前登录用户 |
| GET | /api/health | 健康检查 + 模型状态 |
| GET | /api/users | 用户列表（医生） |
| POST | /api/users | 新建医生/病人账号（医生） |
| GET | /api/users/:id | 用户详情（医生） |
| PUT | /api/users/:id | 更新用户（医生） |
| DELETE | /api/users/:id | 删除用户（医生） |
| POST | /api/patients | 新建患者 |
| GET | /api/patients | 患者列表（分页/搜索） |
| GET | /api/patients/:id | 患者详情 |
| PUT | /api/patients/:id | 更新患者信息 |
| DELETE | /api/patients/:id | 删除患者（软删除） |
| POST | /api/diagnose | 上传图片 → 推理 → 保存 |
| GET | /api/diagnoses | 诊断记录列表 |
| GET | /api/diagnoses/:id | 诊断详情 |
| PUT | /api/diagnoses/:id | 更新备注 |
| GET | /api/images/:path | 返回原图/轮廓图 |
| GET | /api/stats/overview | 统计概览 |
| GET | /api/stats/lesions | 病灶频率分布 |
| GET | /api/stats/trend | 病灶面积趋势 |

### 6.4 数据库模型

**Patient**
```
id, name, gender, age, patient_id, created_at, is_deleted
```

**User**
```
id, username, display_name, password_hash, role(doctor|patient),
linked_patient_id, is_active, created_at, is_deleted
```

**Diagnosis**
```
id, patient_id (FK), image_path, contour_path,
lesion_areas (JSON), lesion_counts (JSON),
severity, notes, created_at, is_deleted
```

---

## 7. 页面与路由

| 路由 | 页面 | 核心内容 |
|------|------|----------|
| / | Dashboard | 数字统计卡片 + ECharts 3D 图表 |
| /diagnose | 诊断页 | 上传图片 → 查看报告 + 轮廓图 |
| /diagnose/:id | 诊断详情 | 量化报告 + 轮廓图 + Three.js 3D 展示 |
| /patients | 患者列表 | CRUD、搜索、分页 |
| /patients/:id | 患者详情 | 该患者所有诊断历史 |
| /users | 用户管理 | 医生/病人账号 CRUD |
| /my-records | 我的记录 | 病人查看关联患者诊断记录 |

### 7.1 全局布局

```
┌──────────────────────────────────────┐
│ 侧边栏  │  主内容区                    │
│         │                              │
│  🏠     │                              │
│  Dashboard                            │
│         │                              │
│  🔬     │                              │
│  Diagnose                             │
│         │                              │
│  👥     │                              │
│  Patients                             │
│         │                              │
└──────────────────────────────────────┘
```

- 左侧窄侧边栏，图标 + 文字导航，选中项高亮
- 右侧主内容区，毛玻璃背景

### 7.2 Dashboard 页

```
┌──────────────────────────────────────────────┐
│  👋 欢迎回来                                  │
│                                                │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│  │ 总诊断数 │ │ 今日诊断 │ │ 患者总数 │ │ 检出...  │         │
│  └──────┘ └──────┘ └──────┘ └──────┘         │
│                                                │
│  ┌────────────────────────────────────┐        │
│  │  ECharts 3D 柱状图（病灶频率分布）  │        │
│  └────────────────────────────────────┘        │
│                                                │
│  ┌─────────────────────┐ ┌──────────────────┐ │
│  │  3D 饼图（病灶占比）  │ │  3D 趋势折线图    │ │
│  └─────────────────────┘ └──────────────────┘ │
│                                                │
│  ┌────────────────────────────────────┐        │
│  │  最近诊断列表（5条）                │        │
│  └────────────────────────────────────┘        │
└──────────────────────────────────────────────┘
```

### 7.3 诊断页（上传页面）

```
┌──────────────────────────────────────────────┐
│  🔬 病灶诊断                                    │
│                                                │
│  ┌───────────────────────┐   ┌──────────────┐ │
│  │   图片上传区域          │   │  患者信息      │ │
│  │   （拖拽或点击）        │   │  姓名: [___]  │ │
│  │                       │   │  病历号: [__]  │ │
│  │   ┌─────────────┐     │   │              │ │
│  │   │  预览图      │     │   │  [ 开始诊断 ] │ │
│  │   └─────────────┘     │   │              │ │
│  │                       │   └──────────────┘ │
│  └───────────────────────┘                    │
│                                                │
│  诊断结果（推理完成后出现）                       │
│  ┌────────────────────────────────────────┐    │
│  │  量化报告（病灶面积、数量、综合评估）    │    │
│  │  [查看病灶图] [查看3D分布]              │    │
│  └────────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

- 左侧上传区域，右侧患者信息表单
- 点击"开始诊断"后推理，下方出现诊断结果
- 可跳转到详情页查看完整报告 + 轮廓图 + 3D

### 7.4 诊断详情页

```
┌──────────────────────────────────────────────┐
│  🔬 诊断详情  ← 返回                        │
│                                                │
│  ┌────────────────────────────────────────┐    │
│  │    量化诊断报告（主体区域）              │    │
│  │  🩺 诊断报告                            │    │
│  │  ─────────────────────                  │    │
│  │  患者：XXX    时间：...                  │    │
│  │  🔴 出血（HE）     ：15处 | 3.2%        │    │
│  │  🟡 渗出（EX）     ：7处  | 1.8%        │    │
│  │  🟢 微动脉瘤（MA） ：28处 | 0.6%        │    │
│  │  🔵 棉絮斑（SE）   ：2处  | 0.9%        │    │
│  │  综合评估：中度 NPDR                    │    │
│  └────────────────────────────────────────┘    │
│                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  病灶图   │ │ 3D 分布  │ │ 原图     │       │
│  │  (Tab 1)  │ │ (Tab 2)  │ │ (Tab 3)  │       │
│  └──────────┘ └──────────┘ └──────────┘       │
│                                                │
│  ┌────────────────────────────────────────┐    │
│  │  Tab1: 病灶轮廓叠加图                    │    │
│  │  Tab2: Three.js 3D 球体病灶分布         │    │
│  │  Tab3: 原始眼底图                       │    │
│  └────────────────────────────────────────┘    │
│                                                │
│  备注：[____________________________] [保存]   │
└──────────────────────────────────────────────┘
```

### 7.5 患者列表页

```
┌──────┬──────┬────┬────┬──────┬──────┐
│ 病历号 │ 姓名  │ 性别 │ 年龄 │ 诊断次数 │ 操作  │
├──────┼──────┼────┼────┼──────┼──────┤
│  ...  │ ...  │ .. │ .. │  ..  │ 编辑│删除 │
└──────┴──────┴────┴────┴──────┴──────┘
```

### 7.6 患者详情页

```
┌──────┬──────────┬────────┬──────────┬────┐
│ 时间  │ 诊断结果  │ 出血    │ 渗出    │ 操作 │
├──────┼──────────┼────────┼──────────┼────┤
│ 6/13 │ 中度NPDR │ 3.2%   │ 1.8%    │ 查看 │
│ 6/10 │ 轻度NPDR │ 1.1%   │ 0.5%    │ 查看 │
└──────┴──────────┴────────┴──────────┴────┘
```

### 7.7 UI 风格

沿用毛玻璃主题（iOS 通透毛玻璃 + soft shadow + rounded token 体系）。

---

## 8. 质量要求

### 8.1 分割模型验收标准

- 至少 3 类病灶 Dice > 0.5
- 推理单张 < 5 秒（CPU, 512×512 输入）
- placeholder 模式在无模型时可正常演示

### 8.2 后端验收标准

- 全部接口通过 pytest 测试
- 非法上传（格式/大小）正确拦截
- 支持 MODEL_BACKEND 三种模式切换

### 8.3 前端验收标准

- 完整走通：上传 → 推理 → 报告展示 → 3D 展示
- Three.js 3D 场景可正常渲染旋转

---

## 9. 当前限制与说明

- 分割模型的综合评估（severity）基于病灶面积占比的经验阈值，非临床诊断标准
- 训练需在 Kaggle 上完成，本地不做训练
- DDR 数据集请通过 Kaggle 下载，不提交到代码仓库
- Three.js 3D 为精简版实现，不做真实眼球解剖建模
- ECharts 3D 图表仅在支持 WebGL 的浏览器中可用
