# Banana Slides 架构文档

## 📋 目录

1. [项目概述](#项目概述)
2. [技术栈](#技术栈)
3. [系统架构](#系统架构)
4. [前端架构](#前端架构)
5. [后端架构](#后端架构)
6. [数据模型](#数据模型)
7. [核心工作流程](#核心工作流程)
8. [服务层设计](#服务层设计)
9. [API 设计](#api-设计)
10. [异步任务处理](#异步任务处理)
11. [文件存储架构](#文件存储架构)
12. [部署架构](#部署架构)

---

## 项目概述

Banana Slides 是一个基于 **nano banana pro** 模型的 AI 原生 PPT 生成应用。它支持从想法、大纲或页面描述生成完整的 PPT 演示文稿，并提供灵活的编辑和导出功能。

### 核心特性

- **多种创作路径**：支持从想法、大纲、页面描述三种方式创建 PPT
- **智能素材解析**：自动解析 PDF/Docx/MD/Txt 等文件，提取关键信息
- **自然语言编辑**：支持口头式修改（Vibe 编辑）
- **可编辑 PPTX 导出**：支持导出为可编辑的 PPTX 文件（Beta）
- **多格式导出**：支持导出为 PPTX 和 PDF 格式

---

## 技术栈

### 前端技术栈

| 技术 | 版本/说明 | 用途 |
|------|----------|------|
| **React** | 18+ | UI 框架 |
| **TypeScript** | - | 类型安全 |
| **Vite** | 5 | 构建工具和开发服务器 |
| **Zustand** | - | 轻量级状态管理 |
| **React Router** | v6 | 路由管理 |
| **Tailwind CSS** | - | 样式框架 |
| **@dnd-kit** | - | 拖拽功能 |
| **Axios** | - | HTTP 客户端 |
| **Lucide React** | - | 图标库 |

### 后端技术栈

| 技术 | 版本/说明 | 用途 |
|------|----------|------|
| **Python** | 3.10+ | 编程语言 |
| **Flask** | 3.0+ | Web 框架 |
| **SQLite** | - | 数据库（通过 SQLAlchemy） |
| **Flask-SQLAlchemy** | 3.1.1+ | ORM |
| **Flask-Migrate** | 4.0+ | 数据库迁移（基于 Alembic） |
| **Flask-CORS** | 4.0+ | 跨域支持 |
| **uv** | - | Python 包管理器 |
| **google-genai** | 1.52.0+ | Google Gemini API 客户端 |
| **openai** | 1.0.0+ | OpenAI API 客户端 |
| **python-pptx** | 1.0.0+ | PPTX 文件处理 |
| **Pillow** | 12.0.0+ | 图像处理 |
| **markitdown** | - | 文件解析（PDF/Docx/MD 等） |
| **reportlab** | 4.1.0+ | PDF 生成 |
| **img2pdf** | 0.5.1+ | 图片转 PDF |
| **tenacity** | 9.0.0+ | 重试机制 |

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  首页    │  │ 大纲编辑 │  │ 描述编辑 │  │ 预览页面 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     前端应用 (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 状态管理     │  │  API 客户端  │  │  路由管理    │     │
│  │ (Zustand)    │  │  (Axios)     │  │ (React Router)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   后端应用 (Flask)                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              控制器层 (Controllers)                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐│   │
│  │  │ Project  │ │  Page    │ │ Material │ │ Export  ││   │
│  │  │Controller│ │Controller│ │Controller│ │Controller││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘│   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              服务层 (Services)                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐│   │
│  │  │AIService │ │Export    │ │File      │ │Task     ││   │
│  │  │          │ │Service   │ │Service   │ │Manager  ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘│   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              数据访问层 (Models)                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐│   │
│  │  │ Project  │ │  Page    │ │ Material │ │  Task   ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘│   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│                    ┌──────────────┐                          │
│                    │   SQLite     │                          │
│                    │   Database   │                          │
│                    └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    外部服务集成                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Google Gemini│  │  OpenAI API  │  │  百度 OCR    │      │
│  │    API       │  │              │  │    API      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 架构特点

1. **前后端分离**：前端使用 React SPA，后端提供 RESTful API
2. **分层架构**：后端采用 Controller-Service-Model 三层架构
3. **异步任务处理**：使用 ThreadPoolExecutor 处理长时间运行的任务
4. **可扩展的 AI 提供商**：支持多种 AI 提供商（Gemini、OpenAI、Vertex AI）
5. **文件存储**：本地文件系统存储，支持 Docker 卷挂载

---

## 前端架构

### 目录结构

```
frontend/
├── src/
│   ├── pages/              # 页面组件
│   │   ├── Home.tsx        # 首页（创建项目）
│   │   ├── OutlineEditor.tsx    # 大纲编辑页
│   │   ├── DetailEditor.tsx      # 详细描述编辑页
│   │   ├── SlidePreview.tsx      # 幻灯片预览页
│   │   ├── History.tsx           # 历史版本管理页
│   │   └── Settings.tsx          # 设置页面
│   │
│   ├── components/         # UI 组件
│   │   ├── outline/        # 大纲相关组件
│   │   │   └── OutlineCard.tsx
│   │   ├── preview/        # 预览相关组件
│   │   │   ├── SlideCard.tsx
│   │   │   └── DescriptionCard.tsx
│   │   ├── shared/         # 共享组件
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Textarea.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Loading.tsx
│   │   │   ├── Toast.tsx
│   │   │   ├── MaterialSelector.tsx
│   │   │   ├── MaterialGeneratorModal.tsx
│   │   │   ├── TemplateSelector.tsx
│   │   │   └── ReferenceFileSelector.tsx
│   │   ├── history/        # 历史版本组件
│   │   │   └── ProjectCard.tsx
│   │
│   ├── store/              # Zustand 状态管理
│   │   ├── useProjectStore.ts    # 项目状态管理
│   │   └── useExportTasksStore.ts # 导出任务状态管理
│   │
│   ├── api/                # API 接口
│   │   ├── client.ts       # Axios 客户端配置
│   │   └── endpoints.ts     # API 端点定义
│   │
│   ├── types/              # TypeScript 类型定义
│   │   └── index.ts
│   │
│   ├── utils/              # 工具函数
│   │   ├── index.ts
│   │   └── projectUtils.ts
│   │
│   ├── hooks/              # 自定义 Hooks
│   │   ├── useGeneratingState.ts
│   │   └── usePageStatus.ts
│   │
│   ├── config/             # 配置文件
│   │   └── presetStyles.ts
│   │
│   ├── App.tsx             # 根组件
│   ├── main.tsx            # 入口文件
│   └── index.css           # 全局样式
│
├── public/                 # 静态资源
├── package.json
├── vite.config.ts          # Vite 配置
├── tailwind.config.js      # Tailwind CSS 配置
└── Dockerfile              # Docker 构建文件
```

### 状态管理

使用 **Zustand** 进行状态管理，主要状态包括：

- **useProjectStore**：管理当前项目状态
  - `currentProject`: 当前项目数据
  - `isGlobalLoading`: 全局加载状态
  - `activeTaskId`: 当前活动任务 ID
  - `taskProgress`: 任务进度
  - `pageGeneratingTasks`: 页面生成任务映射
  - 项目操作方法（创建、更新、删除等）
  - 生成操作方法（生成大纲、描述、图片等）
  - 导出操作方法

- **useExportTasksStore**：管理导出任务状态
  - 导出任务列表
  - 任务状态跟踪

### 路由设计

```typescript
/                           # 首页（创建项目）
/history                    # 历史项目列表
/settings                   # 设置页面
/project/:projectId/outline  # 大纲编辑页
/project/:projectId/detail   # 描述编辑页
/project/:projectId/preview  # 预览页面
```

### 核心工作流程（前端）

1. **项目创建流程**
   ```
   用户输入 → 选择创建类型 → 上传模板（可选） → 创建项目 → 跳转到编辑页
   ```

2. **生成流程**
   ```
   触发生成 → 创建异步任务 → 轮询任务状态 → 更新 UI → 完成
   ```

3. **编辑流程**
   ```
   用户编辑 → 防抖保存 → API 调用 → 同步状态 → 更新 UI
   ```

---

## 后端架构

### 目录结构

```
backend/
├── app.py                  # Flask 应用入口
├── config.py               # 配置文件
│
├── models/                 # 数据库模型
│   ├── __init__.py
│   ├── project.py          # Project 模型
│   ├── page.py             # Page 模型（幻灯片页）
│   ├── task.py             # Task 模型（异步任务）
│   ├── material.py         # Material 模型（参考素材）
│   ├── user_template.py    # UserTemplate 模型（用户模板）
│   ├── reference_file.py   # ReferenceFile 模型（参考文件）
│   ├── page_image_version.py # PageImageVersion 模型（页面版本）
│   └── settings.py         # Settings 模型（系统设置）
│
├── controllers/            # API 控制器
│   ├── __init__.py
│   ├── project_controller.py      # 项目管理
│   ├── page_controller.py          # 页面管理
│   ├── material_controller.py      # 素材管理
│   ├── template_controller.py      # 模板管理
│   ├── user_template_controller.py  # 用户模板管理
│   ├── reference_file_controller.py # 参考文件管理
│   ├── export_controller.py        # 导出功能
│   ├── file_controller.py          # 文件上传
│   └── settings_controller.py      # 设置管理
│
├── services/               # 服务层
│   ├── __init__.py
│   ├── ai_service.py       # AI 生成服务（Gemini/OpenAI 集成）
│   ├── ai_service_manager.py # AI 服务管理器
│   ├── file_service.py     # 文件管理服务
│   ├── file_parser_service.py # 文件解析服务
│   ├── export_service.py    # PPTX/PDF 导出服务
│   ├── task_manager.py     # 异步任务管理
│   ├── inpainting_service.py # 图片修复服务
│   ├── prompts.py          # AI 提示词模板
│   │
│   ├── ai_providers/       # AI 提供商抽象层
│   │   ├── text/           # 文本生成提供商
│   │   │   ├── base.py
│   │   │   ├── genai_provider.py
│   │   │   └── openai_provider.py
│   │   ├── image/          # 图片生成提供商
│   │   │   ├── base.py
│   │   │   ├── genai_provider.py
│   │   │   ├── openai_provider.py
│   │   │   ├── gemini_inpainting_provider.py
│   │   │   ├── baidu_inpainting_provider.py
│   │   │   └── volcengine_inpainting_provider.py
│   │   └── ocr/           # OCR 提供商
│   │       ├── baidu_accurate_ocr_provider.py
│   │       └── baidu_table_ocr_provider.py
│   │
│   └── image_editability/  # 可编辑 PPTX 导出相关服务
│       ├── service.py      # 主服务
│       ├── extractors.py   # 组件提取器
│       ├── hybrid_extractor.py # 混合提取器
│       ├── coordinate_mapper.py # 坐标映射
│       ├── text_attribute_extractors.py # 文本属性提取
│       ├── inpaint_providers.py # 背景图修复提供商
│       └── helpers.py     # 辅助函数
│
├── utils/                  # 工具函数
│   ├── __init__.py
│   ├── response.py         # 统一响应格式
│   ├── validators.py       # 数据验证
│   ├── path_utils.py       # 路径处理
│   ├── page_utils.py       # 页面工具函数
│   ├── mask_utils.py        # 遮罩工具函数
│   ├── latex_utils.py       # LaTeX 工具函数
│   └── pptx_builder.py     # PPTX 构建器
│
├── migrations/             # 数据库迁移文件（Alembic）
│   └── versions/
│
├── instance/              # SQLite 数据库（自动生成）
│   └── database.db
│
├── tests/                 # 测试文件
│   ├── unit/              # 单元测试
│   └── integration/       # 集成测试
│
└── Dockerfile             # Docker 构建文件
```

### 应用初始化流程

```python
create_app()
  ├── 加载配置（Config）
  ├── 初始化数据库（SQLAlchemy）
  ├── 配置 CORS
  ├── 初始化数据库迁移（Flask-Migrate）
  ├── 注册 Blueprint（路由）
  ├── 加载设置到配置（从数据库）
  └── 返回 Flask 应用实例
```

### 控制器层设计

控制器负责处理 HTTP 请求，调用服务层，返回响应。

**设计原则**：
- 控制器只处理请求/响应转换
- 业务逻辑放在服务层
- 使用统一的响应格式

**示例**：`project_controller.py`

```python
@project_bp.route('/api/projects', methods=['POST'])
def create_project():
    # 1. 验证请求数据
    # 2. 调用服务层创建项目
    # 3. 返回统一格式响应
```

---

## 数据模型

### 核心模型关系图

```
Project (项目)
  ├── has many → Page (页面)
  ├── has many → Task (任务)
  ├── has many → Material (素材)
  ├── has many → ReferenceFile (参考文件)
  └── has one → UserTemplate (用户模板，可选)

Page (页面)
  ├── belongs to → Project
  └── has many → PageImageVersion (图片版本)

Task (任务)
  └── belongs to → Project

Material (素材)
  └── belongs to → Project (可为 null，表示全局素材)

ReferenceFile (参考文件)
  └── belongs to → Project

Settings (设置)
  └── 单例模式（全局设置）
```

### 模型详细说明

#### 1. Project（项目）

```python
id: str                    # UUID，主键
idea_prompt: str           # 想法提示词（idea 类型）
outline_text: str          # 大纲文本（outline 类型）
description_text: str      # 描述文本（descriptions 类型）
extra_requirements: str    # 额外要求
creation_type: str         # 创建类型：idea|outline|descriptions
template_image_path: str   # 模板图片路径
template_style: str        # 风格描述文本（无模板图模式）
export_extractor_method: str # 导出提取方法：mineru|hybrid
export_inpaint_method: str  # 导出背景图方法：generative|baidu|hybrid
status: str                # 状态：DRAFT|PROCESSING|COMPLETED|FAILED
created_at: datetime
updated_at: datetime
```

#### 2. Page（页面）

```python
id: str                    # UUID，主键
project_id: str            # 外键 → Project.id
order_index: int           # 页面顺序
part: str                  # 可选的分区名称
outline_content: str       # JSON 字符串，大纲内容
description_content: str    # JSON 字符串，描述内容
generated_image_path: str  # 生成的图片路径
status: str                # 状态：DRAFT|PROCESSING|COMPLETED|FAILED
created_at: datetime
updated_at: datetime
```

#### 3. Task（任务）

```python
id: str                    # UUID，主键
project_id: str            # 外键 → Project.id
task_type: str             # 任务类型：GENERATE_OUTLINE|GENERATE_DESCRIPTIONS|GENERATE_IMAGES|...
status: str                # 状态：PENDING|PROCESSING|COMPLETED|FAILED
progress: str              # JSON 字符串，进度信息
created_at: datetime
completed_at: datetime
```

#### 4. Material（素材）

```python
id: str                    # UUID，主键
project_id: str            # 外键 → Project.id（可为 null，表示全局素材）
filename: str              # 文件名
relative_path: str         # 相对路径
url: str                   # 访问 URL
created_at: datetime
```

#### 5. PageImageVersion（页面图片版本）

```python
id: str                    # UUID，主键
page_id: str               # 外键 → Page.id
image_path: str            # 图片路径
version_number: int        # 版本号
is_current: bool          # 是否为当前版本
created_at: datetime
```

#### 6. ReferenceFile（参考文件）

```python
id: str                    # UUID，主键
project_id: str            # 外键 → Project.id
filename: str              # 文件名
file_path: str             # 文件路径
file_type: str             # 文件类型：pdf|docx|md|txt|...
parsed_content: str        # JSON 字符串，解析后的内容
created_at: datetime
```

#### 7. Settings（设置）

```python
id: int                    # 主键（单例，id=1）
ai_provider_format: str    # AI 提供商格式：gemini|openai|vertex
api_base_url: str          # API 基础 URL
api_key: str               # API 密钥
output_language: str        # 输出语言：zh|en|ja|auto
image_resolution: str      # 图片分辨率：1K|2K|4K
image_aspect_ratio: str    # 图片宽高比：16:9|4:3|...
max_description_workers: int # 描述生成最大并发数
max_image_workers: int     # 图片生成最大并发数
updated_at: datetime
```

---

## 核心工作流程

### 1. 项目创建流程

```
用户输入
  │
  ├─ 类型：idea
  │   └─→ 创建项目 → 生成大纲 → 生成描述 → 生成图片
  │
  ├─ 类型：outline
  │   └─→ 创建项目 → 解析大纲 → 生成描述 → 生成图片
  │
  └─ 类型：descriptions
      └─→ 创建项目 → 解析描述 → 生成图片
```

### 2. 大纲生成流程

```
用户输入想法
  │
  ├─→ AIService.generate_outline()
  │   └─→ 调用 AI 模型生成大纲
  │
  ├─→ 解析 AI 响应
  │   └─→ 提取结构化大纲数据
  │
  └─→ 创建 Page 记录
      └─→ 保存到数据库
```

### 3. 描述生成流程

```
大纲数据
  │
  ├─→ 创建异步任务（Task）
  │
  ├─→ TaskManager.submit_task()
  │   └─→ generate_descriptions_task()
  │       ├─→ 并行处理多个页面
  │       ├─→ AIService.generate_page_description()
  │       └─→ 更新 Page.description_content
  │
  └─→ 前端轮询任务状态
      └─→ 更新 UI
```

### 4. 图片生成流程

```
页面描述
  │
  ├─→ 创建异步任务（Task）
  │
  ├─→ TaskManager.submit_task()
  │   └─→ generate_images_task()
  │       ├─→ 并行处理多个页面
  │       ├─→ AIService.generate_image()
  │       ├─→ FileService.save_generated_image()
  │       ├─→ 创建 PageImageVersion 记录
  │       └─→ 更新 Page.generated_image_path
  │
  └─→ 前端轮询任务状态
      └─→ 更新 UI
```

### 5. 图片编辑流程（Vibe 编辑）

```
用户选择区域 + 编辑提示
  │
  ├─→ 创建编辑任务
  │
  ├─→ AIService.edit_image()
  │   ├─→ 提取选中区域
  │   ├─→ 调用 AI 模型进行局部重绘
  │   └─→ 返回编辑后的图片
  │
  └─→ 保存新版本
      └─→ 更新 PageImageVersion
```

### 6. 导出流程

#### 6.1 简单导出（图片转 PPTX/PDF）

```
页面图片列表
  │
  ├─→ ExportService.create_pptx_from_images()
  │   ├─→ 创建 Presentation 对象
  │   ├─→ 为每个图片创建幻灯片
  │   └─→ 保存 PPTX 文件
  │
  └─→ 返回文件下载链接
```

#### 6.2 可编辑 PPTX 导出（Beta）

```
页面图片列表
  │
  ├─→ ImageEditabilityService.extract_components()
  │   ├─→ 使用 MinerU 或 Hybrid 方法提取组件
  │   ├─→ 提取文本、图片、表格等元素
  │   └─→ 提取样式信息（字体、颜色、大小等）
  │
  ├─→ 获取背景图
  │   ├─→ 使用生成式方法（AI 生成）
  │   ├─→ 使用百度重绘方法
  │   └─→ 或使用混合方法
  │
  ├─→ CoordinateMapper.map_coordinates()
  │   └─→ 映射元素坐标到 PPTX 坐标系统
  │
  ├─→ PPTXBuilder.build_editable_pptx()
  │   ├─→ 创建幻灯片
  │   ├─→ 添加背景图
  │   ├─→ 添加文本元素（带样式）
  │   ├─→ 添加图片元素
  │   ├─→ 添加表格元素
  │   └─→ 保存 PPTX 文件
  │
  └─→ 返回文件下载链接
```

---

## 服务层设计

### 1. AIService（AI 服务）

**职责**：封装所有 AI 模型交互

**核心方法**：
- `generate_outline()`: 生成大纲
- `generate_page_description()`: 生成页面描述
- `generate_image()`: 生成图片
- `edit_image()`: 编辑图片
- `refine_outline()`: 优化大纲
- `refine_descriptions()`: 优化描述

**设计特点**：
- 使用 Provider 模式，支持多种 AI 提供商
- 自动重试机制（使用 tenacity）
- 统一的错误处理

### 2. ExportService（导出服务）

**职责**：处理 PPTX 和 PDF 导出

**核心方法**：
- `create_pptx_from_images()`: 从图片创建 PPTX
- `create_pdf_from_images()`: 从图片创建 PDF
- `create_editable_pptx()`: 创建可编辑 PPTX（调用 ImageEditabilityService）

### 3. FileService（文件服务）

**职责**：管理文件存储和访问

**核心方法**：
- `save_generated_image()`: 保存生成的图片
- `save_material_image()`: 保存素材图片
- `save_uploaded_file()`: 保存上传的文件
- `get_file_url()`: 获取文件访问 URL
- `delete_file()`: 删除文件

**文件存储结构**：
```
uploads/
├── {project_id}/
│   ├── pages/          # 页面图片
│   ├── template/       # 模板图片
│   ├── exports/         # 导出文件
│   └── materials/       # 素材文件
├── materials/           # 全局素材
└── user-templates/     # 用户模板
```

### 4. FileParserService（文件解析服务）

**职责**：解析上传的文件（PDF、Docx、MD 等）

**核心方法**：
- `parse_file()`: 解析文件
- `extract_text()`: 提取文本
- `extract_images()`: 提取图片
- `extract_tables()`: 提取表格

**支持格式**：
- PDF（使用 markitdown）
- Docx（使用 markitdown）
- Markdown（使用 markitdown）
- TXT（直接读取）

### 5. TaskManager（任务管理器）

**职责**：管理异步任务

**设计**：
- 使用 `ThreadPoolExecutor` 处理后台任务
- 任务状态存储在数据库中（Task 模型）
- 支持任务进度跟踪

**任务类型**：
- `GENERATE_OUTLINE`: 生成大纲
- `GENERATE_DESCRIPTIONS`: 生成描述
- `GENERATE_IMAGES`: 生成图片
- `GENERATE_PAGE_IMAGE`: 生成单页图片
- `GENERATE_MATERIAL_IMAGE`: 生成素材图片
- `EXPORT_PPTX`: 导出 PPTX
- `EXPORT_PDF`: 导出 PDF
- `EXPORT_EDITABLE_PPTX`: 导出可编辑 PPTX

### 6. ImageEditabilityService（可编辑性服务）

**职责**：处理可编辑 PPTX 导出的核心逻辑

**核心方法**：
- `extract_components()`: 提取页面组件
- `get_background_image()`: 获取背景图
- `build_editable_pptx()`: 构建可编辑 PPTX

**提取方法**：
- `mineru`: 使用 MinerU 服务提取
- `hybrid`: 混合方法（MinerU + OCR + AI 分析）

**背景图获取方法**：
- `generative`: 使用 AI 生成背景图
- `baidu`: 使用百度重绘方法
- `hybrid`: 混合方法（百度重绘 + AI 增强）

---

## API 设计

### RESTful API 规范

**基础 URL**：`/api`

**响应格式**：
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

**错误响应**：
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

### 主要 API 端点

#### 项目相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects` | 创建项目 |
| GET | `/api/projects` | 获取项目列表 |
| GET | `/api/projects/:id` | 获取项目详情 |
| PUT | `/api/projects/:id` | 更新项目 |
| DELETE | `/api/projects/:id` | 删除项目 |
| POST | `/api/projects/:id/template` | 上传模板图片 |
| POST | `/api/projects/:id/generate/outline` | 生成大纲 |
| POST | `/api/projects/:id/generate/descriptions` | 生成描述 |
| POST | `/api/projects/:id/generate/images` | 生成图片 |

#### 页面相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/projects/:id/pages` | 获取页面列表 |
| GET | `/api/projects/:id/pages/:pageId` | 获取页面详情 |
| PUT | `/api/projects/:id/pages/:pageId` | 更新页面 |
| PUT | `/api/projects/:id/pages/:pageId/outline` | 更新页面大纲 |
| PUT | `/api/projects/:id/pages/:pageId/description` | 更新页面描述 |
| DELETE | `/api/projects/:id/pages/:pageId` | 删除页面 |
| POST | `/api/projects/:id/pages/:pageId/generate/image` | 生成页面图片 |
| POST | `/api/projects/:id/pages/:pageId/edit/image` | 编辑页面图片 |

#### 任务相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks/:id` | 获取任务状态 |
| GET | `/api/tasks/:id/progress` | 获取任务进度 |

#### 导出相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects/:id/export/pptx` | 导出 PPTX |
| POST | `/api/projects/:id/export/pdf` | 导出 PDF |
| POST | `/api/projects/:id/export/editable-pptx` | 导出可编辑 PPTX |

#### 素材相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects/:id/materials/generate` | 生成素材图片 |
| GET | `/api/projects/:id/materials` | 获取素材列表 |
| DELETE | `/api/projects/:id/materials/:id` | 删除素材 |

#### 文件相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/files/upload` | 上传文件 |
| GET | `/files/:projectId/:type/:filename` | 获取文件 |

#### 设置相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/settings` | 获取设置 |
| PUT | `/api/settings` | 更新设置 |

---

## 异步任务处理

### 任务处理架构

```
HTTP 请求
  │
  ├─→ Controller 创建 Task 记录
  │   └─→ status = 'PENDING'
  │
  ├─→ TaskManager.submit_task()
  │   └─→ ThreadPoolExecutor.submit()
  │       └─→ 后台任务函数
  │
  └─→ 立即返回 task_id (202 Accepted)
      │
      └─→ 前端轮询任务状态
          └─→ GET /api/tasks/:id
```

### 任务状态流转

```
PENDING → PROCESSING → COMPLETED
                    ↓
                  FAILED
```

### 任务进度跟踪

任务进度存储在 `Task.progress` 字段（JSON 字符串）：

```json
{
  "total": 10,
  "completed": 5,
  "failed": 1
}
```

### 并发控制

- **描述生成**：默认最大并发数 5（`MAX_DESCRIPTION_WORKERS`）
- **图片生成**：默认最大并发数 8（`MAX_IMAGE_WORKERS`）
- **任务管理器**：默认最大工作线程数 4

---

## 文件存储架构

### 存储结构

```
uploads/
├── {project_id}/              # 项目专用目录
│   ├── pages/                 # 页面图片
│   │   ├── page_{page_id}_v{version}.png
│   │   └── ...
│   ├── template/              # 模板图片
│   │   └── template.png
│   ├── exports/               # 导出文件
│   │   ├── {filename}.pptx
│   │   └── {filename}.pdf
│   └── materials/            # 项目素材
│       └── image_{timestamp}.png
│
├── materials/                 # 全局素材
│   └── image_{timestamp}.png
│
└── user-templates/            # 用户模板
    └── {template_id}/
        └── template.png
```

### 文件访问

文件通过 HTTP 端点访问：

```
GET /files/{project_id}/{type}/{filename}
```

**type 类型**：
- `pages`: 页面图片
- `template`: 模板图片
- `exports`: 导出文件
- `materials`: 素材文件

### 文件服务配置

- **最大文件大小**：200MB
- **允许的图片格式**：png, jpg, jpeg, gif, webp
- **允许的参考文件格式**：pdf, docx, pptx, doc, ppt, xlsx, xls, csv, txt, md

---

## 部署架构

### Docker Compose 部署

```
┌─────────────────────────────────────────┐
│         Docker Compose                  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │     Frontend Container           │  │
│  │  ┌────────────────────────────┐ │  │
│  │  │   Nginx (Port 80)          │ │  │
│  │  │   └─→ Static Files         │ │  │
│  │  └────────────────────────────┘ │  │
│  │  Port: 3000 → 80                │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │     Backend Container            │  │
│  │  ┌────────────────────────────┐ │  │
│  │  │   Flask App (Port 5000)    │ │  │
│  │  │   ├─→ SQLite Database      │ │  │
│  │  │   └─→ File Storage         │ │  │
│  │  └────────────────────────────┘ │  │
│  │  Port: 5000 → 5000              │  │
│  └──────────────────────────────────┘  │
│                                         │
│  Volumes:                               │
│  ├─ backend/instance → database.db     │
│  └─ uploads → file storage             │
└─────────────────────────────────────────┘
```

### 环境变量配置

**必需配置**：
- `AI_PROVIDER_FORMAT`: AI 提供商格式（gemini|openai|vertex）
- `GOOGLE_API_KEY` / `OPENAI_API_KEY`: API 密钥
- `GOOGLE_API_BASE` / `OPENAI_API_BASE`: API 基础 URL

**可选配置**：
- `PORT`: 后端端口（默认 5000）
- `CORS_ORIGINS`: CORS 允许的源
- `OUTPUT_LANGUAGE`: 输出语言（zh|en|ja|auto）
- `DEFAULT_RESOLUTION`: 默认分辨率（1K|2K|4K）
- `DEFAULT_ASPECT_RATIO`: 默认宽高比（16:9|4:3|...）
- `MAX_DESCRIPTION_WORKERS`: 描述生成最大并发数
- `MAX_IMAGE_WORKERS`: 图片生成最大并发数
- `BAIDU_OCR_API_KEY`: 百度 OCR API 密钥（用于可编辑导出）

### 健康检查

- **后端健康检查**：`GET /health`
- **Docker 健康检查**：每 30 秒检查一次

---

## 扩展性设计

### AI 提供商扩展

通过 Provider 模式，可以轻松添加新的 AI 提供商：

1. 实现 `TextProvider` 或 `ImageProvider` 接口
2. 在 `ai_providers/__init__.py` 中注册
3. 在配置中指定使用新的提供商

### 文件解析扩展

通过扩展 `FileParserService`，可以支持更多文件格式。

### 导出格式扩展

通过扩展 `ExportService`，可以支持更多导出格式（如 ODP、HTML 等）。

---

## 性能优化

### 前端优化

- **代码分割**：使用 Vite 的自动代码分割
- **懒加载**：路由级别的懒加载
- **防抖**：输入框和保存操作使用防抖

### 后端优化

- **并发处理**：使用 ThreadPoolExecutor 并行处理任务
- **数据库优化**：使用 SQLite WAL 模式，支持并发读写
- **缓存**：AI 响应可以缓存（未来可扩展）

### 文件存储优化

- **版本管理**：图片版本管理，避免重复存储
- **清理策略**：定期清理临时文件（未来可扩展）

---

## 安全考虑

### 文件上传安全

- 文件类型验证
- 文件大小限制
- 文件名清理（防止路径遍历）

### API 安全

- CORS 配置
- 输入验证
- SQL 注入防护（使用 SQLAlchemy ORM）

### 数据安全

- 敏感信息（API 密钥）存储在环境变量或数据库设置中
- 数据库文件权限控制

---

## 测试架构

### 测试类型

1. **单元测试**：`backend/tests/unit/`
   - 测试服务层逻辑
   - 测试工具函数

2. **集成测试**：`backend/tests/integration/`
   - 测试 API 端点
   - 测试完整工作流程

3. **前端测试**：`frontend/src/tests/`
   - 组件测试
   - Store 测试

4. **E2E 测试**：`frontend/e2e/`
   - 使用 Playwright
   - 测试完整用户流程

---

## 总结

Banana Slides 采用现代化的前后端分离架构，具有以下特点：

1. **清晰的层次结构**：Controller-Service-Model 三层架构
2. **可扩展的设计**：Provider 模式支持多种 AI 提供商
3. **异步任务处理**：使用 ThreadPoolExecutor 处理长时间任务
4. **灵活的文件管理**：支持项目级和全局文件存储
5. **完善的版本管理**：图片版本历史记录
6. **易于部署**：Docker Compose 一键部署

该架构设计支持快速迭代和功能扩展，同时保持了代码的可维护性和可测试性。

---

**文档版本**：v0.3.0  
**最后更新**：2024年1月

