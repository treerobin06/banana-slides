# 图片重新生成与微调工作流

本文档详细说明重新生成图片和微调图片的工作流程，包括提示词、输入输出以及模板切换的影响。

---

## 📋 目录

1. [重新生成图片工作流](#1-重新生成图片工作流)
2. [微调图片工作流](#2-微调图片工作流)
3. [模板切换的影响](#3-模板切换的影响)

---

## 1. 重新生成图片工作流

### 1.1 API 接口

**接口**：`POST /api/projects/{project_id}/pages/{page_id}/generate/image`

**请求参数**（JSON）：
```json
{
  "use_template": true,        // 是否使用模板图片
  "force_regenerate": false,   // 是否强制重新生成（如果图片已存在）
  "language": "zh"             // 输出语言：zh, en, ja, auto
}
```

### 1.2 工作流程

#### 步骤 1：参数验证和准备

**输入**：
- `project_id`: 项目ID
- `page_id`: 页面ID
- `use_template`: 是否使用模板（默认 `true`）
- `force_regenerate`: 是否强制重新生成（默认 `false`）

**处理逻辑**：
```420:447:banana-slides/backend/controllers/page_controller.py
def generate_page_image(project_id, page_id):
    """
    POST /api/projects/{project_id}/pages/{page_id}/generate/image - Generate single page image
    
    Request body:
    {
        "use_template": true,
        "force_regenerate": false
    }
    """
    try:
        page = Page.query.get(page_id)
        
        if not page or page.project_id != project_id:
            return not_found('Page')
        
        project = Project.query.get(project_id)
        if not project:
            return not_found('Project')
        
        data = request.get_json() or {}
        use_template = data.get('use_template', True)
        force_regenerate = data.get('force_regenerate', False)
        language = data.get('language', current_app.config.get('OUTPUT_LANGUAGE', 'zh'))
        
        # Check if already generated
        if page.generated_image_path and not force_regenerate:
            return bad_request("Image already exists. Set force_regenerate=true to regenerate")
```

**验证**：
- 检查页面是否存在
- 检查项目是否存在
- 如果图片已存在且未设置 `force_regenerate`，返回错误

---

#### 步骤 2：获取页面描述和大纲

**输入**：
- 页面对象（`page`）
- 项目对象（`project`）

**处理逻辑**：
```449:500:banana-slides/backend/controllers/page_controller.py
        # Get description content
        desc_content = page.get_description_content()
        if not desc_content:
            return bad_request("Page must have description content first")
        
        # Reconstruct full outline with part structure
        all_pages = Page.query.filter_by(project_id=project_id).order_by(Page.order_index).all()
        outline = []
        current_part = None
        current_part_pages = []
        
        for p in all_pages:
            oc = p.get_outline_content()
            if not oc:
                continue
                
            page_data = oc.copy()
            
            # 如果当前页面属于一个 part
            if p.part:
                # 如果这是新的 part，先保存之前的 part（如果有）
                if current_part and current_part != p.part:
                    outline.append({
                        "part": current_part,
                        "pages": current_part_pages
                    })
                    current_part_pages = []
                
                current_part = p.part
                # 移除 part 字段，因为它在顶层
                if 'part' in page_data:
                    del page_data['part']
                current_part_pages.append(page_data)
            else:
                # 如果当前页面不属于任何 part，先保存之前的 part（如果有）
                if current_part:
                    outline.append({
                        "part": current_part,
                        "pages": current_part_pages
                    })
                    current_part = None
                    current_part_pages = []
                
                # 直接添加页面
                outline.append(page_data)
        
        # 保存最后一个 part（如果有）
        if current_part:
            outline.append({
                "part": current_part,
                "pages": current_part_pages
            })
```

**输出**：
- `desc_content`: 页面描述内容（字典格式）
- `outline`: 完整的大纲结构（包含 part 和 pages）

---

#### 步骤 3：解析风格指令和额外要求

**输入**：
- `project.template_style`: 风格描述（JSON 或纯文本）
- `project.extra_requirements`: 额外要求

**处理逻辑**：
```544:555:banana-slides/backend/controllers/page_controller.py
        # 解析风格指令和合并额外要求
        combined_requirements = project.extra_requirements or ""
        style_instructions = None
        if project.template_style:
            # 尝试解析为 JSON（新格式的风格指令）
            try:
                import json
                style_instructions = json.loads(project.template_style)
            except (json.JSONDecodeError, TypeError):
                # 如果不是 JSON，则作为纯文本风格描述追加到 extra_requirements
                style_requirement = f"\n\nppt页面风格描述：\n\n{project.template_style}"
                combined_requirements = combined_requirements + style_requirement
```

**输出**：
- `style_instructions`: 风格指令字典（如果 `template_style` 是 JSON 格式）
- `combined_requirements`: 合并后的额外要求（包含 `extra_requirements` 和纯文本风格描述）

---

#### 步骤 4：生成提示词

**输入**：
- `desc_text`: 页面描述文本
- `outline`: 完整大纲
- `page_data`: 当前页面的大纲数据
- `use_template`: 是否使用模板
- `style_instructions`: 风格指令
- `combined_requirements`: 额外要求
- `language`: 输出语言

**处理逻辑**：
```562:570:banana-slides/backend/services/task_manager.py
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

**提示词结构**（`get_image_generation_prompt()`）：

```587:626:banana-slides/backend/services/prompts.py
    prompt = (f"""\
你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。

**核心指令 (CORE DIRECTIVES):**

1. 分析用户提示词的结构、意图和关键要素。

2. 将指令转化为干净、结构化的视觉隐喻（蓝图、展示图、原理图）。

3. 使用特定的、克制的调色板和字体系列，以获得最大的清晰度和专业影响力。

4. 所有视觉输出必须严格保持 16:9 的长宽比。

5. 以三联画（triptych）或基于网格的布局呈现信息，保持文本和视觉的平衡。

{f"【叙事目标】{narrative_goal}" if narrative_goal else ""}

当前PPT页面的内容如下:
<page_content>
{key_content}
</page_content>
{style_section}{visual_layout_section}
<reference_information>
整个PPT的大纲为：
{outline_text}

当前位于章节：{current_section}
</reference_information>

<design_guidelines>
- 要求文字清晰锐利, 画面为4K分辨率，16:9比例。
{template_style_guideline}
- 根据内容自动设计最完美的构图，不重不漏地渲染页面内容中的文本。
- 如非必要，禁止出现 markdown 格式符号（如 # 和 * 等）。
{forbidden_template_text_guidline}- 使用大小恰当的装饰性图形或插画对空缺位置进行填补。
- 如有视觉画面和布局结构要求，请严格遵循。
</design_guidelines>
{get_ppt_language_instruction(language)}
{material_images_note}{extra_req_text}{page_type_hint}
""")
```

**提示词组成部分**：

1. **角色设定和核心指令**（写死）
2. **叙事目标**（从描述中提取，可选）
3. **页面内容**（`<page_content>`）：从描述中提取的关键内容
4. **风格指令**（`<style_instructions>`）：仅在 `has_template=False` 时包含
   - 设计美学
   - 背景色
   - 标题字体
   - 正文字体
   - 主要文字颜色
   - 强调色
   - 视觉元素风格
5. **视觉和布局指令**（`<visual_and_layout_instructions>`）：从描述中提取（可选）
6. **参考信息**（`<reference_information>`）：完整大纲和当前章节
7. **设计指南**（`<design_guidelines>`）：
   - 如果有模板：`"配色和设计语言和模板图片严格相似。"`
   - 如果没有模板：`"严格按照风格描述进行设计。"`
8. **额外要求**（`额外要求（请务必遵循）`）：`combined_requirements`
9. **页面类型提示**：封面页或封底页的特殊提示（可选）

---

#### 步骤 5：生成图片

**输入**：
- `prompt`: 生成的提示词
- `ref_image_path`: 模板图片路径（如果 `use_template=True`）
- `additional_ref_images`: 描述中的图片 URL 列表（可选）

**处理逻辑**：
```573:577:banana-slides/backend/services/task_manager.py
            # Generate image
            logger.info(f"🎨 Generating image for page {page_id}...")
            image = ai_service.generate_image(
                prompt, ref_image_path, aspect_ratio, resolution,
                additional_ref_images=additional_ref_images if additional_ref_images else None
            )
```

**输出**：
- `image`: PIL Image 对象

---

#### 步骤 6：保存图片和版本记录

**处理逻辑**：
```582:585:banana-slides/backend/services/task_manager.py
            # 保存图片并创建历史版本记录
            image_path, next_version = save_image_with_version(
                image, project_id, page_id, file_service, page_obj=page
            )
```

**输出**：
- `image_path`: 保存后的图片相对路径
- `next_version`: 新版本号

---

### 1.3 输入输出总结

| 阶段 | 输入 | 输出 |
|------|------|------|
| **参数验证** | `project_id`, `page_id`, `use_template`, `force_regenerate` | 验证通过 |
| **获取描述和大纲** | 页面对象、项目对象 | `desc_content`, `outline` |
| **解析风格指令** | `project.template_style`, `project.extra_requirements` | `style_instructions`, `combined_requirements` |
| **生成提示词** | 描述、大纲、风格指令、额外要求、模板标志 | `prompt` 字符串 |
| **生成图片** | `prompt`, `ref_image_path`, `additional_ref_images` | PIL Image 对象 |
| **保存图片** | PIL Image 对象 | `image_path`, `next_version` |

---

## 2. 微调图片工作流

### 2.1 API 接口

**接口**：`POST /api/projects/{project_id}/pages/{page_id}/edit/image`

**请求参数**（JSON 或 multipart/form-data）：

**JSON 格式**：
```json
{
  "edit_instruction": "更改文本框样式为虚线",
  "context_images": {
    "use_template": true,              // 是否使用模板图片作为参考
    "desc_image_urls": ["url1", "url2"] // 描述中的图片URL列表
  }
}
```

**multipart/form-data 格式**：
- `edit_instruction`: 文本字段
- `use_template`: 文本字段（"true"/"false"）
- `desc_image_urls`: JSON 数组字符串
- `context_images`: 文件上传（多个文件，key 为 "context_images"）

### 2.2 工作流程

#### 步骤 1：参数验证和准备

**输入**：
- `project_id`: 项目ID
- `page_id`: 页面ID
- `edit_instruction`: 编辑指令（必需）
- `context_images`: 上下文图片配置（可选）

**处理逻辑**：
```629:666:banana-slides/backend/controllers/page_controller.py
        # Parse request data (support both JSON and multipart/form-data)
        if request.is_json:
            data = request.get_json()
            uploaded_files = []
        else:
            # multipart/form-data
            data = request.form.to_dict()
            # Get uploaded files
            uploaded_files = request.files.getlist('context_images')
            # Parse JSON fields
            if 'desc_image_urls' in data and data['desc_image_urls']:
                try:
                    data['desc_image_urls'] = json.loads(data['desc_image_urls'])
                except:
                    data['desc_image_urls'] = []
            else:
                data['desc_image_urls'] = []
        
        if not data or 'edit_instruction' not in data:
            return bad_request("edit_instruction is required")
        
        # Get current image path
        current_image_path = file_service.get_absolute_path(page.generated_image_path)
        
        # Get original description if available
        original_description = None
        desc_content = page.get_description_content()
        if desc_content:
            # Extract text from description_content
            original_description = desc_content.get('text') or ''
            # If text is not available, try to construct from text_content
            if not original_description and desc_content.get('text_content'):
                if isinstance(desc_content['text_content'], list):
                    original_description = '\n'.join(desc_content['text_content'])
                else:
                    original_description = str(desc_content['text_content'])
```

**验证**：
- 检查页面是否存在
- 检查页面是否已有生成的图片
- 检查 `edit_instruction` 是否存在

---

#### 步骤 2：收集参考图片

**输入**：
- `context_images.use_template`: 是否使用模板
- `context_images.desc_image_urls`: 描述中的图片URL列表
- `uploaded_files`: 用户上传的文件列表

**处理逻辑**：
```684:733:banana-slides/backend/controllers/page_controller.py
        # Collect additional reference images
        additional_ref_images = []
        
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
        
        # 2. Add desc image URLs if provided
        if isinstance(context_images, dict):
            desc_image_urls = context_images.get('desc_image_urls', [])
        else:
            desc_image_urls = data.get('desc_image_urls', [])
        
        if desc_image_urls:
            if isinstance(desc_image_urls, str):
                try:
                    desc_image_urls = json.loads(desc_image_urls)
                except:
                    desc_image_urls = []
            if isinstance(desc_image_urls, list):
                additional_ref_images.extend(desc_image_urls)
        
        # 3. Save and add uploaded files to a persistent location
        temp_dir = None
        if uploaded_files:
            # Create a temporary directory in the project's upload folder
            import tempfile
            import shutil
            from werkzeug.utils import secure_filename
            temp_dir = Path(tempfile.mkdtemp(dir=current_app.config['UPLOAD_FOLDER']))
            try:
                for uploaded_file in uploaded_files:
                    if uploaded_file.filename:
                        # Save to temp directory
                        temp_path = temp_dir / secure_filename(uploaded_file.filename)
                        uploaded_file.save(str(temp_path))
                        additional_ref_images.append(str(temp_path))
            except Exception as e:
                # Clean up temp directory on error
                if temp_dir and temp_dir.exists():
                    shutil.rmtree(temp_dir)
                raise e
```

**输出**：
- `additional_ref_images`: 参考图片路径列表（包含模板、描述中的图片、用户上传的图片）
- `temp_dir`: 临时目录路径（用于清理）

---

#### 步骤 3：生成编辑提示词

**输入**：
- `edit_instruction`: 编辑指令
- `original_description`: 原始页面描述（可选）

**处理逻辑**：
```560:564:banana-slides/backend/services/ai_service.py
        edit_instruction = get_image_edit_prompt(
            edit_instruction=prompt,
            original_description=original_description
        )
        return self.generate_image(edit_instruction, current_image_path, aspect_ratio, resolution, additional_ref_images)
```

**提示词结构**（`get_image_edit_prompt()`）：

```643:660:banana-slides/backend/services/prompts.py
    if original_description:
        # 删除"其他页面素材："之后的内容，避免被前面的图影响
        if "其他页面素材" in original_description:
            original_description = original_description.split("其他页面素材")[0].strip()
        
        prompt = (f"""\
该PPT页面的原始页面描述为：
{original_description}

现在，根据以下指令修改这张PPT页面：{edit_instruction}

要求维持原有的文字内容和设计风格，只按照指令进行修改。提供的参考图中既有新素材，也有用户手动框选出的区域，请你根据原图和参考图的关系智能判断用户意图。
""")
    else:
        prompt = f"根据以下指令修改这张PPT页面：{edit_instruction}\n保持原有的内容结构和设计风格，只按照指令进行修改。提供的参考图中既有新素材，也有用户手动框选出的区域，请你根据原图和参考图的关系智能判断用户意图。"
```

**提示词组成部分**：

1. **原始页面描述**（如果有）：从 `page.description_content` 中提取
2. **编辑指令**：用户提供的自然语言指令
3. **要求说明**：
   - 维持原有的文字内容和设计风格
   - 只按照指令进行修改
   - 参考图中既有新素材，也有用户手动框选出的区域
   - 根据原图和参考图的关系智能判断用户意图

---

#### 步骤 4：编辑图片

**输入**：
- `edit_instruction`: 编辑提示词
- `current_image_path`: 当前图片路径（作为参考图片）
- `additional_ref_images`: 额外的参考图片列表

**处理逻辑**：
```661:668:banana-slides/backend/services/task_manager.py
                image = ai_service.edit_image(
                    edit_instruction,
                    current_image_path,
                    aspect_ratio,
                    resolution,
                    original_description=original_description,
                    additional_ref_images=additional_ref_images if additional_ref_images else None
                )
```

**注意**：`edit_image()` 内部会调用 `generate_image()`，将当前图片作为参考图片传递。

**输出**：
- `image`: PIL Image 对象（编辑后的图片）

---

#### 步骤 5：保存图片和版本记录

**处理逻辑**：
```681:684:banana-slides/backend/services/task_manager.py
            # 保存编辑后的图片并创建历史版本记录
            image_path, next_version = save_image_with_version(
                image, project_id, page_id, file_service, page_obj=page
            )
```

**输出**：
- `image_path`: 保存后的图片相对路径
- `next_version`: 新版本号

---

### 2.3 输入输出总结

| 阶段 | 输入 | 输出 |
|------|------|------|
| **参数验证** | `project_id`, `page_id`, `edit_instruction`, `context_images` | 验证通过 |
| **收集参考图片** | `use_template`, `desc_image_urls`, `uploaded_files` | `additional_ref_images` 列表 |
| **生成编辑提示词** | `edit_instruction`, `original_description` | `edit_prompt` 字符串 |
| **编辑图片** | `edit_prompt`, `current_image_path`, `additional_ref_images` | PIL Image 对象 |
| **保存图片** | PIL Image 对象 | `image_path`, `next_version` |

---

## 3. 模板切换的影响

### 3.1 场景：最开始没有模板，生成一版后添加模板

#### 初始状态

- `project.template_image_path = None`
- `project.template_style = {...}` （AI 生成的风格描述，JSON 格式）
- 已生成所有页面的图片（使用风格描述）

#### 用户操作：在幻灯片预览页勾选模板

**前端操作**：
```773:817:banana-slides/frontend/src/pages/SlidePreview.tsx
  const handleTemplateSelect = async (templateFile: File | null, templateId?: string) => {
    if (!projectId) return;
    
    // 如果有templateId，按需加载File
    let file = templateFile;
    if (templateId && !file) {
      file = await getTemplateFile(templateId, userTemplates);
      if (!file) {
        show({ message: '加载模板失败', type: 'error' });
        return;
      }
    }
    
    if (!file) {
      // 如果没有文件也没有 ID，可能是取消选择
      return;
    }
    
    setIsUploadingTemplate(true);
    try {
      await uploadTemplate(projectId, file);
      await syncProject(projectId);
      setIsTemplateModalOpen(false);
      show({ message: '模板更换成功', type: 'success' });
      
      // 更新选择状态
      if (templateId) {
        // 判断是用户模板还是预设模板（短ID通常是预设模板）
        if (templateId.length <= 3 && /^\d+$/.test(templateId)) {
          setSelectedPresetTemplateId(templateId);
          setSelectedTemplateId(null);
        } else {
          setSelectedTemplateId(templateId);
          setSelectedPresetTemplateId(null);
        }
      }
    } catch (error: any) {
      show({ 
        message: `更换模板失败: ${error.message || '未知错误'}`, 
        type: 'error' 
      });
    } finally {
      setIsUploadingTemplate(false);
    }
  };
```

**后端处理**：
```17:56:banana-slides/backend/controllers/template_controller.py
@template_bp.route('/<project_id>/template', methods=['POST'])
def upload_template(project_id):
    """
    POST /api/projects/{project_id}/template - Upload template image
    
    Content-Type: multipart/form-data
    Form: template_image=@file.png
    """
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return not_found('Project')
        
        # Check if file is in request
        if 'template_image' not in request.files:
            return bad_request("No file uploaded")
        
        file = request.files['template_image']
        
        if file.filename == '':
            return bad_request("No file selected")
        
        # Validate file extension
        if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            return bad_request("Invalid file type. Allowed types: png, jpg, jpeg, gif, webp")
        
        # Save template
        file_service = FileService(current_app.config['UPLOAD_FOLDER'])
        file_path = file_service.save_template_image(file, project_id)
        
        # Update project
        project.template_image_path = file_path
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return success_response({
            'template_image_url': f'/files/{project_id}/template/{file_path.split("/")[-1]}'
        })
    
    except Exception as e:
        db.session.rollback()
        return error_response('SERVER_ERROR', str(e), 500)
```

#### 切换后的状态

- `project.template_image_path = "template/xxx.png"` （新模板路径）
- `project.template_style = {...}` （保持不变，但不会被使用）
- 已生成的图片保持不变（不会自动重新生成）

---

### 3.2 影响分析

#### 对已生成图片的影响

**无影响**：
- 已生成的图片不会自动重新生成
- 图片路径和版本记录保持不变

#### 对后续生成的影响

**重新生成单页图片**（`generate_page_image`）：

1. **如果 `use_template=True`**：
   - 使用新模板图片作为参考
   - 风格描述（`style_instructions`）不会被包含在 prompt 中
   - 设计指南：`"配色和设计语言和模板图片严格相似。"`

2. **如果 `use_template=False`**：
   - 不使用模板图片
   - 风格描述会被包含在 prompt 中
   - 设计指南：`"严格按照风格描述进行设计。"`

**批量生成图片**（`generate_images`）：

同样的逻辑：
- `use_template=True` → 使用模板，忽略风格描述
- `use_template=False` → 使用风格描述，忽略模板

**微调图片**（`edit_page_image`）：

- 如果 `context_images.use_template=True`，模板图片会被添加到 `additional_ref_images` 中
- 但编辑提示词不包含风格描述（只包含原始描述和编辑指令）

---

### 3.3 关键代码位置

**风格描述的使用判断**：
```552:564:banana-slides/backend/services/prompts.py
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

**设计指南的生成**：
```547:549:banana-slides/backend/services/prompts.py
    # 根据是否有模板生成不同的设计指南内容
    template_style_guideline = "- 配色和设计语言和模板图片严格相似。" if has_template else "- 严格按照风格描述进行设计。"
    forbidden_template_text_guidline = "- 只参考风格设计，禁止出现模板中的文字。\n" if has_template else ""
```

---

### 3.4 总结

| 场景 | 模板状态 | 风格描述状态 | 生成图片时的行为 |
|------|----------|--------------|------------------|
| **初始生成** | 无模板 | 有风格描述 | 使用风格描述生成 |
| **添加模板后** | 有模板 | 有风格描述（保留但不用） | 取决于 `use_template` 参数 |
| **`use_template=True`** | 有模板 | 忽略 | 使用模板图片，忽略风格描述 |
| **`use_template=False`** | 有模板 | 使用 | 使用风格描述，忽略模板图片 |

**重要提示**：
- 模板和风格描述是**互斥**的，不能同时使用
- 模板优先级更高（如果 `use_template=True`）
- 已生成的图片不会自动更新，需要手动重新生成



