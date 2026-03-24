# `get_image_generation_prompt()` 详细解析文档

## 📋 概述

本文档详细说明 `prompts.py::get_image_generation_prompt()` 函数如何生成图片生成提示词，明确区分哪些部分是**动态生成**的，哪些是**固定写死**的，以及**最开始是否给定风格描述的影响**。

---

## 🔧 函数签名

```python
def get_image_generation_prompt(
    page_desc: str,                    # 页面描述文本（从步骤3生成）
    outline_text: str,                 # 大纲文本
    current_section: str,               # 当前章节
    has_material_images: bool = False, # 是否有素材图片
    extra_requirements: str = None,     # 额外的要求（可能包含风格描述）
    language: str = None,               # 输出语言
    has_template: bool = True,          # 是否有模板图片
    page_index: int = 1,               # 页面编号（从1开始）
    style_instructions: dict = None,    # 全局风格指令（从步骤2生成或用户提供）
    total_pages: int = None            # 总页数（用于识别最后一页）
) -> str:
```

---

## 📊 提示词生成流程

### 步骤 1：解析页面描述（动态生成）

```python
parsed_desc = _parse_page_description(page_desc)
key_content = parsed_desc.get('key_content', page_desc)
visual_desc = parsed_desc.get('visual', '')
layout_desc = parsed_desc.get('layout', '')
narrative_goal = parsed_desc.get('narrative_goal', '')
```

**来源**：`page_desc` 参数（从步骤 3 生成的页面描述）

**处理**：解析页面描述文本，提取 4 个部分：
- `narrative_goal`：叙事目标
- `key_content`：关键内容（标题、副标题、要点）
- `visual_desc`：视觉画面描述
- `layout_desc`：布局结构描述

**是否写死**：❌ **动态生成**（从页面描述中解析）

---

### 步骤 2：处理素材图片提示（动态生成，条件性）

```python
material_images_note = ""
if has_material_images:
    material_images_note = (
        "\n\n提示：" + ("除了模板参考图片（用于风格参考）外，还提供了额外的素材图片。" if has_template else "用户提供了额外的素材图片。") +
        "这些素材图片是可供挑选和使用的元素，你可以从这些素材图片中选择合适的图片、图标、图表或其他视觉元素"
        "直接整合到生成的PPT页面中。请根据页面内容的需要，智能地选择和组合这些素材图片中的元素。"
    )
```

**来源**：`has_material_images` 参数（从页面描述中提取的图片 URL）

**处理逻辑**：
- 如果有素材图片，生成提示文本
- 根据是否有模板图片，生成不同的提示文本

**提示文本**：✅ **写死的**（但根据条件动态插入）

**是否写死**：⚠️ **混合**（判断逻辑是动态的，但提示文本是写死的）

---

### 步骤 3：处理额外要求（动态生成，条件性）

```python
extra_req_text = ""
if extra_requirements and extra_requirements.strip():
    extra_req_text = f"\n\n额外要求（请务必遵循）：\n{extra_requirements}\n"
```

**来源**：`extra_requirements` 参数

**处理逻辑**：
- 如果 `extra_requirements` 存在且不为空，格式化后追加到提示词

**重要**：`extra_requirements` 可能包含：
- 用户提供的 `extra_requirements`
- 如果 `template_style` 不是 JSON 格式，会被追加到这里（见 `project_controller.py::generate_images()`）

**是否写死**：❌ **动态生成**（内容来自用户或项目配置）

---

### 步骤 4：生成设计指南（动态生成，条件性）

```python
template_style_guideline = "- 配色和设计语言和模板图片严格相似。" if has_template else "- 严格按照风格描述进行设计。"
forbidden_template_text_guidline = "- 只参考风格设计，禁止出现模板中的文字。\n" if has_template else ""
```

**来源**：根据 `has_template` 参数动态生成

**处理逻辑**：
- **有模板图片**：`"- 配色和设计语言和模板图片严格相似。"`
- **无模板图片**：`"- 严格按照风格描述进行设计。"`

**是否写死**：⚠️ **混合**（判断逻辑是动态的，但提示文本是写死的）

---

### 步骤 5：格式化风格指令（动态生成，条件性）⭐

