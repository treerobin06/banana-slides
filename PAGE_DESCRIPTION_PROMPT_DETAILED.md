# `get_page_description_prompt()` 详细解析文档

## 📋 概述

本文档详细说明 `prompts.py::get_page_description_prompt()` 函数如何生成页面描述提示词，明确区分哪些部分是**动态生成**的，哪些是**固定写死**的。

---

## 🔧 函数签名

```python
def get_page_description_prompt(
    project_context: 'ProjectContext',  # 项目上下文对象
    outline: list,                      # 完整大纲（从步骤2生成）
    page_outline: dict,                 # 当前页面的大纲
    page_index: int,                    # 页面编号（从1开始）
    part_info: str = "",                # 可选的章节信息
    language: str = None,               # 输出语言
    style_instructions: dict = None,    # 全局风格指令（从步骤2生成或用户提供）
    total_pages: int = None             # 总页数（用于识别最后一页）
) -> str:
```

---

## 📊 提示词生成流程

### 步骤 1：准备参考文件内容（动态生成）

```python
files_xml = _format_reference_files_xml(project_context.reference_files_content)
```

**来源**：`project_context.reference_files_content`（用户上传的参考文件）

**处理**：将参考文件内容格式化为 XML 结构

**示例输出**：
```xml
<uploaded_files>
  <file name="参考文档.pdf">
    <content>
    文档内容...
    </content>
  </file>
</uploaded_files>
```

**是否写死**：❌ **动态生成**（取决于用户是否上传参考文件）

---

### 步骤 2：提取原始输入（动态生成）

```python
if project_context.creation_type == 'idea' and project_context.idea_prompt:
    original_input = project_context.idea_prompt
elif project_context.creation_type == 'outline' and project_context.outline_text:
    original_input = f"用户提供的大纲：\n{project_context.outline_text}"
elif project_context.creation_type == 'descriptions' and project_context.description_text:
    original_input = f"用户提供的描述：\n{project_context.description_text}"
else:
    original_input = project_context.idea_prompt or ""
```

**来源**：根据项目类型从 `project_context` 中提取

- **idea 类型**：使用 `idea_prompt`（用户输入的主题）
- **outline 类型**：使用 `outline_text`（用户提供的大纲文本）
- **descriptions 类型**：使用 `description_text`（用户提供的描述文本）

**是否写死**：❌ **动态生成**（取决于项目类型和用户输入）

---

### 步骤 3：格式化风格指令（动态生成，条件性）

```python
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

**来源**：`style_instructions` 参数（从步骤 2 生成或用户提供）

**处理逻辑**：
- 如果 `style_instructions` 存在，动态格式化各个字段
- 如果某个字段不存在，使用默认值（如 `'专业简洁'`、`'#FFFFFF'` 等）

**默认值（写死的）**：
- `design_aesthetic`: `'专业简洁'`
- `background_color`: `'#FFFFFF'`
- `primary_font`: `'思源黑体'`
- `secondary_font`: `'思源宋体'`
- `primary_text_color`: `'#2F3542'`
- `accent_color`: `'#007AFF'`
- `visual_elements`: `'简洁线条和图形'`

**是否写死**：❌ **动态生成**（内容来自步骤 2，但格式模板是写死的）

---

### 步骤 4：判断页面类型（动态生成）

```python
is_cover_page = page_index == 1
is_closing_page = total_pages and page_index == total_pages

