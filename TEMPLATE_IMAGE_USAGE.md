# 模板图片使用流程与风格描述关系

本文档详细说明用户提供模板图片后，模板在整个工作流程中的使用方式，以及模板图片与风格描述的关系。

---

## 📋 目录

1. [模板图片的存储](#1-模板图片的存储)
2. [模板图片在流程中的使用](#2-模板图片在流程中的使用)
3. [模板图片与风格描述的关系](#3-模板图片与风格描述的关系)
4. [各阶段的具体处理逻辑](#4-各阶段的具体处理逻辑)
5. [优先级规则](#5-优先级规则)

---

## 1. 模板图片的存储

### 存储位置

- **数据库字段**：`Project.template_image_path`（相对路径）
- **文件系统**：保存在项目的 `template/` 目录下
- **上传接口**：`POST /api/projects/{project_id}/template`

### 代码位置

```404:406:banana-slides/backend/controllers/project_controller.py
        # 保存风格指令到项目（如果没有模板图片）
        if style_instructions and not project.template_image_path:
            import json
```

```49:49:banana-slides/backend/controllers/template_controller.py
        project.template_image_path = file_path
```

---

## 2. 模板图片在流程中的使用

### 2.1 大纲生成阶段

**位置**：`project_controller.py::generate_outline()`

**逻辑**：
- AI 生成大纲时，**同时生成风格指令**（`style_instructions`）
- **关键判断**：如果项目**没有模板图片**，才保存风格指令到 `project.template_style`
- 如果**有模板图片**，风格指令**不会被保存**

```404:406:banana-slides/backend/controllers/project_controller.py
        # 保存风格指令到项目（如果没有模板图片）
        if style_instructions and not project.template_image_path:
            import json
            project.template_style = json.dumps(style_instructions, ensure_ascii=False)
```

**说明**：
- 即使有模板图片，AI 仍然会生成风格指令（用于页面描述生成）
- 但风格指令不会保存到数据库，因为后续图片生成会直接使用模板图片

---

### 2.2 页面描述生成阶段

**位置**：`project_controller.py::generate_descriptions()`

**逻辑**：
- 从 `project.template_style` 读取风格指令（如果有）
- 风格指令会传递给 `generate_descriptions_task`
- 在生成页面描述时，风格指令会被包含在 prompt 中

```634:640:banana-slides/backend/controllers/project_controller.py
        # 获取风格指令（如果有）
        style_instructions = None
        if project.template_style:
            try:
                style_instructions = json.loads(project.template_style)
            except (json.JSONDecodeError, TypeError):
                pass
```

**说明**：
- 页面描述生成**不受模板图片影响**
- 即使有模板图片，如果之前保存了风格指令，仍然会在描述生成时使用

---

### 2.3 图片生成阶段

**位置**：`project_controller.py::generate_images()` 和 `prompts.py::get_image_generation_prompt()`

**逻辑**：
- 根据 `use_template` 参数决定是否使用模板图片
- 如果 `use_template=True` 且项目有模板图片：
  - 模板图片作为**参考图片**传递给图片生成模型
  - 设计指南改为：**"配色和设计语言和模板图片严格相似"**
  - **风格描述不会被包含在 prompt 中**

```552:570:banana-slides/backend/services/task_manager.py
            ref_image_path = None
            if use_template:
                ref_image_path = file_service.get_template_path(project_id)
                # 注意：如果有风格描述，即使没有模板图片也允许生成
                # 这个检查已经在 controller 层完成，这里不再检查
            
            # Generate image prompt
            page_data = page.get_outline_content() or {}
            if page.part:
                page_data['part'] = page.part
            
            prompt = ai_service.generate_image_prompt(
                outline, page_data, desc_text, page.order_index + 1,
                has_material_images=has_material_images,
                extra_requirements=extra_requirements,
                language=language,
                has_template=use_template,
                style_instructions=style_instructions,
                total_pages=total_pages
            )
```

**关键代码**：

```548:565:banana-slides/backend/services/prompts.py
    # 根据是否有模板生成不同的设计指南内容
    template_style_guideline = "- 配色和设计语言和模板图片严格相似。" if has_template else "- 严格按照风格描述进行设计。"
    forbidden_template_text_guidline = "- 只参考风格设计，禁止出现模板中的文字。\n" if has_template else ""
    
    # 格式化风格指令
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

**说明**：
- **如果有模板图片**（`has_template=True`）：
  - 风格描述**不会被包含**在 prompt 中（`if style_instructions and not has_template`）
  - 设计指南强调"配色和设计语言和模板图片严格相似"
  - 模板图片作为参考图片传递给图片生成模型
  
- **如果没有模板图片**（`has_template=False`）：
  - 风格描述**会被包含**在 prompt 中
  - 设计指南强调"严格按照风格描述进行设计"

---

### 2.4 图片编辑阶段

**位置**：`page_controller.py::edit_page_image()`

**逻辑**：
- 用户可以选择是否使用模板图片（通过 `use_template` 参数）
- 如果选择使用，模板图片会作为参考图片传递

```687:697:banana-slides/backend/controllers/page_controller.py
        # 1. Add template image if requested
        context_images = data.get('context_images', {})
        if isinstance(context_images, dict):
            use_template = context_images.get('use_template', False)
        else:
            use_template = data.get('use_template', 'false').lower() == 'true'
        
        if use_template:
            template_path = file_service.get_template_path(project_id)
            if template_path:
                additional_ref_images.append(template_path)
```

---

## 3. 模板图片与风格描述的关系

### 3.1 互斥关系

**核心规则**：模板图片和风格描述在图片生成时是**互斥**的。

| 场景 | 模板图片 | 风格描述 | 使用方式 |
|------|---------|---------|---------|
| **场景1** | ✅ 有 | ❌ 不使用 | 使用模板图片作为参考，风格描述不包含在 prompt 中 |
| **场景2** | ❌ 无 | ✅ 使用 | 使用风格描述，包含在 prompt 中 |
| **场景3** | ✅ 有 | ✅ 有但忽略 | 优先使用模板图片，风格描述被忽略 |

---

### 3.2 优先级规则

**优先级**：**模板图片 > 风格描述**

1. **如果有模板图片**：
   - 图片生成时**优先使用模板图片**
   - 风格描述**不会被包含**在图片生成 prompt 中
   - 设计指南强调"配色和设计语言和模板图片严格相似"

2. **如果没有模板图片**：
   - 使用风格描述
   - 风格描述**会被包含**在图片生成 prompt 中
   - 设计指南强调"严格按照风格描述进行设计"

---

### 3.3 风格描述的保存规则

**关键代码**：

```404:406:banana-slides/backend/controllers/project_controller.py
        # 保存风格指令到项目（如果没有模板图片）
        if style_instructions and not project.template_image_path:
            import json
            project.template_style = json.dumps(style_instructions, ensure_ascii=False)
```

**规则**：
- **只有在没有模板图片时**，才会保存风格指令到 `project.template_style`
- 如果有模板图片，即使 AI 生成了风格指令，也不会保存
- 这样确保后续图片生成时，不会出现模板图片和风格描述同时存在的情况

---

## 4. 各阶段的具体处理逻辑

### 阶段1：项目创建/模板上传

**操作**：用户上传模板图片

**结果**：
- `project.template_image_path` 被设置
- 如果之前有风格描述，**不会被删除**（保留在数据库中）

---

### 阶段2：大纲生成

**操作**：生成 PPT 大纲

**处理**：
1. AI 生成大纲和风格指令
2. **检查是否有模板图片**：
   - ✅ **有模板图片**：风格指令**不保存**到数据库
   - ❌ **无模板图片**：风格指令**保存**到 `project.template_style`

**代码**：

```404:406:banana-slides/backend/controllers/project_controller.py
        # 保存风格指令到项目（如果没有模板图片）
        if style_instructions and not project.template_image_path:
            import json
            project.template_style = json.dumps(style_instructions, ensure_ascii=False)
```

---

### 阶段3：页面描述生成

**操作**：生成页面描述

**处理**：
1. 从 `project.template_style` 读取风格指令（如果有）
2. 风格指令传递给 `generate_descriptions_task`
3. 在生成页面描述时，风格指令会被包含在 prompt 中

**说明**：
- 页面描述生成**不受模板图片影响**
- 即使有模板图片，如果之前保存了风格指令，仍然会在描述生成时使用
- 这是因为页面描述是文字描述，不涉及图片生成

---

### 阶段4：图片生成

**操作**：生成 PPT 页面图片

**处理**：

#### 4.1 准备阶段（`project_controller.py::generate_images()`）

```738:748:banana-slides/backend/controllers/project_controller.py
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
                combined_requirements = combined_requirements + style_requirements
```

**说明**：
- 尝试从 `project.template_style` 解析风格指令
- 如果解析失败（不是 JSON 格式），则作为纯文本追加到 `extra_requirements`

#### 4.2 Prompt 生成阶段（`prompts.py::get_image_generation_prompt()`）

**关键判断**：

```548:565:banana-slides/backend/services/prompts.py
    # 根据是否有模板生成不同的设计指南内容
    template_style_guideline = "- 配色和设计语言和模板图片严格相似。" if has_template else "- 严格按照风格描述进行设计。"
    forbidden_template_text_guidline = "- 只参考风格设计，禁止出现模板中的文字。\n" if has_template else ""
    
    # 格式化风格指令
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

**说明**：
- **如果有模板**（`has_template=True`）：
  - `style_section` 为空（风格描述不包含在 prompt 中）
  - `template_style_guideline` = "配色和设计语言和模板图片严格相似"
  - `forbidden_template_text_guidline` = "只参考风格设计，禁止出现模板中的文字"
  
- **如果没有模板**（`has_template=False`）：
  - `style_section` 包含完整的风格描述
  - `template_style_guideline` = "严格按照风格描述进行设计"
  - `forbidden_template_text_guidline` = 空

#### 4.3 图片生成阶段（`ai_service.py::generate_image()`）

**处理**：

```552:577:banana-slides/backend/services/task_manager.py
            ref_image_path = None
            if use_template:
                ref_image_path = file_service.get_template_path(project_id)
                # 注意：如果有风格描述，即使没有模板图片也允许生成
                # 这个检查已经在 controller 层完成，这里不再检查
            
            # Generate image prompt
            page_data = page.get_outline_content() or {}
            if page.part:
                page_data['part'] = page.part
            
            prompt = ai_service.generate_image_prompt(
                outline, page_data, desc_text, page.order_index + 1,
                has_material_images=has_material_images,
                extra_requirements=extra_requirements,
                language=language,
                has_template=use_template,
                style_instructions=style_instructions,
                total_pages=total_pages
            )
            
            # Generate image
            logger.info(f"🎨 Generating image for page {page_id}...")
            image = ai_service.generate_image(
                prompt, ref_image_path, aspect_ratio, resolution,
                additional_ref_images=additional_ref_images if additional_ref_images else None
            )
```

**说明**：
- 如果 `use_template=True`，获取模板图片路径作为 `ref_image_path`
- 模板图片作为**参考图片**传递给图片生成模型
- 图片生成模型会参考模板图片的风格、配色、布局等

---

## 5. 优先级规则

### 5.1 完整流程图

```
用户上传模板图片
    ↓
project.template_image_path 被设置
    ↓
生成大纲
    ↓
AI 生成风格指令
    ↓
检查：是否有模板图片？
    ├─ 有 → 风格指令不保存到数据库
    └─ 无 → 风格指令保存到 project.template_style
    ↓
生成页面描述
    ↓
使用风格指令（如果有）生成描述
    ↓
生成图片
    ↓
检查：use_template 参数？
    ├─ True + 有模板图片
    │   ├─ 模板图片作为参考图片
    │   ├─ 风格描述不包含在 prompt 中
    │   └─ 设计指南："配色和设计语言和模板图片严格相似"
    │
    └─ False 或 无模板图片
        ├─ 风格描述包含在 prompt 中
        └─ 设计指南："严格按照风格描述进行设计"
```

---

### 5.2 决策表

| 条件 | 模板图片存在 | use_template | 风格描述存在 | 结果 |
|------|------------|--------------|------------|------|
| **情况1** | ✅ | True | ✅/❌ | 使用模板图片，忽略风格描述 |
| **情况2** | ✅ | False | ✅ | 使用风格描述，不使用模板图片 |
| **情况3** | ❌ | True/False | ✅ | 使用风格描述 |
| **情况4** | ❌ | True/False | ❌ | 使用默认风格（架构师核心指令） |

---

### 5.3 关键代码位置总结

| 阶段 | 文件 | 函数 | 关键逻辑 |
|------|------|------|---------|
| **大纲生成** | `project_controller.py` | `generate_outline()` | 第404-406行：只有无模板时才保存风格指令 |
| **描述生成** | `project_controller.py` | `generate_descriptions()` | 第634-640行：读取风格指令（如果有） |
| **图片生成** | `project_controller.py` | `generate_images()` | 第738-748行：解析风格指令 |
| **Prompt生成** | `prompts.py` | `get_image_generation_prompt()` | 第548-565行：根据是否有模板决定是否包含风格描述 |
| **图片生成** | `task_manager.py` | `generate_images_task()` | 第552-570行：获取模板路径并传递 |

---

## 6. 实际使用示例

### 示例1：有模板图片的情况

**流程**：
1. 用户上传模板图片 → `project.template_image_path` 被设置
2. 生成大纲 → AI 生成风格指令，但**不保存**（因为有模板）
3. 生成描述 → 如果有之前保存的风格指令，会使用（但通常没有）
4. 生成图片 → `use_template=True`：
   - 模板图片作为参考图片
   - 风格描述不包含在 prompt 中
   - 设计指南："配色和设计语言和模板图片严格相似"

**结果**：生成的图片风格与模板图片相似

---

### 示例2：无模板图片的情况

**流程**：
1. 用户不上传模板图片 → `project.template_image_path` 为 `None`
2. 生成大纲 → AI 生成风格指令，**保存**到 `project.template_style`
3. 生成描述 → 使用保存的风格指令
4. 生成图片 → `use_template=False`：
   - 风格描述包含在 prompt 中
   - 设计指南："严格按照风格描述进行设计"

**结果**：生成的图片风格遵循风格描述

---

### 示例3：有模板但用户选择不使用

**流程**：
1. 用户上传模板图片 → `project.template_image_path` 被设置
2. 生成大纲 → AI 生成风格指令，但**不保存**（因为有模板）
3. 生成描述 → 如果有之前保存的风格指令，会使用
4. 生成图片 → `use_template=False`：
   - 如果之前保存了风格指令，会使用
   - 如果没有风格指令，使用默认风格

**结果**：生成的图片不参考模板，使用风格描述或默认风格

---

## 7. 总结

### 核心规则

1. **模板图片优先级高于风格描述**
   - 如果有模板图片且 `use_template=True`，优先使用模板图片
   - 风格描述不会被包含在图片生成 prompt 中

2. **风格描述只在无模板时保存**
   - 大纲生成时，只有没有模板图片才保存风格指令
   - 确保后续图片生成时不会出现冲突

3. **页面描述生成不受模板影响**
   - 页面描述是文字描述，不涉及图片生成
   - 如果有风格指令，会在描述生成时使用

4. **用户可以选择是否使用模板**
   - 通过 `use_template` 参数控制
   - 即使有模板图片，用户也可以选择不使用

### 设计理念

- **模板图片**：提供**视觉参考**，让 AI 直接学习模板的风格、配色、布局
- **风格描述**：提供**文字指导**，让 AI 根据文字描述生成风格
- **互斥设计**：避免两种方式同时使用造成冲突，确保生成结果的一致性

---

**文档版本**：v1.0.0  
**最后更新**：2024年1月