```python
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

**关键条件**：`if style_instructions and not has_template`

**含义**：
- ✅ **只有在无模板图模式时**，才会插入 `<style_instructions>` 标签
- ❌ **如果有模板图片**，即使有 `style_instructions`，也不会插入（模板图片是主要参考）

**来源**：`style_instructions` 参数（从步骤 2 生成或用户提供）

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

### 步骤 6：格式化视觉和布局指令（动态生成，条件性）

```python
visual_layout_section = ""
if visual_desc or layout_desc:
    visual_layout_section = "\n<visual_and_layout_instructions>"
    if visual_desc:
        visual_layout_section += f"\n【视觉画面要求】\n{visual_desc}"
    if layout_desc:
        visual_layout_section += f"\n\n【布局结构要求】\n{layout_desc}"
    visual_layout_section += "\n</visual_and_layout_instructions>\n"
```

**来源**：从步骤 1 解析的 `visual_desc` 和 `layout_desc`

**处理逻辑**：
- 如果 `visual_desc` 或 `layout_desc` 存在，格式化到 `<visual_and_layout_instructions>` 标签中

**是否写死**：❌ **动态生成**（内容来自页面描述）

---

### 步骤 7：判断页面类型（动态生成）

```python
is_cover_page = page_index == 1
is_closing_page = total_pages and page_index == total_pages

page_type_hint = ""
if is_cover_page:
    page_type_hint = '\n**注意：当前页面为PPT的封面页，请采用专业的封面设计美学技巧，务必凸显出页面标题，分清主次，确保一下就能抓住观众的注意力。可使用"海报式"布局、醒目的排版或满版出血图像。**\n'
elif is_closing_page:
    page_type_hint = '\n**注意：当前页面为PPT的封底页，需要有强有力的结尾。应该是经过设计的结束语、有意义的引用或强有力的视觉总结，锚定整个叙事。**\n'
```

**来源**：根据 `page_index` 和 `total_pages` 动态判断

**处理逻辑**：
- 第 1 页 → 封面页提示
- 最后一页 → 封底页提示
- 其他页面 → 空字符串

**提示内容**：✅ **写死的**（但根据页面类型条件性插入）

**是否写死**：⚠️ **混合**（判断逻辑是动态的，但提示文本是写死的）

---

### 步骤 8：构建主提示词模板（写死的部分）

#### 8.1 角色设定（写死）

```python
你是一位专家级UI UX演示设计师，专注于生成设计良好的PPT页面。
```

**是否写死**：✅ **完全写死**

---

#### 8.2 叙事目标（动态生成，条件性）

```python
{f"【叙事目标】{narrative_goal}" if narrative_goal else ""}
```

**来源**：从步骤 1 解析的 `narrative_goal`

**是否写死**：❌ **动态生成**（如果存在）

---

#### 8.3 页面内容（动态生成）

```python
当前PPT页面的内容如下:
<page_content>
{key_content}
</page_content>
```

**来源**：从步骤 1 解析的 `key_content`

**是否写死**：❌ **动态生成**

---

#### 8.4 风格指令和视觉布局指令（动态生成，条件性）

```python
{style_section}{visual_layout_section}
```

**来源**：
- `style_section`：从步骤 5 生成（仅在无模板图时）
- `visual_layout_section`：从步骤 6 生成（如果存在）

**是否写死**：❌ **动态生成**

---

#### 8.5 参考信息（动态生成）

```python
<reference_information>
整个PPT的大纲为：
{outline_text}