page_type_hint = ""
if is_cover_page:
    page_type_hint = """
**【封面页设计要求】**
- 这是PPT的封面页，应采用"海报式"布局
- 内容保持极简：只放标题和副标题，**切勿包含任何占位符（如"汇报人"、"日期"、"地点"等）**
- 视觉上要醒目，使用满版出血图像或强烈的排版
- 需要一下就能抓住观众的注意力
"""
elif is_closing_page:
    page_type_hint = """
**【封底页设计要求】**
- 这是PPT的封底页，需要有强有力的结尾
- 不要使用通用的"谢谢"或"有问题吗？"
- 应该是经过设计的结束语、有意义的引用或强有力的视觉总结
- 锚定整个叙事，给观众留下深刻印象
"""
```

**来源**：根据 `page_index` 和 `total_pages` 动态判断

**处理逻辑**：
- 第 1 页 → 封面页提示
- 最后一页 → 封底页提示
- 其他页面 → 空字符串

**提示内容**：✅ **写死的**（但根据页面类型条件性插入）

**是否写死**：⚠️ **混合**（判断逻辑是动态的，但提示文本是写死的）

---

### 步骤 5：构建主提示词模板（写死的部分）

#### 5.1 角色设定（写死）

```python
你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。
```

**是否写死**：✅ **完全写死**

---

#### 5.2 核心指令（写死）

```python
**核心指令 (CORE DIRECTIVES):**
1. 分析内容的结构、意图和关键要素
2. 将指令转化为干净、结构化的视觉隐喻（蓝图、展示图、原理图、建筑图纸风格）
3. 所有视觉输出必须严格保持 16:9 的长宽比
4. 以三联画（triptych）或基于网格的布局呈现信息，保持文本和视觉的平衡
5. 背景应有精细的底纹（如细如发丝的网格线、蓝图纹理、淡得几不可察的公式水印）
6. 使用半透明的几何体、矢量线条、流形曲面等精密工程元素
7. 图表采用极简的线图或热力图风格，避免装饰性插画
```

**是否写死**：✅ **完全写死**

---

#### 5.3 任务说明（写死）

```python
我们正在为PPT的每一页生成详细描述。这份描述将提供给设计师制作最终的演示文稿。
```

**是否写死**：✅ **完全写死**

---

#### 5.4 上下文部分（动态生成）

```python
<context>
用户的原始需求：{original_input}

完整大纲：
{outline}
{part_info}
</context>
```

**动态部分**：
- `{original_input}`：从步骤 2 提取
- `{outline}`：完整大纲（从参数传入）
- `{part_info}`：章节信息（从参数传入）

**是否写死**：❌ **动态生成**

---

#### 5.5 风格指令部分（动态生成，条件性）

```python
{style_section}
```

**来源**：步骤 3 生成的 `style_section`

**是否写死**：❌ **动态生成**（如果 `style_instructions` 存在）

---

#### 5.6 当前页面信息（动态生成）

```python
现在请为第 {page_index} 页生成描述：
{page_outline}
{page_type_hint}
```

**动态部分**：
- `{page_index}`：页面编号
- `{page_outline}`：当前页面的大纲（从参数传入）
- `{page_type_hint}`：页面类型提示（从步骤 4 生成）

**是否写死**：❌ **动态生成**

---

#### 5.7 输出格式说明（写死）

```python
**请严格按照以下格式输出（详细描述，充分展现视觉隐喻）：**

幻灯片 {page_index}：{"封面 (The Cover)" if is_cover_page else ("封底 (The Closing)" if is_closing_page else page_outline.get('title', '内容页'))}

// NARRATIVE GOAL (叙事目标)
详细解释这张幻灯片在整个故事弧光中的具体叙事目的。这不仅是技术的介绍，更是一场关于主题的哲学宣示。描述它如何打破观众的固有认知，如何推动整体叙事，为后续内容奠定什么样的基调。

// KEY CONTENT (关键内容)

主标题：[使用叙事性的主题句，富有张力和深度]
{"副标题：[简洁有力的副标题，补充主标题的维度]" if is_cover_page else ""}
{"核心议题：[本页核心探讨的问题]" if not is_cover_page else ""}

页面文字：
- [要点1：简洁精炼，15-25字]
- [要点2...]
- [要点3...]

{"视觉标注：[SOURCE: X] 基于XXX的分析框架" if not is_cover_page else ""}
```

**动态部分**：
- `{page_index}`：页面编号
- 封面/封底/普通页的判断逻辑

**写死部分**：
- 格式说明文本
- 各部分的描述要求

**是否写死**：⚠️ **混合**（格式模板是写死的，但页面编号和类型判断是动态的）

---

#### 5.8 VISUAL 部分说明（写死）

```python
// VISUAL (视觉画面)
用连续的段落详细描述视觉元素，使用建筑图纸/蓝图风格的视觉隐喻。参考示例：

"海报式布局。背景是深邃的网格。画面中央是一个巨大的、半透明的立方体（代表信息总量），它正在通过一个光栅（代表Tokenizer）。光栅左侧是汉字"道"，右侧是英文单词"Logos"。汉字穿过光栅后变成了少量、致密的发光晶体；英文穿过光栅后变成了大量、松散的碎片。这种视觉隐喻直观地展示了"密度"与"切分"的关系。"

