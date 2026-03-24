# Banana Slides 后端工作流程文档

## 📋 目录

1. [概述](#概述)
2. [完整工作流程概览](#完整工作流程概览)
3. [步骤 1：创建项目](#步骤-1创建项目)
4. [步骤 2：生成大纲](#步骤-2生成大纲)
5. [步骤 3：生成页面描述](#步骤-3生成页面描述)
6. [步骤 4：生成页面图片](#步骤-4生成页面图片)
7. [风格描述文本的应用](#风格描述文本的应用)
8. [数据流转图](#数据流转图)

---

## 概述

本文档详细说明 Banana Slides 后端从用户输入主题到生成完整 PPT 的整个工作流程。以 **"主题输入"（idea 类型）** 为例，详细描述每一步的输入、处理过程和输出。

### 工作流程类型

Banana Slides 支持三种创建类型：

- **idea**：从一句话主题生成 PPT（本文档示例）
- **outline**：从用户提供的大纲文本生成 PPT
- **descriptions**：从用户提供的页面描述文本生成 PPT

---

## 完整工作流程概览

```
用户输入主题
    │
    ├─→ 步骤 1：创建项目
    │   └─→ 保存项目到数据库
    │
    ├─→ 步骤 2：生成大纲
    │   ├─→ 调用 AI 生成大纲和风格指令
    │   ├─→ 解析 AI 响应
    │   └─→ 创建 Page 记录
    │
    ├─→ 步骤 3：生成页面描述
    │   ├─→ 创建异步任务
    │   ├─→ 并行生成每页描述
    │   └─→ 更新 Page.description_content
    │
    └─→ 步骤 4：生成页面图片
        ├─→ 创建异步任务
        ├─→ 并行生成每页图片
        └─→ 保存图片并创建版本记录
```

---

## 步骤 1：创建项目

### API 端点

```
POST /api/projects
```

### 输入

**请求体（JSON）**：

```json
{
  "creation_type": "idea",
  "idea_prompt": "人工智能的发展历程与应用前景",
  "template_style": null  // 可选：风格描述文本
}
```

**字段说明**：

- `creation_type`：创建类型，必填，值为 `"idea"`、`"outline"` 或 `"descriptions"`
- `idea_prompt`：主题提示词，当 `creation_type="idea"` 时必填
- `template_style`：风格描述文本（可选），用于无模板图模式

### 处理过程

**控制器**：`project_controller.py::create_project()`

1. **验证请求数据**

   - 检查 `creation_type` 是否存在且有效
   - 根据 `creation_type` 验证对应的必填字段
2. **创建项目记录**

   ```python
   project = Project(
       creation_type='idea',
       idea_prompt='人工智能的发展历程与应用前景',
       template_style=None,
       status='DRAFT'
   )
   db.session.add(project)
   db.session.commit()
   ```
3. **返回响应**

### 输出

**响应（JSON）**：

```json
{
  "success": true,
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "DRAFT",
    "pages": []
  }
}
```

**数据库状态**：

**projects 表**：

| 字段             | 值                                       |
| ---------------- | ---------------------------------------- |
| id               | `550e8400-e29b-41d4-a716-446655440000` |
| creation_type    | `idea`                                 |
| idea_prompt      | `人工智能的发展历程与应用前景`         |
| outline_text     | `NULL`                                 |
| description_text | `NULL`                                 |
| template_style   | `NULL`                                 |
| status           | `DRAFT`                                |
| created_at       | `2024-01-15 10:00:00`                  |
| updated_at       | `2024-01-15 10:00:00`                  |

---

## 步骤 2：生成大纲

### API 端点

```
POST /api/projects/{project_id}/generate/outline
```

### 输入

**请求体（JSON）**：

```json
{
  "idea_prompt": "人工智能的发展历程与应用前景"  // 可选，如果不提供则使用项目中的值
}
```

**查询参数**：

- `language`：输出语言（可选），值为 `zh`、`en`、`ja` 或 `auto`，默认从配置读取

### 处理过程

**控制器**：`project_controller.py::generate_outline()`

1. **获取项目信息**

   - 从数据库加载项目
   - 获取参考文件内容（如果有）
2. **构建项目上下文**

   ```python
   project_context = ProjectContext(
       project=project,
       reference_files_content=reference_files_content
   )
   ```
3. **调用 AI 服务生成大纲**

   ```python
   ai_service = get_ai_service()
   outline, style_instructions = ai_service.generate_outline(
       project_context, 
       language='zh'
   )
   ```
4. **AI 提示词（Prompt）**

   调用 `prompts.py::get_outline_generation_prompt()` 生成提示词：

   ```python
   """
   你是一位世界级的演示文稿设计师和故事讲述者。你创作的幻灯片在视觉上令人震撼、极其精美，并能有效地传达复杂的信息。

   **首先**，在编写幻灯片大纲之前，你必须根据内容主题和用户请求生成一个全局性的**风格指令（style_instructions）**。

   你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。

   **核心指令 (CORE DIRECTIVES):**
   1. 分析用户提示词的结构、意图和关键要素。
   2. 将指令转化为干净、结构化的视觉隐喻（蓝图、展示图、原理图）。
   3. 使用特定的、克制的调色板和字体系列，以获得最大的清晰度和专业影响力。
   4. 所有视觉输出必须严格保持 16:9 的长宽比。
   5. 以三联画（triptych）或基于网格的布局呈现信息，保持文本和视觉的平衡。

   **输出格式要求（JSON）：**
   {
     "style_instructions": {
       "design_aesthetic": "详细的设计美学描述...",
       "background_color": "背景色描述及十六进制代码",
       "primary_font": "标题字体名称及使用说明",
       "secondary_font": "正文字体名称及使用说明",
       "primary_text_color": "主要文字颜色描述及十六进制代码",
       "accent_color": "强调色描述及十六进制代码",
       "visual_elements": "视觉元素的详细描述"
     },
     "outline": [...]
   }

   **大纲结构有两种格式：**
   1. 简单格式（适用于短PPT）：
     "outline": [{"title": "标题1", "points": ["要点1", "要点2"]}, ...]

   2. 分章节格式（适用于长PPT）：
     "outline": [{
       "part": "第一部分：引言",
       "pages": [{"title": "欢迎", "points": ["要点1", "要点2"]}, ...]
     }, ...]

   **重要规则：**
   - 第1页必须是封面页，最后一页必须是封底页
   - 避免使用"标题：副标题"的格式
   - 明确避免陈词滥调的"AI废话"模式
   - 使用直接、自信、主动的人类语言
   - 封面页只包含标题和副标题，不包含占位符信息

   用户需求：人工智能的发展历程与应用前景

   现在生成 JSON 输出，不要包含任何其他文字。
   请使用全中文输出。
   """
   ```
5. **AI 响应示例**

   ```json
   {
     "style_instructions": {
       "design_aesthetic": "你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。\n\n**核心指令 (CORE DIRECTIVES):**\n1. 分析用户提示词的结构、意图和关键要素。\n2. 将指令转化为干净、结构化的视觉隐喻（蓝图、展示图、原理图）。\n3. 使用特定的、克制的调色板和字体系列，以获得最大的清晰度和专业影响力。\n4. 所有视觉输出必须严格保持 16:9 的长宽比。\n5. 以三联画（triptych）或基于网格的布局呈现信息，保持文本和视觉的平衡。\n\n在此基础上，详细描述整体风格。参考示例：\"计算野兽派\"与\"精密工程学\"的结合。风格冷峻、理性，强调数据结构的美感。视觉隐喻应围绕\"信息压缩\"、\"切片\"和\"流体动力学\"展开。整体感觉像是一份来自未来的、针对语言模型经济学的解密报告。",
       "background_color": "深空灰 (Deep Space Grey), #1A1A1A。这为高亮数据提供了极佳的对比度，减少屏幕眩光，适合深度阅读。",
       "primary_font": "Helvetica Now Display (Bold/Black)。用于极具冲击力的标题，字间距紧凑，传达权威感。",
       "secondary_font": "JetBrains Mono。一种为代码和数据设计的等宽字体，用于正文、标注和数据点，强化\"计算\"和\"工程\"的语境。",
       "primary_text_color": "雾白 (Mist White), #E0E0E0",
       "accent_color": "信号橙 (Signal Orange), #FF5722 (代表成本/警示) 和 荧光青 (Cyber Cyan), #00BCD4 (代表效率/DeepSeek)",
       "visual_elements": "细如发丝的白色网格线作为背景纹理。使用半透明的几何体表示\"令牌(Token)\"。图表应采用极简的线图或热力图风格。避免任何装饰性的插画，一切元素必须服务于数据表达。"
     },
     "outline": [
       {
         "title": "人工智能：从概念到现实",
         "points": ["AI 的定义与核心概念", "为什么 AI 在今天如此重要"]
       },
       {
         "title": "AI 的发展历程",
         "points": ["1950 年代：图灵测试的提出", "1980 年代：专家系统的兴起", "2010 年代：深度学习的突破", "2020 年代：大语言模型的崛起"]
       },
       {
         "title": "AI 的核心技术",
         "points": ["机器学习基础", "神经网络架构", "自然语言处理", "计算机视觉"]
       },
       {
         "title": "AI 的应用场景",
         "points": ["医疗诊断与药物研发", "自动驾驶技术", "智能推荐系统", "内容生成与创作"]
       },
       {
         "title": "AI 的未来展望",
         "points": ["通用人工智能（AGI）的可能性", "AI 与人类的协作模式", "伦理与安全的挑战"]
       },
       {
         "title": "结语：智能时代的到来",
         "points": ["AI 正在重塑我们的世界", "拥抱变化，共创未来"]
       }
     ]
   }
   ```
6. **解析 AI 响应**

   ```python
   # 在 ai_service.py::generate_outline() 中
   result = self.generate_json(outline_prompt, thinking_budget=1000)
   outline, style_instructions = self._extract_outline_and_style(result)
   ```
7. **保存风格指令**

   ```python
   if style_instructions and not project.template_image_path:
       project.template_style = json.dumps(style_instructions, ensure_ascii=False)
   ```
8. **扁平化大纲结构**

   ```python
   pages_data = ai_service.flatten_outline(outline)
   # 将分章节格式转换为页面列表
   ```
9. **创建 Page 记录**

   ```python
   # 删除旧页面（如果存在）
   old_pages = Page.query.filter_by(project_id=project_id).all()
   for old_page in old_pages:
       db.session.delete(old_page)

   # 创建新页面
   for index, page_data in enumerate(pages_data):
       page = Page(
           project_id=project_id,
           order_index=index,
           part=page_data.get('part'),
           outline_content=json.dumps(page_data, ensure_ascii=False),
           status='DRAFT'
       )
       db.session.add(page)

   db.session.commit()
   ```

### 输出

**响应（JSON）**：

```json
{
  "success": true,
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "outline": [
      {
        "title": "人工智能：从概念到现实",
        "points": ["AI 的定义与核心概念", "为什么 AI 在今天如此重要"]
      },
      // ... 其他页面
    ],
    "style_instructions": {
      "design_aesthetic": "...",
      "background_color": "...",
      // ... 其他风格字段
    }
  }
}
```

**数据库状态**：

**projects 表

| 字段           | 值                                                                            |
| -------------- | ----------------------------------------------------------------------------- |
| template_style | `{"design_aesthetic": "...", "background_color": "...", ...}` (JSON 字符串) |
| status         | `OUTLINE_GENERATED`                                                         |

**pages 表**（示例，共 6 页）：

| id         | project_id     | order_index | part     | outline_content                                          | status    |
| ---------- | -------------- | ----------- | -------- | -------------------------------------------------------- | --------- |
| `page-1` | `project-id` | 0           | `NULL` | `{"title": "人工智能：从概念到现实", "points": [...]}` | `DRAFT` |
| `page-2` | `project-id` | 1           | `NULL` | `{"title": "AI 的发展历程", "points": [...]}`          | `DRAFT` |
| ...        | ...            | ...         | ...      | ...                                                      | ...       |

---

## 步骤 3：生成页面描述

### API 端点

```
POST /api/projects/{project_id}/generate/descriptions
```

### 输入

**请求体（JSON）**：

```json
{
  "max_workers": 5,  // 可选，默认 5
  "language": "zh"   // 可选，默认从配置读取
}
```

### 处理过程

**控制器**：`project_controller.py::generate_descriptions()`

1. **获取项目信息**

   - 从数据库加载项目和页面
   - 获取参考文件内容
   - 重建大纲结构
2. **创建异步任务**

   ```python
   task = Task(
       project_id=project_id,
       task_type='GENERATE_DESCRIPTIONS',
       status='PENDING'
   )
   task.set_progress({
       'total': len(pages),
       'completed': 0,
       'failed': 0
   })
   db.session.add(task)
   db.session.commit()
   ```
3. **提交后台任务**

   ```python
   task_manager.submit_task(
       task.id,
       generate_descriptions_task,
       project_id,
       ai_service,
       project_context,
       outline,
       max_workers=5,
       app=current_app._get_current_object(),
       language='zh',
       style_instructions=style_instructions
   )
   ```
4. **后台任务处理**：`task_manager.py::generate_descriptions_task()`

   **并行生成每页描述**：

   ```python
   with ThreadPoolExecutor(max_workers=max_workers) as executor:
       futures = [
           executor.submit(generate_single_description, page, page_data, i)
           for i, (page, page_data) in enumerate(zip(pages, pages_data), 1)
       ]
   ```
5. **生成单页描述**：`ai_service.py::generate_page_description()`

   **AI 提示词（Prompt）**：

   调用 `prompts.py::get_page_description_prompt()` 生成提示词：

   ```python
   """
   你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。


   **核心指令 (CORE DIRECTIVES):**
   1. 分析内容的结构、意图和关键要素
   2. 将指令转化为干净、结构化的视觉隐喻（蓝图、展示图、原理图、建筑图纸风格）
   3. 所有视觉输出必须严格保持 16:9 的长宽比
   4. 以三联画（triptych）或基于网格的布局呈现信息，保持文本和视觉的平衡
   5. 背景应有精细的底纹（如细如发丝的网格线、蓝图纹理、淡得几不可察的公式水印）
   6. 使用半透明的几何体、矢量线条、流形曲面等精密工程元素
   7. 图表采用极简的线图或热力图风格，避免装饰性插画

   <context>
   用户的原始需求：人工智能的发展历程与应用前景

   完整大纲：
   [
     {"title": "人工智能：从概念到现实", "points": [...]},
     {"title": "AI 的发展历程", "points": [...]},
     ...
   ]
   </context>

   <style_instructions>
   设计美学：你是架构师（The Architect）...
   背景色：深空灰 (Deep Space Grey), #1A1A1A
   标题字体：Helvetica Now Display (Bold/Black)
   正文字体：JetBrains Mono
   主要文字颜色：雾白 (Mist White), #E0E0E0
   强调色：信号橙 (Signal Orange), #FF5722 和 荧光青 (Cyber Cyan), #00BCD4
   视觉元素：细如发丝的白色网格线作为背景纹理...
   </style_instructions>

   现在请为第 1 页生成描述：
   {"title": "人工智能：从概念到现实", "points": ["AI 的定义与核心概念", "为什么 AI 在今天如此重要"]}

   **【封面页设计要求】**
   - 这是PPT的封面页，应采用"海报式"布局
   - 内容保持极简：只放标题和副标题，**切勿包含任何占位符（如"汇报人"、"日期"、"地点"等）**
   - 视觉上要醒目，使用满版出血图像或强烈的排版
   - 需要一下就能抓住观众的注意力

   **请严格按照以下格式输出（详细描述，充分展现视觉隐喻）：**

   幻灯片 1：封面 (The Cover)

   // NARRATIVE GOAL (叙事目标)
   详细解释这张幻灯片在整个故事弧光中的具体叙事目的。这不仅是技术的介绍，更是一场关于主题的哲学宣示。描述它如何打破观众的固有认知，如何推动整体叙事，为后续内容奠定什么样的基调。

   // KEY CONTENT (关键内容)

   主标题：[使用叙事性的主题句，富有张力和深度]
   副标题：[简洁有力的副标题，补充主标题的维度]

   // VISUAL (视觉画面)
   用连续的段落详细描述视觉元素，使用建筑图纸/蓝图风格的视觉隐喻。参考示例：

   "海报式布局。背景是深邃的网格。画面中央是一个巨大的、半透明的立方体（代表信息总量），它正在通过一个光栅（代表Tokenizer）。光栅左侧是汉字"道"，右侧是英文单词"Logos"。汉字穿过光栅后变成了少量、致密的发光晶体；英文穿过光栅后变成了大量、松散的碎片。这种视觉隐喻直观地展示了"密度"与"切分"的关系。"

   你的描述应包含：
   - 核心视觉元素（如动态粒子系统、半透明几何体、流形曲面、信息流图、数据切片、光栅、晶体等）
   - 背景底纹（如深邃的网格、蓝图纹理、淡如水印的公式等）
   - 视觉隐喻（画面如何象征内容的核心概念）
   - 动态感（元素的流动、透明度变化、延伸方式等）

   **不要写具体的颜色十六进制代码，用描述性语言代替（如"深邃的背景"、"高亮的强调色"）。**

   // LAYOUT (布局结构)
   用连续的段落描述页面构图和空间安排。参考示例：

   "标题使用超大号字体居左下对齐，占据视觉重心的40%。右侧是核心视觉隐喻。顶部有一行极小的代码样式的元数据（时间、地点、研究代号）。"

   你的描述应包含：
   - 构图模式（非对称动态平衡、满版出血、三联画布局等）
   - 标题排版（位置、相对大小、排版风格）
   - 视觉重心（核心视觉元素占据的位置和比例）
   - 留白策略（哪些区域保留纯净空间）

   **重要规则：**
   - **封面页切勿包含任何占位符**：不要包含"汇报人"、"日期"、"地点"、"姓名"等占位符信息。封面页只包含标题和副标题。
   - 充分发挥视觉隐喻，将抽象概念转化为可视化的建筑图纸/蓝图风格
   - 不要写具体的颜色代码（如#FF5722），用描述性语言（如"高亮强调色"、"深邃背景色"）
   - "页面文字"部分会直接渲染到PPT上，必须简洁精炼
   - 避免使用"标题：副标题"的格式；使用叙事性的主题句
   - 避免AI废话模式，切勿使用"不仅仅是[X]，而是[Y]"等套话
   - 使用直接、自信、主动的人类语言
   - 永远假设听众比你想象的更专业、更感兴趣、更聪明

   请使用全中文输出。
   """
   ```
6. **AI 响应示例**（第 1 页，封面页）

   ```
   幻灯片 1：封面 (The Cover)

   // NARRATIVE GOAL (叙事目标)
   这张封面页是整个演示文稿的哲学宣言，它要打破观众对人工智能的固有认知——AI 不是科幻小说中的遥远概念，而是正在重塑我们世界的现实力量。它通过视觉隐喻建立"智能"与"进化"的关联，为后续的技术细节奠定情感和认知基础。

   // KEY CONTENT (关键内容)

   主标题：智能的觉醒：从算法到意识
   副标题：探索人工智能如何从计算工具演变为认知伙伴

   // VISUAL (视觉画面)

   海报式布局，背景是深邃的网格纹理，如同未来城市的数字蓝图。画面中央是一个巨大的、半透明的神经网络结构，由无数发光的节点和连接线组成，象征着 AI 的复杂性和互联性。这个网络结构正在缓慢旋转，节点之间的连接线闪烁着数据流动的光芒。

   在网络的中心，有一个逐渐显现的人形轮廓，由光点构成，代表着人类智能与机器智能的融合。轮廓周围环绕着三个半透明的几何体：一个立方体代表"数据"，一个球体代表"算法"，一个锥体代表"应用"。这些几何体通过光流连接到网络的不同节点，形成动态的信息流动。

   背景的网格线在视觉焦点处逐渐变亮，形成一种"聚焦"效果，引导观众的视线。在画面的边缘，有淡得几乎不可见的公式和代码片段作为水印，暗示着 AI 背后的数学和工程基础。

   // LAYOUT (布局结构)

   采用非对称动态平衡布局。主标题使用超大号字体，采用 Helvetica Now Display Black 字重，居左下对齐，占据视觉重心的 35%。标题文字采用雾白色，在深色背景上形成强烈对比。

   副标题位于主标题下方，使用较小的字号，采用 JetBrains Mono 等宽字体，与主标题形成层次对比。副标题采用荧光青色，作为强调色。

   核心视觉隐喻（神经网络结构）占据画面右侧和中央，占据视觉重心的 60%。网络结构采用半透明效果，与背景网格形成深度层次。

   画面顶部有一行极小的代码样式元数据，采用 JetBrains Mono 字体，颜色为深灰色，显示"AI-2024"和"智能时代研究"等标识信息。

   留白策略：画面左侧和底部保留纯净空间，让标题和视觉元素有呼吸空间，避免视觉拥挤。
   ```
7. **解析并保存描述**

   ```python
   # 在 generate_descriptions_task 中
   description_text = ai_service.generate_page_description(
       project_context, outline, page_data, page_index,
       language='zh', style_instructions=style_instructions,
       total_pages=len(pages)
   )

   # 解析描述文本（提取 NARRATIVE GOAL, KEY CONTENT, VISUAL, LAYOUT）
   parsed_desc = _parse_page_description(description_text)

   # 保存到数据库
   page.set_description_content({
       'text': description_text,
       'narrative_goal': parsed_desc.get('narrative_goal', ''),
       'key_content': parsed_desc.get('key_content', ''),
       'visual': parsed_desc.get('visual', ''),
       'layout': parsed_desc.get('layout', '')
   })
   page.status = 'DESCRIPTION_GENERATED'
   db.session.commit()
   ```
8. **更新任务进度**

   ```python
   task.update_progress({
       'total': len(pages),
       'completed': completed,
       'failed': failed
   })
   db.session.commit()
   ```

### 输出

**响应（JSON）**（立即返回，不等待任务完成）：

```json
{
  "success": true,
  "data": {
    "task_id": "task-uuid-123",
    "status": "PENDING"
  }
}
```

**前端轮询任务状态**：

```
GET /api/tasks/{task_id}
```

**任务状态响应**：

```json
{
  "success": true,
  "data": {
    "task_id": "task-uuid-123",
    "status": "PROCESSING",  // 或 "COMPLETED", "FAILED"
    "progress": {
      "total": 6,
      "completed": 3,
      "failed": 0
    }
  }
}
```

**数据库状态**：

**tasks 表**：

| id                | project_id     | task_type                 | status        | progress                                      | created_at              |
| ----------------- | -------------- | ------------------------- | ------------- | --------------------------------------------- | ----------------------- |
| `task-uuid-123` | `project-id` | `GENERATE_DESCRIPTIONS` | `COMPLETED` | `{"total": 6, "completed": 6, "failed": 0}` | `2024-01-15 10:05:00` |

**pages 表**（更新后）：

| id         | description_content                                                                                                | status                    |
| ---------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------- |
| `page-1` | `{"text": "幻灯片 1：封面...", "narrative_goal": "...", "key_content": "...", "visual": "...", "layout": "..."}` | `DESCRIPTION_GENERATED` |
| `page-2` | `{"text": "幻灯片 2：...", ...}`                                                                                 | `DESCRIPTION_GENERATED` |
| ...        | ...                                                                                                                | ...                       |

**projects 表**：

| status                     |
| -------------------------- |
| `DESCRIPTIONS_GENERATED` |

---

## 步骤 4：生成页面图片

### API 端点

```
POST /api/projects/{project_id}/generate/images
```

### 输入

**请求体（JSON）**：

```json
{
  "max_workers": 8,        // 可选，默认 8
  "use_template": true,    // 可选，默认 true（是否使用模板图片）
  "language": "zh",       // 可选，默认从配置读取
  "page_ids": null        // 可选，指定要生成的页面 ID 列表（null 表示生成所有页面）
}
```

### 处理过程

**控制器**：`project_controller.py::generate_images()`

1. **获取项目信息**

   - 从数据库加载项目和页面
   - 重建大纲结构
   - 解析风格指令
2. **创建异步任务**

   ```python
   task = Task(
       project_id=project_id,
       task_type='GENERATE_IMAGES',
       status='PENDING'
   )
   task.set_progress({
       'total': len(pages),
       'completed': 0,
       'failed': 0
   })
   db.session.add(task)
   db.session.commit()
   ```
3. **提交后台任务**

   ```python
   task_manager.submit_task(
       task.id,
       generate_images_task,
       project_id,
       ai_service,
       file_service,
       outline,
       use_template=True,
       max_workers=8,
       aspect_ratio='16:9',
       resolution='2K',
       app=current_app._get_current_object(),
       extra_requirements=combined_requirements,
       language='zh',
       page_ids=None,
       style_instructions=style_instructions
   )
   ```
4. **后台任务处理**：`task_manager.py::generate_images_task()`

   **并行生成每页图片**：

   ```python
   with ThreadPoolExecutor(max_workers=max_workers) as executor:
       futures = [
           executor.submit(generate_single_image, page.id, page_data, i)
           for i, (page, page_data) in enumerate(zip(pages, pages_data), 1)
       ]
   ```
5. **生成单页图片**：`generate_single_image()`

   **步骤 5.1：获取页面描述**

   ```python
   page_obj = Page.query.get(page_id)
   desc_content = page_obj.get_description_content()
   desc_text = desc_content.get('text', '')
   ```

   **步骤 5.2：提取图片 URL**（从描述中的 Markdown 图片链接）

   ```python
   image_urls = ai_service.extract_image_urls_from_markdown(desc_text)
   # 例如：从描述中提取 ![](/files/materials/image_123.png)
   ```

   **步骤 5.3：获取模板图片路径**

   ```python
   if use_template:
       page_ref_image_path = file_service.get_template_path(project_id)
   ```

   **步骤 5.4：生成图片提示词**

   调用 `prompts.py::get_image_generation_prompt()` 生成提示词：

   ```python
   """
   你是一位专家级UI UX演示设计师，专注于生成设计良好的PPT页面。
   【叙事目标】这张封面页是整个演示文稿的哲学宣言，它要打破观众对人工智能的固有认知...

   当前PPT页面的内容如下:
   <page_content>
   主标题：智能的觉醒：从算法到意识
   副标题：探索人工智能如何从计算工具演变为认知伙伴
   </page_content>

   <style_instructions>
   设计美学：你是架构师（The Architect）...
   背景色：深空灰 (Deep Space Grey), #1A1A1A
   标题字体：Helvetica Now Display (Bold/Black)
   正文字体：JetBrains Mono
   主要文字颜色：雾白 (Mist White), #E0E0E0
   强调色：信号橙 (Signal Orange), #FF5722 和 荧光青 (Cyber Cyan), #00BCD4
   视觉元素风格：细如发丝的白色网格线作为背景纹理...
   </style_instructions>

   <visual_and_layout_instructions>
   【视觉画面要求】
   海报式布局，背景是深邃的网格纹理，如同未来城市的数字蓝图。画面中央是一个巨大的、半透明的神经网络结构，由无数发光的节点和连接线组成，象征着 AI 的复杂性和互联性。这个网络结构正在缓慢旋转，节点之间的连接线闪烁着数据流动的光芒。

   在网络的中心，有一个逐渐显现的人形轮廓，由光点构成，代表着人类智能与机器智能的融合。轮廓周围环绕着三个半透明的几何体：一个立方体代表"数据"，一个球体代表"算法"，一个锥体代表"应用"。这些几何体通过光流连接到网络的不同节点，形成动态的信息流动。

   背景的网格线在视觉焦点处逐渐变亮，形成一种"聚焦"效果，引导观众的视线。在画面的边缘，有淡得几乎不可见的公式和代码片段作为水印，暗示着 AI 背后的数学和工程基础。

   【布局结构要求】
   采用非对称动态平衡布局。主标题使用超大号字体，采用 Helvetica Now Display Black 字重，居左下对齐，占据视觉重心的 35%。标题文字采用雾白色，在深色背景上形成强烈对比。

   副标题位于主标题下方，使用较小的字号，采用 JetBrains Mono 等宽字体，与主标题形成层次对比。副标题采用荧光青色，作为强调色。

   核心视觉隐喻（神经网络结构）占据画面右侧和中央，占据视觉重心的 60%。网络结构采用半透明效果，与背景网格形成深度层次。

   画面顶部有一行极小的代码样式元数据，采用 JetBrains Mono 字体，颜色为深灰色，显示"AI-2024"和"智能时代研究"等标识信息。

   留白策略：画面左侧和底部保留纯净空间，让标题和视觉元素有呼吸空间，避免视觉拥挤。
   </visual_and_layout_instructions>

   <reference_information>
   整个PPT的大纲为：
   [
     {"title": "人工智能：从概念到现实", "points": [...]},
     {"title": "AI 的发展历程", "points": [...]},
     ...
   ]

   当前位于章节：封面页
   </reference_information>

   <design_guidelines>
   - 要求文字清晰锐利, 画面为4K分辨率，16:9比例。
   - 配色和设计语言和模板图片严格相似。
   - 根据内容自动设计最完美的构图，不重不漏地渲染页面内容中的文本。
   - 如非必要，禁止出现 markdown 格式符号（如 # 和 * 等）。
   - 只参考风格设计，禁止出现模板中的文字。
   - 使用大小恰当的装饰性图形或插画对空缺位置进行填补。
   - 如有视觉画面和布局结构要求，请严格遵循。
   </design_guidelines>

   PPT文字请使用全中文。

   **注意：当前页面为PPT的封面页，请采用专业的封面设计美学技巧，务必凸显出页面标题，分清主次，确保一下就能抓住观众的注意力。可使用"海报式"布局、醒目的排版或满版出血图像。**
   """
   ```
6. **调用 AI 生成图片**

   ```python
   image = ai_service.generate_image(
       prompt=prompt,
       ref_image_path=page_ref_image_path,  # 模板图片路径（如果有）
       aspect_ratio='16:9',
       resolution='2K',
       additional_ref_images=page_additional_ref_images  # 素材图片列表（如果有）
   )
   ```

   **AI 服务内部处理**：

   - 如果提供了 `ref_image_path`，将其作为参考图片传递给图片生成模型
   - 如果提供了 `additional_ref_images`，将其作为额外参考图片
   - 调用图片生成提供商的 `generate_image()` 方法
   - 返回 PIL Image 对象
7. **保存图片并创建版本记录**

   ```python
   image_path, next_version = save_image_with_version(
       image, project_id, page_id, file_service, page_obj=page_obj
   )
   ```

   **save_image_with_version() 函数处理**：

   ```python
   # 1. 计算下一个版本号
   max_version = db.session.query(func.max(PageImageVersion.version_number))\
       .filter_by(page_id=page_id).scalar() or 0
   next_version = max_version + 1

   # 2. 标记所有旧版本为非当前版本
   PageImageVersion.query.filter_by(page_id=page_id)\
       .update({'is_current': False})

   # 3. 保存图片到最终位置
   image_path = file_service.save_generated_image(
       image, project_id, page_id,
       version_number=next_version,
       image_format='PNG'
   )
   # 保存路径：uploads/{project_id}/pages/page_{page_id}_v{version}.png

   # 4. 创建新版本记录
   new_version = PageImageVersion(
       page_id=page_id,
       image_path=image_path,
       version_number=next_version,
       is_current=True
   )
   db.session.add(new_version)

   # 5. 更新页面状态和图片路径
   page_obj.generated_image_path = image_path
   page_obj.status = 'COMPLETED'
   page_obj.updated_at = datetime.utcnow()

   db.session.commit()
   ```
8. **更新任务进度**

   ```python
   task.update_progress({
       'total': len(pages),
       'completed': completed,
       'failed': failed
   })
   db.session.commit()
   ```

### 输出

**响应（JSON）**（立即返回，不等待任务完成）：

```json
{
  "success": true,
  "data": {
    "task_id": "task-uuid-456",
    "status": "PENDING"
  }
}
```

**前端轮询任务状态**：

```
GET /api/tasks/{task_id}
```

**任务状态响应**：

```json
{
  "success": true,
  "data": {
    "task_id": "task-uuid-456",
    "status": "PROCESSING",  // 或 "COMPLETED", "FAILED"
    "progress": {
      "total": 6,
      "completed": 2,
      "failed": 0
    }
  }
}
```

**数据库状态**：

**tasks 表**：

| id                | project_id     | task_type           | status        | progress                                      | created_at              |
| ----------------- | -------------- | ------------------- | ------------- | --------------------------------------------- | ----------------------- |
| `task-uuid-456` | `project-id` | `GENERATE_IMAGES` | `COMPLETED` | `{"total": 6, "completed": 6, "failed": 0}` | `2024-01-15 10:10:00` |

**pages 表**（更新后）：

| id         | generated_image_path                                 | status        |
| ---------- | ---------------------------------------------------- | ------------- |
| `page-1` | `uploads/{project_id}/pages/page_{page_id}_v1.png` | `COMPLETED` |
| `page-2` | `uploads/{project_id}/pages/page_{page_id}_v1.png` | `COMPLETED` |
| ...        | ...                                                  | ...           |

**page_image_versions 表**（示例，第 1 页）：

| id            | page_id    | image_path                                           | version_number | is_current | created_at              |
| ------------- | ---------- | ---------------------------------------------------- | -------------- | ---------- | ----------------------- |
| `version-1` | `page-1` | `uploads/{project_id}/pages/page_{page_id}_v1.png` | 1              | `true`   | `2024-01-15 10:12:00` |

**projects 表**：

| status        |
| ------------- |
| `COMPLETED` |

**文件系统**：

```
uploads/
└── {project_id}/
    ├── pages/
    │   ├── page_{page-1-id}_v1.png
    │   ├── page_{page-2-id}_v1.png
    │   ├── page_{page-3-id}_v1.png
    │   ├── page_{page-4-id}_v1.png
    │   ├── page_{page-5-id}_v1.png
    │   └── page_{page-6-id}_v1.png
    └── template/
        └── template.png  // 如果有模板图片
```

---

## 风格描述文本的应用

### 什么是风格描述文本（template_style）

`template_style` 是存储在 `Project` 模型中的字段，用于存储 PPT 的全局风格指令。它有两种格式：

1. **JSON 格式**（新格式）：由 AI 生成的结构化风格指令

   ```json
   {
     "design_aesthetic": "你是架构师（The Architect）...",
     "background_color": "深空灰 (Deep Space Grey), #1A1A1A",
     "primary_font": "Helvetica Now Display (Bold/Black)",
     "secondary_font": "JetBrains Mono",
     "primary_text_color": "雾白 (Mist White), #E0E0E0",
     "accent_color": "信号橙 (Signal Orange), #FF5722",
     "visual_elements": "细如发丝的白色网格线作为背景纹理..."
   }
   ```
2. **纯文本格式**（旧格式或用户手动输入）：简单的风格描述文本

   ```
   使用深色背景，现代简约风格，蓝色和橙色作为强调色
   ```

### 风格描述文本的来源

风格描述文本（`template_style`）有两种来源方式：

#### 方式 1：AI 自动生成（主要方式）⭐

**触发时机**：在**步骤 2：生成大纲**时自动生成

**适用场景**：

- **idea 类型**：从主题生成大纲时
- **outline 类型**：解析用户提供的大纲文本时
- **descriptions 类型**：从描述文本解析大纲时

**生成逻辑**：

```python
# 在 project_controller.py::generate_outline() 中

# idea 类型
outline, style_instructions = ai_service.generate_outline(project_context, language=language)

# outline 类型
outline, style_instructions = ai_service.parse_outline_text(project_context, language=language)

# descriptions 类型（在 generate_from_description 中）
outline, style_instructions = ai_service.parse_description_to_outline(project_context, language=language)

# 保存风格指令（如果没有模板图片）
if style_instructions and not project.template_image_path:
    project.template_style = json.dumps(style_instructions, ensure_ascii=False)
```

**AI 生成风格指令的 Prompt 要求**：

在 `prompts.py::get_outline_generation_prompt()` 中，AI 被明确要求：

```
**首先**，在编写幻灯片大纲之前，你必须根据内容主题和用户请求生成一个全局性的**风格指令（style_instructions）**。

你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。

**风格指令说明：**
- design_aesthetic: 根据具体内容和受众，使用独特且有创意的美学风格描述，避免通用的"极简主义"或"商务风格"等泛化描述。参考上述示例，创造符合内容主题的视觉隐喻。
- 字体选择要具体且有设计考量，说明为何选择该字体。
- 颜色选择要有情感和氛围的考量，不仅仅是十六进制代码。
- visual_elements要详细描述线条、形状、图像风格，以及布局的整体氛围。
```

**关键点**：

- ✅ **自动根据主题生成**：AI 会分析用户输入的主题/大纲/描述，智能生成符合内容主题的风格指令
- ✅ **无需用户干预**：用户不需要手动提供风格描述，系统会自动生成
- ✅ **保存条件**：只有当项目没有模板图片时，才会保存 AI 生成的风格指令（如果有模板图片，模板图片是主要参考）

#### 方式 2：用户手动输入（可选方式）

**触发时机**：在**步骤 1：创建项目**时用户手动提供

**适用场景**：

- 用户想要使用"无模板图模式"，通过文字描述来控制风格
- 用户有特定的风格要求，希望覆盖 AI 自动生成的风格

**使用方式**：

```typescript
// 前端代码（useProjectStore.ts）
initializeProject: async (type, content, templateImage, templateStyle) => {
  const request: any = {};
  
  // 添加风格描述（如果有）
  if (templateStyle && templateStyle.trim()) {
    request.template_style = templateStyle.trim();
  }
  
  // 创建项目
  await api.createProject(request);
}
```

**后端处理**：

```python
# 在 project_controller.py::create_project() 中
project = Project(
    creation_type=creation_type,
    idea_prompt=data.get('idea_prompt'),
    template_style=data.get('template_style'),  # 用户提供的风格描述
    status='DRAFT'
)
```

**关键点**：

- ⚠️ **用户可选**：用户可以选择提供或不提供
- ⚠️ **优先级**：如果用户在创建项目时提供了 `template_style`，会覆盖后续 AI 自动生成的风格指令
- ⚠️ **格式灵活**：可以是 JSON 格式或纯文本格式

### 风格描述文本的优先级

```
用户手动输入（创建项目时）
    ↓ （如果存在，优先使用）
AI 自动生成（生成大纲时）
    ↓ （如果没有模板图片，保存到 template_style）
应用到后续步骤（生成描述、生成图片）
```

**实际工作流程**：

1. **用户创建项目时**：

   - 如果提供了 `template_style` → 保存到数据库
   - 如果没有提供 → `template_style` 为 `NULL`
2. **生成大纲时**：

   - 如果 `template_style` 已存在（用户提供）→ **不覆盖**，继续使用用户提供的
   - 如果 `template_style` 为空且没有模板图片 → AI 自动生成并保存
   - 如果 `template_style` 为空但有模板图片 → 不生成风格指令（模板图片是主要参考）
3. **后续步骤**：

   - 使用已保存的 `template_style`（无论是用户提供还是 AI 生成）

### 风格描述文本的应用场景

#### 场景 1：步骤 2 - 生成大纲时（保存风格指令）

**位置**：`project_controller.py::generate_outline()`

**处理逻辑**：

```python
# AI 生成大纲和风格指令
outline, style_instructions = ai_service.generate_outline(project_context, language=language)

# 如果没有模板图片，保存风格指令到 template_style
if style_instructions and not project.template_image_path:
    project.template_style = json.dumps(style_instructions, ensure_ascii=False)
    db.session.commit()
```

**作用**：将 AI 生成的风格指令保存到数据库，供后续步骤使用。

---

#### 场景 2：步骤 3 - 生成页面描述时（应用风格指令）

**位置**：`project_controller.py::generate_descriptions()`

**处理逻辑**：

```python
# 解析风格指令（如果有）
style_instructions = None
if project.template_style:
    try:
        style_instructions = json.loads(project.template_style)
    except (json.JSONDecodeError, TypeError):
        pass  # 如果不是 JSON 格式，忽略（纯文本格式在图片生成时处理）

# 传递给后台任务
task_manager.submit_task(
    task.id,
    generate_descriptions_task,
    ...,
    style_instructions=style_instructions  # 传递给描述生成任务
)
```

**在描述生成提示词中的应用**：`prompts.py::get_page_description_prompt()`

**重要说明**：提示词中的风格描述是**混合的**，包含两部分：

1. **固定部分**（写死的）：提示词开头有一段固定的风格描述，用于设定基础角色和设计理念：
   ```python
   你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。

   你的设计美学是"计算野兽派"与"精密工程学"的结合——风格冷峻、理性，强调数据结构的美感。视觉隐喻围绕"信息压缩"、"切片"和"流体动力学"展开。整体感觉像是一份来自未来的解密报告。
   ```

2. **动态部分**（依据前面的风格提示）：如果传入了 `style_instructions`，会动态插入 `<style_instructions>` 标签：
   ```python
   # 格式化风格指令
   style_section = ""
   if style_instructions:
       style_section = f"""
   <style_instructions>
   设计美学：{style_instructions.get('design_aesthetic', '专业简洁')}
   背景色：{style_instructions.get('background_color', '#FFFFFF')}
   标题字体：{style_instructions.get('primary_font', '思源黑体')}
   正文字体：{style_instructions.get('secondary_font', '思源宋体')}
   主要文字颜色：{style_instructions.get('primary_text_color', '#2F3542')}
   强调色：{style_instructions.get('accent_color', '#007AFF')}
   视觉元素：{style_instructions.get('visual_elements', '简洁线条和图形')}
   </style_instructions>
   """
   ```

**完整的提示词结构**：

```
你是架构师（The Architect）...  [固定部分：基础角色设定]

你的设计美学是"计算野兽派"与"精密工程学"的结合...  [固定部分：基础设计理念]

**核心指令 (CORE DIRECTIVES):**
1. 分析内容的结构、意图和关键要素
2. 将指令转化为干净、结构化的视觉隐喻...
...

<context>
用户的原始需求：...
完整大纲：...
</context>

<style_instructions>  [动态部分：从 template_style 解析而来]
设计美学：...  [从 style_instructions.get('design_aesthetic') 获取]
背景色：...  [从 style_instructions.get('background_color') 获取]
标题字体：...  [从 style_instructions.get('primary_font') 获取]
...
</style_instructions>

现在请为第 X 页生成描述：...
```

**作用**：

- **固定部分**：提供基础的角色设定和设计理念，确保所有描述都遵循"架构师"的设计哲学
- **动态部分**：根据具体项目的风格指令（从步骤 2 生成或用户提供），提供具体的颜色、字体、视觉元素等细节
- 两者结合：固定部分提供设计方向，动态部分提供具体参数，共同指导 AI 生成符合项目风格的页面描述
- 确保描述中的 VISUAL 和 LAYOUT 部分既符合基础设计理念，又体现项目的具体风格要求

---

#### 场景 3：步骤 4 - 生成页面图片时（应用风格指令）

**位置**：`project_controller.py::generate_images()`

**处理逻辑**：

```python
# 解析风格指令和合并额外要求
combined_requirements = project.extra_requirements or ""
style_instructions = None
if project.template_style:
    # 尝试解析为 JSON（新格式的风格指令）
    try:
        style_instructions = json.loads(project.template_style)
    except (json.JSONDecodeError, TypeError):
        # 如果不是 JSON，则作为纯文本风格描述追加到 extra_requirements
        style_requirement = f"\n\nppt页面风格描述：\n\n{project.template_style}"
        combined_requirements = combined_requirements + style_requirement

# 传递给后台任务
task_manager.submit_task(
    task.id,
    generate_images_task,
    ...,
    extra_requirements=combined_requirements if combined_requirements.strip() else None,
    style_instructions=style_instructions  # 如果是 JSON 格式，单独传递
)
```

**在图片生成提示词中的应用**：`prompts.py::get_image_generation_prompt()`

**情况 A：JSON 格式的风格指令（无模板图模式）**

```python
# 格式化风格指令（仅在无模板图时使用）
style_section = ""
if style_instructions and not has_template:
    style_section = f"""
<style_instructions>
设计美学：{style_instructions.get('design_aesthetic', '专业简洁')}
背景色：{style_instructions.get('background_color', '#FFFFFF')}
标题字体：{style_instructions.get('primary_font', '思源黑体')}
正文字体：{style_instructions.get('secondary_font', '思源宋体')}
主要文字颜色：{style_instructions.get('primary_text_color', '#2F3542')}
强调色：{style_instructions.get('accent_color', '#007AFF')}
视觉元素风格：{style_instructions.get('visual_elements', '简洁线条和图形')}
</style_instructions>
"""
```

**情况 B：纯文本格式的风格描述**

如果 `template_style` 不是 JSON 格式，会被追加到 `extra_requirements` 中：

```python
extra_req_text = ""
if extra_requirements and extra_requirements.strip():
    extra_req_text = f"\n\n额外要求（请务必遵循）：\n{extra_requirements}\n"
```

**设计指南的差异**：

```python
# 根据是否有模板生成不同的设计指南内容
template_style_guideline = "- 配色和设计语言和模板图片严格相似。" if has_template else "- 严格按照风格描述进行设计。"
```

**作用**：

- **有模板图片时**：风格指令主要用于补充说明，模板图片是主要参考
- **无模板图片时**：风格指令是唯一的设计指导，AI 必须严格按照风格描述进行设计
- 确保生成的图片符合全局风格，保持视觉一致性

---

### 风格描述文本的应用流程图

```
┌─────────────────────────────────────────────────────────────┐
│              步骤 1：创建项目                                 │
│  用户可提供 template_style（纯文本或 JSON）                  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              步骤 2：生成大纲                                 │
│  ├─→ AI 生成大纲和风格指令                                    │
│  └─→ 如果没有模板图片，保存风格指令到 template_style         │
│      （JSON 格式）                                            │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              步骤 3：生成页面描述                             │
│  ├─→ 解析 template_style 为 style_instructions（JSON）       │
│  ├─→ 传递给描述生成提示词                                     │
│  └─→ 影响描述中的 VISUAL 和 LAYOUT 部分                      │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              步骤 4：生成页面图片                             │
│  ├─→ 解析 template_style                                     │
│  │   ├─→ 如果是 JSON：解析为 style_instructions             │
│  │   └─→ 如果不是 JSON：追加到 extra_requirements           │
│  ├─→ 根据是否有模板图片决定应用方式：                         │
│  │   ├─→ 有模板：风格指令作为补充，模板图片是主要参考         │
│  │   └─→ 无模板：风格指令是唯一设计指导                      │
│  └─→ 传递给图片生成提示词                                     │
└─────────────────────────────────────────────────────────────┘
```

### 关键代码位置总结

| 步骤                     | 文件                      | 函数/方法                         | 说明                     |
| ------------------------ | ------------------------- | --------------------------------- | ------------------------ |
| **保存风格指令**   | `project_controller.py` | `generate_outline()`            | 保存 AI 生成的风格指令   |
| **描述生成应用**   | `project_controller.py` | `generate_descriptions()`       | 解析并传递风格指令       |
| **描述生成提示词** | `prompts.py`            | `get_page_description_prompt()` | 将风格指令格式化到提示词 |
| **图片生成应用**   | `project_controller.py` | `generate_images()`             | 解析并传递风格指令       |
| **图片生成提示词** | `prompts.py`            | `get_image_generation_prompt()` | 将风格指令格式化到提示词 |

### 注意事项

1. **格式兼容性**：

   - 系统同时支持 JSON 格式和纯文本格式
   - JSON 格式会被解析为结构化对象，应用更精确
   - 纯文本格式会被追加到额外要求中，作为文字描述
2. **模板图片优先级**：

   - 如果有模板图片（`template_image_path` 不为空），模板图片是主要参考
   - 风格指令作为补充说明
   - 如果没有模板图片，风格指令是唯一的设计指导
3. **无模板图模式**：

   - 当 `use_template=false` 或没有模板图片时
   - 风格指令会被格式化到 `<style_instructions>` 标签中
   - 设计指南会改为"严格按照风格描述进行设计"

---

## 数据流转图

```
┌─────────────────────────────────────────────────────────────────┐
│                        步骤 1：创建项目                          │
└─────────────────────────────────────────────────────────────────┘
输入: {"creation_type": "idea", "idea_prompt": "人工智能..."}
    │
    ├─→ 验证请求数据
    ├─→ 创建 Project 记录
    └─→ 保存到数据库
    │
输出: {"project_id": "...", "status": "DRAFT"}

┌─────────────────────────────────────────────────────────────────┐
│                        步骤 2：生成大纲                          │
└─────────────────────────────────────────────────────────────────┘
输入: project_id, language="zh"
    │
    ├─→ 构建 ProjectContext
    ├─→ 调用 AI 生成大纲
    │   ├─→ Prompt: get_outline_generation_prompt()
    │   ├─→ AI 响应: {"style_instructions": {...}, "outline": [...]}
    │   └─→ 解析响应
    ├─→ 保存风格指令到 project.template_style
    ├─→ 扁平化大纲结构
    └─→ 创建 Page 记录（每页一个）
    │
输出: {"outline": [...], "style_instructions": {...}}
数据库: projects.status = "OUTLINE_GENERATED", pages 表有 6 条记录

┌─────────────────────────────────────────────────────────────────┐
│                      步骤 3：生成页面描述                         │
└─────────────────────────────────────────────────────────────────┘
输入: project_id, max_workers=5, language="zh"
    │
    ├─→ 创建异步任务 (Task)
    ├─→ 提交后台任务 (generate_descriptions_task)
    │   │
    │   └─→ 并行处理（ThreadPoolExecutor, max_workers=5）
    │       │
    │       ├─→ 页面 1: generate_page_description()
    │       │   ├─→ Prompt: get_page_description_prompt()
    │       │   ├─→ AI 响应: "幻灯片 1：封面...\n// NARRATIVE GOAL..."
    │       │   ├─→ 解析描述（提取 4 部分）
    │       │   └─→ 保存到 page.description_content
    │       │
    │       ├─→ 页面 2: generate_page_description()
    │       │   └─→ ...
    │       │
    │       └─→ 页面 6: generate_page_description()
    │           └─→ ...
    │
    └─→ 立即返回 task_id
    │
输出: {"task_id": "...", "status": "PENDING"}
数据库: tasks 表有 1 条记录, pages.description_content 更新, 
       projects.status = "DESCRIPTIONS_GENERATED"

┌─────────────────────────────────────────────────────────────────┐
│                       步骤 4：生成页面图片                        │
└─────────────────────────────────────────────────────────────────┘
输入: project_id, max_workers=8, use_template=true, language="zh"
    │
    ├─→ 创建异步任务 (Task)
    ├─→ 提交后台任务 (generate_images_task)
    │   │
    │   └─→ 并行处理（ThreadPoolExecutor, max_workers=8）
    │       │
    │       ├─→ 页面 1: generate_single_image()
    │       │   ├─→ 获取页面描述
    │       │   ├─→ 提取图片 URL（从 Markdown）
    │       │   ├─→ 获取模板图片路径
    │       │   ├─→ 生成图片提示词: get_image_generation_prompt()
    │       │   ├─→ 调用 AI 生成图片: ai_service.generate_image()
    │       │   │   ├─→ 输入: prompt, ref_image_path, aspect_ratio, resolution
    │       │   │   └─→ 输出: PIL Image 对象
    │       │   └─→ 保存图片: save_image_with_version()
    │       │       ├─→ 计算版本号
    │       │       ├─→ 保存图片文件
    │       │       ├─→ 创建 PageImageVersion 记录
    │       │       └─→ 更新 page.generated_image_path
    │       │
    │       ├─→ 页面 2: generate_single_image()
    │       │   └─→ ...
    │       │
    │       └─→ 页面 6: generate_single_image()
    │           └─→ ...
    │
    └─→ 立即返回 task_id
    │
输出: {"task_id": "...", "status": "PENDING"}
数据库: tasks 表有 1 条记录, pages.generated_image_path 更新,
       page_image_versions 表有 6 条记录,
       projects.status = "COMPLETED"
文件系统: uploads/{project_id}/pages/ 目录下有 6 张 PNG 图片
```

---

## 关键提示词总结

### 1. 大纲生成提示词

**位置**：`prompts.py::get_outline_generation_prompt()`

**核心内容**：

- 角色设定：世界级演示文稿设计师和故事讲述者
- 风格指令生成：要求生成全局风格指令（design_aesthetic, colors, fonts 等）
- 大纲结构：支持简单格式和分章节格式
- 重要规则：封面页、封底页要求，避免 AI 废话等

### 2. 页面描述生成提示词

**位置**：`prompts.py::get_page_description_prompt()`

**核心内容**：

- 角色设定：架构师（The Architect）
- 输出格式：4 部分结构（NARRATIVE GOAL, KEY CONTENT, VISUAL, LAYOUT）
- 视觉隐喻：建筑图纸/蓝图风格
- 布局要求：详细描述构图、排版、留白等

### 3. 图片生成提示词

**位置**：`prompts.py::get_image_generation_prompt()`

**核心内容**：

- 角色设定：专家级 UI UX 演示设计师
- 页面内容：从描述中提取的关键内容
- 风格指令：设计美学、颜色、字体等
- 视觉和布局指令：从描述中提取的 VISUAL 和 LAYOUT 部分
- 设计指南：分辨率、比例、文字渲染要求等

---

## 异步任务处理机制

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
  "total": 6,
  "completed": 3,
  "failed": 0
}
```

### 前端轮询

前端通过轮询 `GET /api/tasks/{task_id}` 获取任务状态和进度。

---

## 文件存储结构

### 图片存储

```
uploads/
└── {project_id}/
    ├── pages/
    │   ├── page_{page_id}_v1.png  # 第 1 版
    │   ├── page_{page_id}_v2.png  # 第 2 版（如果重新生成）
    │   └── ...
    └── template/
        └── template.png  # 模板图片（如果有）
```

### 版本管理

每次生成新图片时：

1. 计算下一个版本号（MAX(version_number) + 1）
2. 标记所有旧版本为 `is_current = false`
3. 保存新图片为 `page_{page_id}_v{version}.png`
4. 创建新的 `PageImageVersion` 记录，`is_current = true`
5. 更新 `Page.generated_image_path` 指向最新版本

---

## 总结

Banana Slides 后端工作流程采用**异步任务处理**和**并行生成**的设计，确保：

1. **快速响应**：API 立即返回，不阻塞用户
2. **高效处理**：使用 ThreadPoolExecutor 并行处理多个页面
3. **进度跟踪**：实时更新任务进度，前端可轮询获取
4. **版本管理**：支持图片版本历史，可回溯到任意版本
5. **灵活扩展**：支持多种 AI 提供商，易于扩展新功能

整个流程从用户输入主题到生成完整 PPT，涉及 4 个主要步骤，每个步骤都有明确的输入、处理和输出，便于理解和维护。

---

**文档版本**：v0.3.0
**最后更新**：2024年1月
