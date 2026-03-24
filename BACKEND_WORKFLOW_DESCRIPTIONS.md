# Banana Slides 后端工作流程文档 - Descriptions 类型

## 📋 目录

1. [概述](#概述)
2. [完整工作流程概览](#完整工作流程概览)
3. [步骤 1：创建项目](#步骤-1创建项目)
4. [步骤 2：从描述生成大纲和页面描述](#步骤-2从描述生成大纲和页面描述)
5. [步骤 3：生成页面描述（可选）](#步骤-3生成页面描述可选)
6. [步骤 4：生成页面图片](#步骤-4生成页面图片)
7. [风格描述管理](#风格描述管理)
8. [与 Idea 类型的区别对比](#与-idea-类型的区别对比)
9. [数据流转图](#数据流转图)

---

## 概述

本文档详细说明 Banana Slides 后端从**用户提供的页面描述文本**到生成完整 PPT 的整个工作流程。以 **"描述输入"（descriptions 类型）** 为例，详细描述每一步的**输入**、**处理过程**、**提示词**和**输出**。

### 工作流程类型对比

Banana Slides 支持三种创建类型：

- **idea**：从一句话主题生成 PPT
- **outline**：从用户提供的大纲文本生成 PPT
- **descriptions**：从用户提供的页面描述文本生成 PPT（本文档重点）

### Descriptions 类型的特点

- ✅ **用户提供完整的页面描述文本**：用户可以直接提供详细的页面描述，包含视觉和布局要求
- ✅ **一步到位**：在步骤 2 中同时生成大纲和页面描述，跳过 idea 类型的步骤 3
- ✅ **支持格式化描述**：如果用户提供的描述符合格式（包含"幻灯片 X："和四个部分），系统会直接切分使用
- ✅ **智能解析**：如果描述不符合格式，AI 会自动解析并生成符合格式的描述

---

## 完整工作流程概览

```
用户输入描述文本
    │
    ├─→ 步骤 1：创建项目
    │   └─→ 保存项目到数据库（包含 description_text）
    │
    ├─→ 步骤 2：从描述生成大纲和页面描述（特殊端点）
    │   ├─→ 2.1 解析描述文本到大纲结构
    │   │   ├─→ 调用 AI 解析描述
    │   │   ├─→ 提取大纲结构
    │   │   └─→ 生成风格指令
    │   │
    │   └─→ 2.2 切分描述文本到每页描述
    │       ├─→ 检测描述格式
    │       ├─→ 如果符合格式：直接切分
    │       └─→ 如果不符合格式：AI 生成符合格式的描述
    │
    ├─→ 步骤 3：生成页面描述（通常跳过）
    │   └─→ 对于 descriptions 类型，这一步通常不需要
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
  "creation_type": "descriptions",
  "description_text": "幻灯片 1：封面\n// NARRATIVE GOAL\n这张封面页是整个演示文稿的哲学宣言...\n\n// KEY CONTENT\n主标题：人工智能的觉醒\n副标题：从算法到意识\n\n// VISUAL\n海报式布局，背景是深邃的网格纹理...\n\n// LAYOUT\n采用非对称动态平衡布局...\n\n幻灯片 2：AI 的发展历程\n// NARRATIVE GOAL\n...\n\n// KEY CONTENT\n...\n\n// VISUAL\n...\n\n// LAYOUT\n...",
  "template_style": null  // 可选：风格描述文本
}
```

**字段说明**：

- `creation_type`：创建类型，必填，值为 `"descriptions"`
- `description_text`：页面描述文本，必填，可以是：
  - **格式化描述**：包含"幻灯片 X："标记和四个部分（NARRATIVE GOAL, KEY CONTENT, VISUAL, LAYOUT）
  - **非格式化描述**：普通的描述文本，AI 会自动解析并格式化
- `template_style`：风格描述文本（可选），用于无模板图模式

### 处理过程

**控制器**：`project_controller.py::create_project()`

1. **验证请求数据**
   - 检查 `creation_type` 是否存在且为 `"descriptions"`
   - 验证 `description_text` 是否存在

2. **创建项目记录**

   ```python
   project = Project(
       creation_type='descriptions',
       description_text='幻灯片 1：封面\n// NARRATIVE GOAL\n...',
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
| creation_type    | `descriptions`                          |
| idea_prompt      | `NULL`                                 |
| outline_text     | `NULL`                                 |
| description_text | `幻灯片 1：封面\n// NARRATIVE GOAL\n...` |
| template_style   | `NULL`                                 |
| status           | `DRAFT`                                |
| created_at       | `2024-01-15 10:00:00`                  |
| updated_at       | `2024-01-15 10:00:00`                  |

---

## 步骤 2：从描述生成大纲和页面描述

### ⚠️ 重要区别

**Descriptions 类型使用特殊的端点**：`/api/projects/{project_id}/generate/from-description`

这与 idea 类型的 `/api/projects/{project_id}/generate/outline` 不同。

### API 端点

```
POST /api/projects/{project_id}/generate/from-description
```

### 输入

**请求体（JSON）**：

```json
{
  "description_text": "幻灯片 1：封面\n...",  // 可选，如果不提供则使用项目中的值
  "language": "zh"  // 可选，输出语言：zh、en、ja 或 auto
}
```

**查询参数**：

- `language`：输出语言（可选），值为 `zh`、`en`、`ja` 或 `auto`，默认从配置读取

### 处理过程

**控制器**：`project_controller.py::generate_from_description()`

这个端点会执行两个主要步骤：

#### 步骤 2.1：解析描述文本到大纲结构

**AI 服务方法**：`ai_service.py::parse_description_to_outline()`

1. **构建项目上下文**

   ```python
   project_context = ProjectContext(
       project=project,
       reference_files_content=reference_files_content
   )
   ```

2. **调用 AI 解析描述**

   ```python
   outline, style_instructions = ai_service.parse_description_to_outline(
       project_context, 
       language='zh'
   )
   ```

3. **AI 提示词（Prompt）**

   调用 `prompts.py::get_description_to_outline_prompt()` 生成提示词：

   ```python
   """
   你是一位世界级的演示文稿设计师和故事讲述者。你创作的幻灯片在视觉上令人震撼、极其精美，并能有效地传达复杂的信息。

   你需要分析用户提供的PPT描述文本，提取大纲结构，并根据内容主题生成适合的视觉风格。

   用户提供的描述文本：

   幻灯片 1：封面
   // NARRATIVE GOAL
   这张封面页是整个演示文稿的哲学宣言...
   
   // KEY CONTENT
   主标题：人工智能的觉醒
   副标题：从算法到意识
   
   // VISUAL
   海报式布局，背景是深邃的网格纹理...
   
   // LAYOUT
   采用非对称动态平衡布局...

   幻灯片 2：AI 的发展历程
   ...

   **你的任务：**
   1. 从描述文本中提取大纲结构（标题和要点）
   2. 根据内容主题智能生成全局风格指令

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
     "outline": [
       {"title": "人工智能的觉醒", "points": ["从算法到意识", "探索人工智能如何从计算工具演变为认知伙伴"]},
       {"title": "AI 的发展历程", "points": ["1950 年代：图灵测试的提出", "1980 年代：专家系统的兴起", ...]},
       ...
     ]
   }

   **重要规则：**
   - 从描述文本中提取大纲结构
   - 识别每页的标题和要点
   - 如果文本有明确的章节/部分，使用分章节格式
   - 保留原始文本的逻辑结构和组织
   - 要点应该是每页主要内容的简洁摘要
   - 风格指令应根据内容主题智能选择，使用独特且有创意的美学风格

   现在从上述描述文本中提取大纲结构。只返回 JSON，不要包含任何其他文字。
   请使用全中文输出。
   """
   ```

4. **AI 响应示例**

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
         "title": "人工智能的觉醒",
         "points": ["从算法到意识", "探索人工智能如何从计算工具演变为认知伙伴"]
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

5. **解析 AI 响应**

   ```python
   # 在 ai_service.py::parse_description_to_outline() 中
   parse_prompt = get_description_to_outline_prompt(project_context, language)
   result = self.generate_json(parse_prompt, thinking_budget=1000)
   outline, style_instructions = self._extract_outline_and_style(result)
   ```

6. **保存风格指令**

   ```python
   if style_instructions and not project.template_image_path:
       project.template_style = json.dumps(style_instructions, ensure_ascii=False)
   ```

#### 步骤 2.2：切分描述文本到每页描述

**AI 服务方法**：`ai_service.py::parse_description_to_page_descriptions()`

1. **检测描述格式**

   ```python
   # 检测是否符合格式化结构（包含"幻灯片 X："和四个部分）
   if self._detect_formatted_description(description_text):
       # 符合格式：直接切分
       pages = self._parse_formatted_description(description_text)
   else:
       # 不符合格式：使用 AI 生成符合格式的描述
       formatted_prompt = get_description_format_prompt(project_context, outline, language)
       descriptions = self.generate_json(formatted_prompt, thinking_budget=1500)
   ```

2. **情况 A：描述符合格式（直接切分）**

   如果描述文本包含"幻灯片 X："标记和四个部分（NARRATIVE GOAL, KEY CONTENT, VISUAL, LAYOUT），系统会直接切分：

   ```python
   # 使用正则表达式切分
   slide_pattern = r'幻灯片\s*(\d+)[:：]\s*([^\n]*)'
   slide_matches = list(re.finditer(slide_pattern, description_text))
   
   # 为每页提取内容（从当前标记到下一个标记之间）
   for i, match in enumerate(slide_matches):
       start_pos = match.start()
       if i + 1 < len(slide_matches):
           end_pos = slide_matches[i + 1].start()
       else:
           end_pos = len(description_text)
       page_content = description_text[start_pos:end_pos].strip()
       pages.append(page_content)
   ```

3. **情况 B：描述不符合格式（AI 生成）**

   如果描述文本不符合格式，调用 `prompts.py::get_description_format_prompt()` 生成提示词：

   ```python
   """
   你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。

   用户提供的描述文本：

   人工智能的发展历程与应用前景。第一页是封面，展示AI的觉醒。第二页介绍AI的发展历程，从1950年代开始...

   已解析的大纲结构：

   [
     {"title": "人工智能的觉醒", "points": [...]},
     {"title": "AI 的发展历程", "points": [...]},
     ...
   ]

   **你的任务：**
   根据描述文本和大纲结构，为每一页生成符合以下格式的详细描述。

   **输出格式要求（JSON数组）：**
   返回一个JSON数组，每个元素对应大纲中的一页（按顺序），格式如下：

   [
     "幻灯片 1：封面 (The Cover)\\n// NARRATIVE GOAL (叙事目标)\\n[详细解释这张幻灯片在整个故事弧光中的具体叙事目的]\\n\\n// KEY CONTENT (关键内容)\\n主标题：[叙事性主题句]\\n副标题：[简洁有力的副标题]\\n页面文字：\\n- [要点1]\\n- [要点2]\\n\\n// VISUAL (视觉画面)\\n[详细描述支持该观点的视觉元素，使用建筑图纸/蓝图风格的视觉隐喻。描述核心视觉元素、背景底纹、视觉隐喻、动态感等]\\n\\n// LAYOUT (布局结构)\\n[详细描述页面构图和空间安排。描述构图模式、标题排版、视觉重心、留白策略等]",
     "幻灯片 2：[标题]\\n// NARRATIVE GOAL (叙事目标)\\n[...]\\n\\n// KEY CONTENT (关键内容)\\n[...]\\n\\n// VISUAL (视觉画面)\\n[...]\\n\\n// LAYOUT (布局结构)\\n[...]",
     ...
   ]

   **重要规则：**
   - 封面页切勿包含任何占位符：不要包含"汇报人"、"日期"、"地点"等占位符信息
   - 充分发挥视觉隐喻，将抽象概念转化为可视化的建筑图纸/蓝图风格
   - 不要写具体的颜色代码（如#FF5722），用描述性语言（如"高亮强调色"、"深邃背景色"）
   - "页面文字"部分会直接渲染到PPT上，必须简洁精炼
   - 避免使用"标题：副标题"的格式；使用叙事性的主题句
   - 避免AI废话模式，切勿使用"不仅仅是[X]，而是[Y]"等套话
   - 使用直接、自信、主动的人类语言

   请使用全中文输出。
   """
   ```

4. **AI 响应示例**（格式化后的描述）

   ```json
   [
     "幻灯片 1：封面 (The Cover)\n\n// NARRATIVE GOAL (叙事目标)\n这张封面页是整个演示文稿的哲学宣言，它要打破观众对人工智能的固有认知——AI 不是科幻小说中的遥远概念，而是正在重塑我们世界的现实力量。它通过视觉隐喻建立\"智能\"与\"进化\"的关联，为后续的技术细节奠定情感和认知基础。\n\n// KEY CONTENT (关键内容)\n\n主标题：智能的觉醒：从算法到意识\n副标题：探索人工智能如何从计算工具演变为认知伙伴\n\n// VISUAL (视觉画面)\n\n海报式布局，背景是深邃的网格纹理，如同未来城市的数字蓝图。画面中央是一个巨大的、半透明的神经网络结构，由无数发光的节点和连接线组成，象征着 AI 的复杂性和互联性。这个网络结构正在缓慢旋转，节点之间的连接线闪烁着数据流动的光芒。\n\n在网络的中心，有一个逐渐显现的人形轮廓，由光点构成，代表着人类智能与机器智能的融合。轮廓周围环绕着三个半透明的几何体：一个立方体代表\"数据\"，一个球体代表\"算法\"，一个锥体代表\"应用\"。这些几何体通过光流连接到网络的不同节点，形成动态的信息流动。\n\n背景的网格线在视觉焦点处逐渐变亮，形成一种\"聚焦\"效果，引导观众的视线。在画面的边缘，有淡得几乎不可见的公式和代码片段作为水印，暗示着 AI 背后的数学和工程基础。\n\n// LAYOUT (布局结构)\n\n采用非对称动态平衡布局。主标题使用超大号字体，采用 Helvetica Now Display Black 字重，居左下对齐，占据视觉重心的 35%。标题文字采用雾白色，在深色背景上形成强烈对比。\n\n副标题位于主标题下方，使用较小的字号，采用 JetBrains Mono 等宽字体，与主标题形成层次对比。副标题采用荧光青色，作为强调色。\n\n核心视觉隐喻（神经网络结构）占据画面右侧和中央，占据视觉重心的 60%。网络结构采用半透明效果，与背景网格形成深度层次。\n\n画面顶部有一行极小的代码样式元数据，采用 JetBrains Mono 字体，颜色为深灰色，显示\"AI-2024\"和\"智能时代研究\"等标识信息。\n\n留白策略：画面左侧和底部保留纯净空间，让标题和视觉元素有呼吸空间，避免视觉拥挤。",
     "幻灯片 2：AI 的发展历程\n\n// NARRATIVE GOAL (叙事目标)\n这一页通过时间线的形式，展示 AI 从概念到现实的演进过程，帮助观众理解 AI 不是一夜之间出现的，而是经过数十年积累的成果。\n\n// KEY CONTENT (关键内容)\n\n页面文字：\n- 1950 年代：图灵测试的提出\n- 1980 年代：专家系统的兴起\n- 2010 年代：深度学习的突破\n- 2020 年代：大语言模型的崛起\n\n// VISUAL (视觉画面)\n\n采用时间线布局，背景是深空灰色，带有细如发丝的网格线。时间线从左到右延伸，由一条发光的水平线表示，线上有四个关键节点，每个节点代表一个重要的历史时期。\n\n每个节点都是一个半透明的几何体，内部显示对应时期的代表性图像或符号。节点之间用光流连接，表示时间的连续性和技术的演进。节点的大小和亮度根据重要性动态变化。\n\n在时间线的上方，有淡得几乎不可见的年份标签，采用 JetBrains Mono 字体。在时间线的下方，有每个时期的简要说明文字。\n\n// LAYOUT (布局结构)\n\n采用水平时间线布局。时间线占据画面中央，从左到右延伸，占据视觉重心的 60%。\n\n标题位于画面顶部，使用 Helvetica Now Display Bold 字重，居中对齐。标题下方是时间线，时间线下方是每个时期的详细说明。\n\n留白策略：画面左右两侧保留空间，让时间线有延伸感。",
     ...
   ]
   ```

5. **扁平化大纲结构**

   ```python
   pages_data = ai_service.flatten_outline(outline)
   # 将分章节格式转换为页面列表
   ```

6. **创建 Page 记录（同时包含大纲和描述）**

   ```python
   # 删除旧页面（如果存在）
   old_pages = Page.query.filter_by(project_id=project_id).all()
   for old_page in old_pages:
       db.session.delete(old_page)

   # 创建新页面，同时设置大纲和描述
   for i, (page_data, page_desc) in enumerate(zip(pages_data, page_descriptions)):
       page = Page(
           project_id=project_id,
           order_index=i,
           part=page_data.get('part'),
           status='DESCRIPTION_GENERATED'  # 直接设置为已生成描述
       )
       
       # 设置大纲内容
       page.set_outline_content({
           'title': page_data.get('title'),
           'points': page_data.get('points', [])
       })
       
       # 设置描述内容
       desc_content = {
           "text": page_desc,
           "generated_at": datetime.utcnow().isoformat()
       }
       page.set_description_content(desc_content)
       
       db.session.add(page)

   db.session.commit()
   ```

### 输出

**响应（JSON）**：

```json
{
  "success": true,
  "data": {
    "pages": [
      {
        "id": "page-1",
        "order_index": 0,
        "outline_content": {
          "title": "人工智能的觉醒",
          "points": ["从算法到意识", "探索人工智能如何从计算工具演变为认知伙伴"]
        },
        "description_content": {
          "text": "幻灯片 1：封面 (The Cover)\n\n// NARRATIVE GOAL...",
          "generated_at": "2024-01-15T10:05:00"
        },
        "status": "DESCRIPTION_GENERATED"
      },
      // ... 其他页面
    ],
    "status": "DESCRIPTIONS_GENERATED"
  }
}
```

**数据库状态**：

**projects 表**：

| 字段           | 值                                                                            |
| -------------- | ----------------------------------------------------------------------------- |
| template_style | `{"design_aesthetic": "...", "background_color": "...", ...}` (JSON 字符串) |
| status         | `DESCRIPTIONS_GENERATED`                                                     |

**pages 表**（示例，共 6 页）：

| id         | project_id     | order_index | part     | outline_content                                          | description_content                                                                                                | status                    |
| ---------- | -------------- | ----------- | -------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------- |
| `page-1` | `project-id` | 0           | `NULL` | `{"title": "人工智能的觉醒", "points": [...]}` | `{"text": "幻灯片 1：封面...", "generated_at": "..."}`                                                          | `DESCRIPTION_GENERATED` |
| `page-2` | `project-id` | 1           | `NULL` | `{"title": "AI 的发展历程", "points": [...]}`          | `{"text": "幻灯片 2：AI 的发展历程...", "generated_at": "..."}`                                                | `DESCRIPTION_GENERATED` |
| ...        | ...            | ...         | ...      | ...                                                      | ...                                                                                                                | ...                       |

---

## 步骤 3：生成页面描述（可选）

### ⚠️ 重要说明

**对于 descriptions 类型，这一步通常不需要**，因为：

1. 在步骤 2 中已经生成了页面描述
2. 页面状态已经是 `DESCRIPTION_GENERATED`
3. 如果用户想要修改描述，可以使用 `/api/projects/{project_id}/refine/descriptions` 端点

### 如果仍然调用此端点

如果前端仍然调用了 `/api/projects/{project_id}/generate/descriptions`，系统会：

1. 检查页面是否已有描述
2. 如果已有描述，可能会跳过或重新生成（取决于实现）
3. 建议：对于 descriptions 类型，前端应该跳过这一步，直接进入步骤 4

---

## 步骤 4：生成页面图片

### ⚠️ 重要说明

**步骤 4 对于 descriptions 类型和 idea 类型是完全相同的**。

无论项目类型是 `idea`、`outline` 还是 `descriptions`，生成图片的逻辑都使用同一个端点和相同的处理流程。这是因为：

1. **统一的数据结构**：所有类型的页面描述都存储在 `Page.description_content` 字段中
2. **统一的处理逻辑**：都是从描述中提取内容，生成图片提示词，调用 AI 生成图片
3. **统一的风格应用**：都从 `project.template_style` 读取风格描述并应用到提示词中

唯一的区别是**描述内容的来源**：
- **Idea 类型**：描述在步骤 3 中由 AI 生成
- **Descriptions 类型**：描述在步骤 2 中从用户输入解析或格式化

但在生成图片时，都是从 `page.description_content` 中读取，所以后续处理完全一致。

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

**注意**：此函数不区分项目类型，对所有类型使用相同的逻辑。

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
   ```

   **步骤 5.3：获取模板图片路径**

   ```python
   if use_template:
       page_ref_image_path = file_service.get_template_path(project_id)
   ```

   **步骤 5.4：生成图片提示词**

   调用 `prompts.py::get_image_generation_prompt()` 生成提示词（与 idea 类型相同）。

   **步骤 5.5：调用 AI 生成图片**

   ```python
   image = ai_service.generate_image(
       prompt=prompt,
       ref_image_path=page_ref_image_path,
       aspect_ratio='16:9',
       resolution='2K',
       additional_ref_images=page_additional_ref_images
   )
   ```

   **步骤 5.6：保存图片并创建版本记录**

   ```python
   image_path, next_version = save_image_with_version(
       image, project_id, page_id, file_service, page_obj=page_obj
   )
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
    "status": "PROCESSING",
    "progress": {
      "total": 6,
      "completed": 2,
      "failed": 0
    }
  }
}
```

**数据库状态**：

与 idea 类型完全相同。

### 与 Idea 类型的对比

| 对比项           | Idea 类型                                    | Descriptions 类型                                    |
| ---------------- | -------------------------------------------- | ---------------------------------------------------- |
| **API 端点**     | `POST /api/projects/{project_id}/generate/images` | `POST /api/projects/{project_id}/generate/images`（相同） |
| **处理逻辑**     | 从 `page.description_content` 读取描述       | 从 `page.description_content` 读取描述（相同）       |
| **图片生成流程** | 生成提示词 → 调用 AI → 保存图片               | 生成提示词 → 调用 AI → 保存图片（相同）              |
| **风格应用**     | 从 `project.template_style` 读取并应用        | 从 `project.template_style` 读取并应用（相同）        |
| **唯一区别**     | 描述在步骤 3 中生成                          | 描述在步骤 2 中生成（来源不同，但存储格式相同）      |

**结论**：步骤 4 对于所有类型都是完全相同的，代码实现完全一致。

---

## 风格描述管理

### 概述

在 descriptions 类型中，风格描述（`template_style`）的管理遵循以下原则：

1. **用户可以在创建项目时提供风格描述**（可选）
2. **AI 会在解析描述文本时自动生成风格指令**（如果没有模板图片）
3. **用户提供的风格描述优先级更高**（如果已存在，不会覆盖）
4. **风格描述会应用到图片生成阶段**

### 风格描述的生命周期

```
┌─────────────────────────────────────────────────────────────┐
│              步骤 1：创建项目                                 │
│  用户可提供 template_style（纯文本或 JSON）                  │
│  └─→ 保存到 project.template_style                          │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              步骤 2：从描述生成大纲和页面描述                 │
│  ├─→ AI 解析描述文本，生成风格指令                            │
│  └─→ 如果 project.template_style 为空且没有模板图片：       │
│      └─→ 保存 AI 生成的风格指令到 project.template_style      │
│      如果 project.template_style 已存在：                   │
│      └─→ 不覆盖，继续使用用户提供的风格描述                   │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              步骤 4：生成页面图片                             │
│  ├─→ 从 project.template_style 读取风格描述                 │
│  ├─→ 如果是 JSON 格式：解析为 style_instructions              │
│  ├─→ 如果不是 JSON 格式：追加到 extra_requirements           │
│  └─→ 应用到图片生成提示词                                    │
└─────────────────────────────────────────────────────────────┘
```

### 步骤 1：创建项目时的风格描述

**用户输入（可选）**：

```json
{
  "creation_type": "descriptions",
  "description_text": "幻灯片 1：封面\n...",
  "template_style": "简约商务风格，使用深蓝色和白色配色，字体清晰大方，布局整洁"
}
```

**处理逻辑**：

```python
# 在 project_controller.py::create_project() 中
project = Project(
    creation_type='descriptions',
    description_text=data.get('description_text'),
    template_style=data.get('template_style'),  # 用户提供的风格描述（如果有）
    status='DRAFT'
)
```

**数据库状态**：

| 字段           | 值                                 |
| -------------- | ---------------------------------- |
| template_style | `"简约商务风格，使用深蓝色和白色配色..."`（用户提供）或 `NULL` |

### 步骤 2：AI 生成风格指令

**处理逻辑**：

```python
# 在 project_controller.py::generate_from_description() 中

# Step 1: 解析描述文本到大纲结构（同时生成风格指令）
outline, style_instructions = ai_service.parse_description_to_outline(
    project_context, 
    language=language
)

# 保存风格指令到项目（如果没有模板图片）
if style_instructions and not project.template_image_path:
    # 关键：只有当 template_style 为空时，才保存 AI 生成的风格指令
    if not project.template_style:
        project.template_style = json.dumps(style_instructions, ensure_ascii=False)
        db.session.commit()
```

**AI 生成的风格指令格式**（JSON）：

```json
{
  "design_aesthetic": "你是架构师（The Architect）...",
  "background_color": "深空灰 (Deep Space Grey), #1A1A1A",
  "primary_font": "Helvetica Now Display (Bold/Black)",
  "secondary_font": "JetBrains Mono",
  "primary_text_color": "雾白 (Mist White), #E0E0E0",
  "accent_color": "信号橙 (Signal Orange), #FF5722 和 荧光青 (Cyber Cyan), #00BCD4",
  "visual_elements": "细如发丝的白色网格线作为背景纹理..."
}
```

**保存条件**：

1. ✅ **AI 生成了风格指令**（`style_instructions` 不为空）
2. ✅ **项目没有模板图片**（`project.template_image_path` 为空）
3. ✅ **项目还没有风格描述**（`project.template_style` 为空）

**优先级规则**：

```
用户提供的 template_style（步骤 1）
    ↓ （如果存在，优先使用，不覆盖）
AI 生成的 style_instructions（步骤 2）
    ↓ （如果用户没有提供且没有模板图片，保存）
应用到后续步骤（生成图片）
```

### 步骤 4：应用风格描述生成图片

**处理逻辑**：

```python
# 在 project_controller.py::generate_images() 中

# 解析风格指令和合并额外要求
combined_requirements = project.extra_requirements or ""
style_instructions = None

if project.template_style:
    # 尝试解析为 JSON（新格式的风格指令）
    try:
        style_instructions = json.loads(project.template_style)
        # 成功解析：作为结构化对象传递
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

**应用方式**：

#### 情况 A：JSON 格式的风格指令（AI 生成或用户提供的结构化格式）

```python
# 在 prompts.py::get_image_generation_prompt() 中
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

#### 情况 B：纯文本格式的风格描述（用户提供的简单描述）

```python
# 追加到 extra_requirements
extra_req_text = ""
if extra_requirements and extra_requirements.strip():
    extra_req_text = f"\n\n额外要求（请务必遵循）：\n{extra_requirements}\n"
```

### 风格描述格式对比

| 格式类型     | 来源                 | 存储格式 | 应用方式                           |
| ------------ | -------------------- | -------- | ---------------------------------- |
| **JSON 格式** | AI 自动生成          | JSON 字符串 | 解析为 `style_instructions` 对象，格式化到 `<style_instructions>` 标签 |
| **纯文本格式** | 用户手动输入         | 纯文本   | 追加到 `extra_requirements`，作为文字描述 |

### 与模板图片的关系

**有模板图片时**：

- 风格描述作为**补充说明**
- 模板图片是**主要参考**
- 设计指南：`"配色和设计语言和模板图片严格相似。"`

**无模板图片时**：

- 风格描述是**唯一的设计指导**
- 设计指南：`"严格按照风格描述进行设计。"`
- 如果风格描述是 JSON 格式，会格式化到 `<style_instructions>` 标签中

### 关键代码位置总结

| 步骤                     | 文件                      | 函数/方法                         | 说明                     |
| ------------------------ | ------------------------- | --------------------------------- | ------------------------ |
| **保存用户提供的风格**   | `project_controller.py` | `create_project()`              | 保存用户输入的 `template_style` |
| **生成并保存风格指令**   | `project_controller.py` | `generate_from_description()` | 保存 AI 生成的风格指令（如果用户没有提供） |
| **解析风格指令**         | `project_controller.py` | `generate_images()`             | 解析 `template_style` 为 `style_instructions` 或追加到 `extra_requirements` |
| **应用风格指令到提示词** | `prompts.py`            | `get_image_generation_prompt()` | 将风格指令格式化到图片生成提示词 |

### 注意事项

1. **优先级**：
   - 用户提供的风格描述优先级最高
   - 如果用户在创建项目时提供了 `template_style`，AI 不会覆盖它

2. **格式兼容性**：
   - 系统同时支持 JSON 格式和纯文本格式
   - JSON 格式会被解析为结构化对象，应用更精确
   - 纯文本格式会被追加到额外要求中，作为文字描述

3. **模板图片优先级**：
   - 如果有模板图片（`template_image_path` 不为空），模板图片是主要参考
   - 风格描述作为补充说明
   - 如果没有模板图片，风格描述是唯一的设计指导

4. **保存时机**：
   - AI 生成的风格指令只在步骤 2 中保存一次
   - 如果后续用户修改了描述文本并重新生成，风格指令可能会更新（如果 `template_style` 为空）

---

## 与 Idea 类型的区别对比

### 核心区别总结

| 对比项           | Idea 类型                                    | Descriptions 类型                                    |
| ---------------- | -------------------------------------------- | ---------------------------------------------------- |
| **用户输入**     | 一句话主题（如"人工智能的发展历程与应用前景"） | 完整的页面描述文本（包含视觉和布局要求）             |
| **步骤 2**       | 生成大纲（`/generate/outline`）              | 从描述生成大纲和页面描述（`/generate/from-description`） |
| **步骤 3**       | 生成页面描述（必需）                         | 通常跳过（已在步骤 2 中完成）                        |
| **描述来源**     | AI 生成                                      | 用户提供或 AI 格式化                                 |
| **描述格式**     | AI 自动生成符合格式的描述                    | 支持格式化描述（直接切分）或非格式化描述（AI 格式化） |
| **工作流程**     | 4 个步骤（创建→大纲→描述→图片）              | 3 个步骤（创建→大纲+描述→图片）                      |
| **API 端点差异** | `/generate/outline` + `/generate/descriptions` | `/generate/from-description`（一步到位）            |

### 详细对比

#### 1. 步骤 1：创建项目

**Idea 类型**：

```json
{
  "creation_type": "idea",
  "idea_prompt": "人工智能的发展历程与应用前景"
}
```

**Descriptions 类型**：

```json
{
  "creation_type": "descriptions",
  "description_text": "幻灯片 1：封面\n// NARRATIVE GOAL\n...\n\n// KEY CONTENT\n...\n\n// VISUAL\n...\n\n// LAYOUT\n..."
}
```

#### 2. 步骤 2：生成大纲

**Idea 类型**：

- **端点**：`POST /api/projects/{project_id}/generate/outline`
- **处理**：调用 `ai_service.generate_outline()` 从主题生成大纲
- **提示词**：`get_outline_generation_prompt()` - 要求 AI 生成大纲和风格指令
- **输出**：大纲结构（JSON），创建 Page 记录（只有 outline_content）

**Descriptions 类型**：

- **端点**：`POST /api/projects/{project_id}/generate/from-description`
- **处理**：
  1. 调用 `ai_service.parse_description_to_outline()` 从描述解析大纲
  2. 调用 `ai_service.parse_description_to_page_descriptions()` 切分或格式化描述
- **提示词**：
  - `get_description_to_outline_prompt()` - 要求 AI 从描述文本提取大纲
  - `get_description_format_prompt()` - 如果描述不符合格式，要求 AI 生成符合格式的描述
- **输出**：大纲结构（JSON）+ 页面描述列表，创建 Page 记录（同时包含 outline_content 和 description_content）

#### 3. 步骤 3：生成页面描述

**Idea 类型**：

- **端点**：`POST /api/projects/{project_id}/generate/descriptions`
- **处理**：并行生成每页描述
- **提示词**：`get_page_description_prompt()` - 要求 AI 根据大纲生成详细描述
- **输出**：更新 Page.description_content

**Descriptions 类型**：

- **通常跳过**：因为步骤 2 已经生成了描述
- **如果调用**：可能会重新生成或跳过（取决于实现）

#### 4. 步骤 4：生成页面图片

**完全相同**：两种类型都使用相同的端点和处理逻辑。

---

## 数据流转图

```
┌─────────────────────────────────────────────────────────────────┐
│                        步骤 1：创建项目                          │
└─────────────────────────────────────────────────────────────────┘
输入: {
  "creation_type": "descriptions",
  "description_text": "幻灯片 1：封面\n// NARRATIVE GOAL\n..."
}
    │
    ├─→ 验证请求数据
    ├─→ 创建 Project 记录
    └─→ 保存到数据库
    │
输出: {"project_id": "...", "status": "DRAFT"}

┌─────────────────────────────────────────────────────────────────┐
│              步骤 2：从描述生成大纲和页面描述                     │
│              (特殊端点: /generate/from-description)              │
└─────────────────────────────────────────────────────────────────┘
输入: {
  "description_text": "幻灯片 1：封面\n...",  // 可选
  "language": "zh"
}
    │
    ├─→ 构建 ProjectContext
    │
    ├─→ 步骤 2.1：解析描述文本到大纲结构
    │   ├─→ Prompt: get_description_to_outline_prompt()
    │   ├─→ AI 响应: {"style_instructions": {...}, "outline": [...]}
    │   ├─→ 解析响应
    │   └─→ 保存风格指令到 project.template_style
    │
    ├─→ 步骤 2.2：切分描述文本到每页描述
    │   ├─→ 检测描述格式
    │   │   ├─→ 如果符合格式：直接切分
    │   │   └─→ 如果不符合格式：AI 生成符合格式的描述
    │   │       ├─→ Prompt: get_description_format_prompt()
    │   │       └─→ AI 响应: ["幻灯片 1：...", "幻灯片 2：...", ...]
    │   └─→ 返回页面描述列表
    │
    ├─→ 扁平化大纲结构
    ├─→ 删除旧页面
    └─→ 创建 Page 记录（同时包含 outline_content 和 description_content）
    │
输出: {
  "pages": [
    {
      "outline_content": {...},
      "description_content": {"text": "幻灯片 1：...", ...},
      "status": "DESCRIPTION_GENERATED"
    },
    ...
  ],
  "status": "DESCRIPTIONS_GENERATED"
}
数据库: projects.status = "DESCRIPTIONS_GENERATED", 
       pages 表有 6 条记录（已包含大纲和描述）

┌─────────────────────────────────────────────────────────────────┐
│                      步骤 3：生成页面描述                         │
│                      (通常跳过，已在步骤 2 完成)                  │
└─────────────────────────────────────────────────────────────────┘
跳过（对于 descriptions 类型）

┌─────────────────────────────────────────────────────────────────┐
│                       步骤 4：生成页面图片                        │
│                      (与 idea 类型完全相同)                      │
└─────────────────────────────────────────────────────────────────┘
输入: {
  "max_workers": 8,
  "use_template": true,
  "language": "zh"
}
    │
    ├─→ 创建异步任务 (Task)
    ├─→ 提交后台任务 (generate_images_task)
    │   │
    │   └─→ 并行处理（ThreadPoolExecutor, max_workers=8）
    │       │
    │       ├─→ 页面 1: generate_single_image()
    │       │   ├─→ 获取页面描述（从 page.description_content）
    │       │   ├─→ 提取图片 URL（从 Markdown）
    │       │   ├─→ 获取模板图片路径
    │       │   ├─→ 生成图片提示词: get_image_generation_prompt()
    │       │   ├─→ 调用 AI 生成图片: ai_service.generate_image()
    │       │   └─→ 保存图片: save_image_with_version()
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

### 1. 描述解析到大纲提示词

**位置**：`prompts.py::get_description_to_outline_prompt()`

**核心内容**：

- 角色设定：世界级演示文稿设计师和故事讲述者
- 任务：从描述文本中提取大纲结构，生成全局风格指令
- 输出格式：JSON，包含 `style_instructions` 和 `outline`
- 重要规则：从描述文本中提取大纲结构，识别每页的标题和要点

### 2. 描述格式化提示词

**位置**：`prompts.py::get_description_format_prompt()`

**核心内容**：

- 角色设定：架构师（The Architect）
- 任务：将非格式化描述转换为符合格式的每页描述
- 输出格式：JSON 数组，每个元素包含四个部分（NARRATIVE GOAL, KEY CONTENT, VISUAL, LAYOUT）
- 重要规则：封面页切勿包含占位符，充分发挥视觉隐喻

### 3. 图片生成提示词

**位置**：`prompts.py::get_image_generation_prompt()`

**核心内容**：

- 与 idea 类型完全相同
- 从页面描述中提取关键内容、视觉和布局要求
- 应用风格指令生成图片

---

## 总结

Descriptions 类型的工作流程相比 Idea 类型更加**高效**和**灵活**：

1. **一步到位**：在步骤 2 中同时生成大纲和页面描述，减少了 API 调用次数
2. **用户控制**：用户可以直接提供详细的页面描述，包括视觉和布局要求
3. **格式灵活**：支持格式化描述（直接切分）和非格式化描述（AI 格式化）
4. **智能解析**：系统会自动检测描述格式，选择最合适的处理方式

整个流程从用户输入描述文本到生成完整 PPT，涉及 3 个主要步骤（步骤 3 通常跳过），每个步骤都有明确的输入、处理和输出，便于理解和维护。

---

**文档版本**：v1.0.0
**最后更新**：2024年1月