你的描述应包含：
- 核心视觉元素（如动态粒子系统、半透明几何体、流形曲面、信息流图、数据切片、光栅、晶体等）
- 背景底纹（如深邃的网格、蓝图纹理、淡如水印的公式等）
- 视觉隐喻（画面如何象征内容的核心概念）
- 动态感（元素的流动、透明度变化、延伸方式等）

**不要写具体的颜色十六进制代码，用描述性语言代替（如"深邃的背景"、"高亮的强调色"）。**
```

**是否写死**：✅ **完全写死**（包括示例文本）

---

#### 5.9 LAYOUT 部分说明（写死）

```python
// LAYOUT (布局结构)
用连续的段落描述页面构图和空间安排。参考示例：

"标题使用超大号字体居左下对齐，占据视觉重心的40%。右侧是核心视觉隐喻。顶部有一行极小的代码样式的元数据（时间、地点、研究代号）。"

你的描述应包含：
- 构图模式（非对称动态平衡、满版出血、三联画布局等）
- 标题排版（位置、相对大小、排版风格）
- 视觉重心（核心视觉元素占据的位置和比例）
- 留白策略（哪些区域保留纯净空间）
```

**是否写死**：✅ **完全写死**（包括示例文本）

---

#### 5.10 重要规则（写死）

```python
**重要规则：**
- **封面页切勿包含任何占位符**：不要包含"汇报人"、"日期"、"地点"、"姓名"等占位符信息。封面页只包含标题和副标题。
- 充分发挥视觉隐喻，将抽象概念转化为可视化的建筑图纸/蓝图风格
- 不要写具体的颜色代码（如#FF5722），用描述性语言（如"高亮强调色"、"深邃背景色"）
- "页面文字"部分会直接渲染到PPT上，必须简洁精炼
- 避免使用"标题：副标题"的格式；使用叙事性的主题句
- 避免AI废话模式，切勿使用"不仅仅是[X]，而是[Y]"等套话
- 使用直接、自信、主动的人类语言
- 永远假设听众比你想象的更专业、更感兴趣、更聪明
- 如果参考文件中包含 /files/ 开头的图片URL，请以markdown格式输出
```

**是否写死**：✅ **完全写死**

---

#### 5.11 语言指令（动态生成）

```python
{get_language_instruction(language)}
```

**来源**：根据 `language` 参数动态生成

**处理**：调用 `get_language_instruction()` 函数，根据语言代码返回对应的指令

**示例**：
- `language='zh'` → `"请使用全中文输出。"`
- `language='en'` → `"Please output all in English."`
- `language='ja'` → `"すべて日本語で出力してください。"`
- `language='auto'` → `""`（空字符串）

**是否写死**：❌ **动态生成**（但语言映射表是写死的）

---

### 步骤 6：组合最终提示词

```python
final_prompt = files_xml + prompt
```

**处理**：将参考文件 XML 和主提示词组合

**是否写死**：❌ **动态组合**

---

## 📋 完整提示词结构总结

```
┌─────────────────────────────────────────────────────────┐
│ 1. 参考文件 XML（动态）                                   │
│    <uploaded_files>...</uploaded_files>                  │
└─────────────────────────────────────────────────────────┘
                         +
┌─────────────────────────────────────────────────────────┐
│ 2. 角色设定（写死）                                       │
│    你是架构师（The Architect）...                        │
├─────────────────────────────────────────────────────────┤
│ 3. 核心指令（写死）                                       │
│    **核心指令 (CORE DIRECTIVES):**                      │
│    1. 分析内容的结构、意图和关键要素                     │
│    2. ...                                                │
├─────────────────────────────────────────────────────────┤
│ 4. 任务说明（写死）                                       │
│    我们正在为PPT的每一页生成详细描述...                  │
├─────────────────────────────────────────────────────────┤
│ 5. 上下文（动态）                                         │
│    <context>                                             │
│    用户的原始需求：{original_input}                      │
│    完整大纲：{outline}                                   │
│    {part_info}                                          │
│    </context>                                            │
├─────────────────────────────────────────────────────────┤
│ 6. 风格指令（动态，条件性）                               │
│    {style_section}                                      │
│    （如果 style_instructions 存在）                      │
├─────────────────────────────────────────────────────────┤
│ 7. 当前页面信息（动态）                                   │
│    现在请为第 {page_index} 页生成描述：                  │
│    {page_outline}                                       │
│    {page_type_hint}                                     │
├─────────────────────────────────────────────────────────┤
│ 8. 输出格式说明（混合）                                   │
│    **请严格按照以下格式输出...**                        │
│    幻灯片 {page_index}：...                             │
│    // NARRATIVE GOAL ...                                │
│    // KEY CONTENT ...                                   │
│    // VISUAL ...                                        │
│    // LAYOUT ...                                        │
├─────────────────────────────────────────────────────────┤
│ 9. VISUAL 部分说明（写死）                                │
│    // VISUAL (视觉画面)                                 │
│    用连续的段落详细描述视觉元素...                       │
│    参考示例：...                                         │
├─────────────────────────────────────────────────────────┤
│ 10. LAYOUT 部分说明（写死）                              │
│     // LAYOUT (布局结构)                                │
│     用连续的段落描述页面构图...                           │
│     参考示例：...                                        │
├─────────────────────────────────────────────────────────┤
│ 11. 重要规则（写死）                                      │
│     **重要规则：**                                       │
│     - 封面页切勿包含任何占位符...                        │
│     - 充分发挥视觉隐喻...                                │
│     - ...                                                │
├─────────────────────────────────────────────────────────┤
│ 12. 语言指令（动态）                                      │
│     {get_language_instruction(language)}                │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 动态 vs 写死 对比表