当前位于章节：{current_section}
</reference_information>
```

**来源**：
- `outline_text`：从参数传入（完整大纲）
- `current_section`：从参数传入（当前章节）

**是否写死**：❌ **动态生成**

---

#### 8.6 设计指南（混合）

```python
<design_guidelines>
- 要求文字清晰锐利, 画面为4K分辨率，16:9比例。
{template_style_guideline}
- 根据内容自动设计最完美的构图，不重不漏地渲染页面内容中的文本。
- 如非必要，禁止出现 markdown 格式符号（如 # 和 * 等）。
{forbidden_template_text_guidline}- 使用大小恰当的装饰性图形或插画对空缺位置进行填补。
- 如有视觉画面和布局结构要求，请严格遵循。
</design_guidelines>
```

**写死部分**：
- "要求文字清晰锐利, 画面为4K分辨率，16:9比例。"
- "根据内容自动设计最完美的构图，不重不漏地渲染页面内容中的文本。"
- "如非必要，禁止出现 markdown 格式符号（如 # 和 * 等）。"
- "使用大小恰当的装饰性图形或插画对空缺位置进行填补。"
- "如有视觉画面和布局结构要求，请严格遵循。"

**动态部分**：
- `{template_style_guideline}`：从步骤 4 生成
- `{forbidden_template_text_guidline}`：从步骤 4 生成

**是否写死**：⚠️ **混合**

---

#### 8.7 语言指令（动态生成）

```python
{get_ppt_language_instruction(language)}
```

**来源**：根据 `language` 参数动态生成

**是否写死**：❌ **动态生成**（但语言映射表是写死的）

---

#### 8.8 其他提示（动态生成，条件性）

```python
{material_images_note}{extra_req_text}{page_type_hint}
```

**来源**：
- `material_images_note`：从步骤 2 生成
- `extra_req_text`：从步骤 3 生成
- `page_type_hint`：从步骤 7 生成

**是否写死**：❌ **动态生成**（条件性插入）

---

## 📋 完整提示词结构总结

```
┌─────────────────────────────────────────────────────────┐
│ 1. 角色设定（写死）                                       │
│    你是一位专家级UI UX演示设计师...                      │
├─────────────────────────────────────────────────────────┤
│ 2. 叙事目标（动态，条件性）                               │
│    {【叙事目标】{narrative_goal}}                        │
│    （如果存在）                                           │
├─────────────────────────────────────────────────────────┤
│ 3. 页面内容（动态）                                       │
│    <page_content>                                       │
│    {key_content}                                        │
│    </page_content>                                      │
├─────────────────────────────────────────────────────────┤
│ 4. 风格指令（动态，条件性）                               │
│    {style_section}                                      │
│    （仅在无模板图时，如果 style_instructions 存在）      │
├─────────────────────────────────────────────────────────┤
│ 5. 视觉和布局指令（动态，条件性）                         │
│    {visual_layout_section}                              │
│    （如果 visual_desc 或 layout_desc 存在）              │
├─────────────────────────────────────────────────────────┤
│ 6. 参考信息（动态）                                       │
│    <reference_information>                              │
│    整个PPT的大纲为：{outline_text}                      │
│    当前位于章节：{current_section}                      │
│    </reference_information>                             │
├─────────────────────────────────────────────────────────┤
│ 7. 设计指南（混合）                                       │
│    <design_guidelines>                                  │
│    - 要求文字清晰锐利, 画面为4K分辨率，16:9比例。       │
│    {template_style_guideline}                           │
│    - 根据内容自动设计最完美的构图...                     │
│    - 如非必要，禁止出现 markdown 格式符号...             │
│    {forbidden_template_text_guidline}                    │
│    - 使用大小恰当的装饰性图形...                         │
│    - 如有视觉画面和布局结构要求，请严格遵循。            │
│    </design_guidelines>                                 │
├─────────────────────────────────────────────────────────┤
│ 8. 语言指令（动态）                                       │
│    {get_ppt_language_instruction(language)}             │
├─────────────────────────────────────────────────────────┤
│ 9. 素材图片提示（动态，条件性）                           │
│    {material_images_note}                               │
│    （如果有素材图片）                                    │
├─────────────────────────────────────────────────────────┤
│ 10. 额外要求（动态，条件性）                              │
│     {extra_req_text}                                    │
│     （如果 extra_requirements 存在）                     │
├─────────────────────────────────────────────────────────┤
│ 11. 页面类型提示（动态，条件性）                           │
│     {page_type_hint}                                    │
│     （如果是封面页或封底页）                              │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 动态 vs 写死 对比表

| 部分 | 是否写死 | 来源/说明 |
|------|---------|----------|
| **角色设定** | ✅ 写死 | 固定文本："你是一位专家级UI UX演示设计师..." |
| **叙事目标** | ❌ 动态 | 从页面描述中解析（如果存在） |
| **页面内容** | ❌ 动态 | 从页面描述中解析的 `key_content` |
| **风格指令** | ❌ 动态 | 从 `style_instructions` 参数传入（仅在无模板图时） |
| **视觉和布局指令** | ❌ 动态 | 从页面描述中解析的 `visual_desc` 和 `layout_desc` |
| **参考信息** | ❌ 动态 | 从参数传入的 `outline_text` 和 `current_section` |
| **设计指南** | ⚠️ 混合 | 部分写死，部分动态（根据是否有模板） |
| **语言指令** | ❌ 动态 | 根据 `language` 参数生成 |
| **素材图片提示** | ⚠️ 混合 | 判断逻辑动态，提示文本写死 |
| **额外要求** | ❌ 动态 | 从 `extra_requirements` 参数传入 |
| **页面类型提示** | ⚠️ 混合 | 判断逻辑动态，提示文本写死 |

---

## 🔍 风格描述的影响分析

### 场景 1：最开始就给定风格描述（用户手动输入）

**流程**：
```
步骤 1：创建项目
    ↓
用户提供 template_style（纯文本或 JSON）
    ↓
保存到 project.template_style
    ↓
步骤 2：生成大纲
    ↓
如果 template_style 已存在 → 不覆盖，继续使用用户提供的
    ↓
步骤 4：生成图片
    ↓
从 project.template_style 解析
    ├─→ 如果是 JSON：解析为 style_instructions
    └─→ 如果不是 JSON：追加到 extra_requirements
    ↓
传递给 get_image_generation_prompt()
```

**影响**：
- ✅ **JSON 格式**：会被解析为 `style_instructions`，在无模板图模式下插入 `<style_instructions>` 标签
- ✅ **纯文本格式**：会被追加到 `extra_requirements`，作为额外要求插入提示词

---

### 场景 2：AI 自动生成风格描述（步骤 2）

**流程**：
```
步骤 1：创建项目
    ↓
template_style = NULL
    ↓
步骤 2：生成大纲
    ↓
AI 生成大纲和风格指令
    ↓
保存到 project.template_style（如果没有模板图片）
    ↓
步骤 4：生成图片
    ↓
从 project.template_style 解析为 style_instructions
    ↓
传递给 get_image_generation_prompt()
```

**影响**：
- ✅ **JSON 格式**：会被解析为 `style_instructions`，在无模板图模式下插入 `<style_instructions>` 标签
- ✅ **自动根据主题生成**：风格指令会根据内容主题智能生成，符合项目需求

---

### 场景 3：有模板图片 vs 无模板图片

#### 情况 A：有模板图片（`has_template=True`）

**风格指令的处理**：
```python
# 即使 style_instructions 存在，也不会插入 <style_instructions> 标签
if style_instructions and not has_template:  # False，因为 has_template=True
    style_section = ...  # 不会执行
```

**设计指南**：
```python
template_style_guideline = "- 配色和设计语言和模板图片严格相似。"
forbidden_template_text_guidline = "- 只参考风格设计，禁止出现模板中的文字。\n"
```

**影响**：
- ❌ **风格指令不插入**：即使有 `style_instructions`，也不会插入到提示词中
- ✅ **模板图片是主要参考**：设计指南要求"配色和设计语言和模板图片严格相似"
- ⚠️ **风格指令可能通过 extra_requirements 传递**：如果 `template_style` 是纯文本格式，会被追加到 `extra_requirements`

---

#### 情况 B：无模板图片（`has_template=False`）

**风格指令的处理**：
```python
# 如果 style_instructions 存在，会插入 <style_instructions> 标签
if style_instructions and not has_template:  # True，因为 has_template=False
    style_section = f"""
    <style_instructions>
    设计美学：{style_instructions.get('design_aesthetic', '专业简洁')}
    背景色：{style_instructions.get('background_color', '#FFFFFF')}
    ...
    </style_instructions>
    """
```

**设计指南**：
```python
template_style_guideline = "- 严格按照风格描述进行设计。"
forbidden_template_text_guidline = ""  # 空字符串
```

**影响**：
- ✅ **风格指令是唯一设计指导**：会插入 `<style_instructions>` 标签
- ✅ **必须严格按照风格描述**：设计指南要求"严格按照风格描述进行设计"
- ✅ **如果没有风格指令**：只能依赖页面描述中的 VISUAL 和 LAYOUT 部分

---

### 场景 4：最开始是否给定风格描述的影响对比