| 部分 | 是否写死 | 来源/说明 |
|------|---------|----------|
| **参考文件 XML** | ❌ 动态 | 从 `project_context.reference_files_content` 生成 |
| **角色设定** | ✅ 写死 | 固定文本："你是架构师（The Architect）..." |
| **核心指令** | ✅ 写死 | 7 条固定的核心指令 |
| **任务说明** | ✅ 写死 | 固定文本 |
| **原始需求** | ❌ 动态 | 从 `project_context` 根据项目类型提取 |
| **完整大纲** | ❌ 动态 | 从参数 `outline` 传入（步骤 2 生成） |
| **章节信息** | ❌ 动态 | 从参数 `part_info` 传入 |
| **风格指令** | ❌ 动态 | 从参数 `style_instructions` 传入（步骤 2 生成或用户提供） |
| **页面编号** | ❌ 动态 | 从参数 `page_index` 传入 |
| **当前页面大纲** | ❌ 动态 | 从参数 `page_outline` 传入 |
| **页面类型提示** | ⚠️ 混合 | 判断逻辑动态，提示文本写死 |
| **输出格式模板** | ✅ 写死 | 固定的格式说明 |
| **VISUAL 说明** | ✅ 写死 | 固定的说明和示例 |
| **LAYOUT 说明** | ✅ 写死 | 固定的说明和示例 |
| **重要规则** | ✅ 写死 | 9 条固定的规则 |
| **语言指令** | ❌ 动态 | 根据 `language` 参数生成 |

---

## 📝 关键参数来源追踪

### `style_instructions` 的来源

```
步骤 2：生成大纲
    ↓
AI 生成大纲和风格指令
    ↓
保存到 project.template_style（如果没有模板图片）
    ↓
步骤 3：生成页面描述
    ↓
从 project.template_style 解析为 style_instructions
    ↓
传递给 get_page_description_prompt()
```

### `outline` 的来源

```
步骤 2：生成大纲
    ↓
AI 生成大纲结构
    ↓
扁平化为页面列表
    ↓
保存到 Page 表
    ↓
步骤 3：生成页面描述
    ↓
从 Page 表重建 outline 结构
    ↓
传递给 get_page_description_prompt()
```

### `page_outline` 的来源

```
从完整的 outline 列表中提取当前页面的数据
    ↓
传递给 get_page_description_prompt()
```

---

## 🔍 代码调用链

```
project_controller.py::generate_descriptions()
    ↓
task_manager.py::generate_descriptions_task()
    ↓
ai_service.py::generate_page_description()
    ↓
prompts.py::get_page_description_prompt()  ← 本文档解析的函数
```

---

## 💡 设计要点

1. **模板化设计**：提示词采用模板化设计，固定部分提供结构和指导，动态部分提供具体内容
2. **条件性插入**：风格指令和页面类型提示采用条件性插入，只在需要时添加
3. **默认值处理**：风格指令的各个字段都有默认值，确保即使缺少某些字段也能正常工作
4. **类型判断**：根据页面编号和总页数动态判断页面类型（封面/封底/普通），提供针对性的提示

---

**文档版本**：v1.0.0  
**最后更新**：2024年1月