| 场景 | 是否有风格描述 | 是否有模板图片 | 风格指令插入 | 设计指南 | 影响 |
|------|--------------|--------------|------------|---------|------|
| **场景 A** | ✅ 用户提供（JSON） | ❌ 无 | ✅ 插入 `<style_instructions>` | "严格按照风格描述进行设计" | 用户完全控制风格 |
| **场景 B** | ✅ 用户提供（JSON） | ✅ 有 | ❌ 不插入 | "配色和设计语言和模板图片严格相似" | 模板图片优先，风格指令无效 |
| **场景 C** | ✅ 用户提供（纯文本） | ❌ 无 | ❌ 不插入（但通过 extra_requirements） | "严格按照风格描述进行设计" | 通过额外要求传递 |
| **场景 D** | ✅ 用户提供（纯文本） | ✅ 有 | ❌ 不插入（但通过 extra_requirements） | "配色和设计语言和模板图片严格相似" | 模板图片优先，风格描述作为补充 |
| **场景 E** | ❌ 无（AI 生成） | ❌ 无 | ✅ 插入 `<style_instructions>` | "严格按照风格描述进行设计" | AI 自动生成风格，完全依赖风格指令 |
| **场景 F** | ❌ 无（AI 生成） | ✅ 有 | ❌ 不插入 | "配色和设计语言和模板图片严格相似" | 完全依赖模板图片 |

---

## 🔑 关键代码位置

### 风格指令的传递链

```
project_controller.py::generate_images()
    ↓
解析 project.template_style
    ├─→ 如果是 JSON：解析为 style_instructions
    └─→ 如果不是 JSON：追加到 extra_requirements
    ↓
task_manager.py::generate_images_task()
    ↓
ai_service.py::generate_image_prompt()
    ↓
prompts.py::get_image_generation_prompt()  ← 本文档解析的函数
    ↓
根据 has_template 决定是否插入 style_section
```

---

## 💡 设计要点

1. **模板图片优先级**：
   - 如果有模板图片，模板图片是主要参考
   - 风格指令不会插入到提示词中（即使存在）
   - 设计指南要求"配色和设计语言和模板图片严格相似"

2. **无模板图模式**：
   - 风格指令是唯一的设计指导
   - 必须严格按照风格描述进行设计
   - 如果没有风格指令，只能依赖页面描述

3. **格式兼容性**：
   - 支持 JSON 格式（结构化，精确应用）
   - 支持纯文本格式（通过 extra_requirements 传递）

4. **条件性插入**：
   - 风格指令只在无模板图时插入
   - 视觉和布局指令只在存在时插入
   - 素材图片提示只在有素材时插入

---

## 📝 最开始是否给定风格描述的影响总结

### ✅ 有影响的情况

1. **无模板图模式 + JSON 格式风格描述**：
   - ✅ 会插入 `<style_instructions>` 标签
   - ✅ 设计指南要求"严格按照风格描述进行设计"
   - ✅ 风格描述直接影响生成的图片

2. **有模板图模式 + 纯文本格式风格描述**：
   - ⚠️ 不会插入 `<style_instructions>` 标签
   - ⚠️ 但会通过 `extra_requirements` 传递
   - ⚠️ 作为补充说明，模板图片是主要参考

### ❌ 无影响的情况

1. **有模板图模式 + JSON 格式风格描述**：
   - ❌ 不会插入 `<style_instructions>` 标签
   - ❌ 风格指令被忽略
   - ❌ 完全依赖模板图片

2. **无模板图模式 + 无风格描述**：
   - ❌ 没有风格指令
   - ❌ 只能依赖页面描述中的 VISUAL 和 LAYOUT 部分
   - ⚠️ 生成结果可能不够统一

---

## 🎯 最佳实践建议

1. **无模板图模式**：
   - ✅ 建议在创建项目时提供风格描述（JSON 格式）
   - ✅ 或者让 AI 在步骤 2 自动生成风格指令
   - ✅ 确保风格描述足够详细，包含所有必要的设计元素

2. **有模板图模式**：
   - ⚠️ 风格描述作用有限（模板图片是主要参考）
   - ⚠️ 如果需要特定风格，建议使用纯文本格式追加到 `extra_requirements`
   - ✅ 模板图片应该已经包含所需的设计风格

3. **混合模式**：
   - ✅ 可以先上传模板图片，再通过 `extra_requirements` 提供额外的风格要求
   - ✅ 这样既能参考模板，又能补充特定的设计需求

---

**文档版本**：v1.0.0  
**最后更新**：2024年1月



