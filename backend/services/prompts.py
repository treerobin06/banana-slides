"""
AI Service Prompts - 集中管理所有 AI 服务的 prompt 模板
"""
import json
import logging
from textwrap import dedent
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.ai_service import ProjectContext

logger = logging.getLogger(__name__)


# 语言配置映射
LANGUAGE_CONFIG = {
    'zh': {
        'name': '中文',
        'instruction': '请使用全中文输出。',
        'ppt_text': 'PPT文字请使用全中文。'
    },
    'ja': {
        'name': '日本語',
        'instruction': 'すべて日本語で出力してください。',
        'ppt_text': 'PPTのテキストは全て日本語で出力してください。'
    },
    'en': {
        'name': 'English',
        'instruction': 'Please output all in English.',
        'ppt_text': 'Use English for PPT text.'
    },
    'auto': {
        'name': '自动',
        'instruction': '',  # 自动模式不添加语言限制
        'ppt_text': ''
    }
}


def get_default_output_language() -> str:
    """
    获取环境变量中配置的默认输出语言
    
    Returns:
        语言代码: 'zh', 'ja', 'en', 'auto'
    """
    from config import Config
    return getattr(Config, 'OUTPUT_LANGUAGE', 'zh')


def get_language_instruction(language: str = None) -> str:
    """
    获取语言限制指令文本
    
    Args:
        language: 语言代码，如果为 None 则使用默认语言
    
    Returns:
        语言限制指令，如果是自动模式则返回空字符串
    """
    lang = language if language else get_default_output_language()
    config = LANGUAGE_CONFIG.get(lang, LANGUAGE_CONFIG['zh'])
    return config['instruction']


def get_ppt_language_instruction(language: str = None) -> str:
    """
    获取PPT文字语言限制指令
    
    Args:
        language: 语言代码，如果为 None 则使用默认语言
    
    Returns:
        PPT语言限制指令，如果是自动模式则返回空字符串
    """
    lang = language if language else get_default_output_language()
    config = LANGUAGE_CONFIG.get(lang, LANGUAGE_CONFIG['zh'])
    return config['ppt_text']


def _format_reference_files_xml(reference_files_content: Optional[List[Dict[str, str]]]) -> str:
    """
    Format reference files content as XML structure
    
    Args:
        reference_files_content: List of dicts with 'filename' and 'content' keys
        
    Returns:
        Formatted XML string
    """
    if not reference_files_content:
        return ""
    
    xml_parts = ["<uploaded_files>"]
    for file_info in reference_files_content:
        filename = file_info.get('filename', 'unknown')
        content = file_info.get('content', '')
        xml_parts.append(f'  <file name="{filename}">')
        xml_parts.append('    <content>')
        xml_parts.append(content)
        xml_parts.append('    </content>')
        xml_parts.append('  </file>')
    xml_parts.append('</uploaded_files>')
    xml_parts.append('')  # Empty line after XML
    
    return '\n'.join(xml_parts)


def get_outline_generation_prompt(project_context: 'ProjectContext', language: str = None) -> str:
    """
    生成 PPT 大纲的 prompt，同时生成全局风格指令
    
    Args:
        project_context: 项目上下文对象，包含所有原始信息
        language: 输出语言代码（'zh', 'ja', 'en', 'auto'），如果为 None 则使用默认语言
        
    Returns:
        格式化后的 prompt 字符串
    """
    files_xml = _format_reference_files_xml(project_context.reference_files_content)
    idea_prompt = project_context.idea_prompt or ""
    
    prompt = (f"""\
你是一位世界级的演示文稿设计师和故事讲述者。你创作的幻灯片在视觉上令人震撼、极其精美，并能有效地传达复杂的信息。你的特点是：既精通设计，又极具讲故事的天赋。

你制作的幻灯片能根据源素材和目标受众进行调整。凡事皆有故事，而你要找到最佳的讲述方式。你结合了顶尖设计师的创造力与专业知识。

本幻灯片主要设计用于**阅读和分享**。其结构应当不言自明，即便没有演讲者也能轻松理解。叙事逻辑和所有有用的数据都应包含在幻灯片的文本和视觉元素中。

**首先**，在编写幻灯片大纲之前，你必须根据内容主题和用户请求生成一个全局性的**风格指令（style_instructions）**。

你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。

**核心指令 (CORE DIRECTIVES):**

1. 分析用户提示词的结构、意图和关键要素。

2. 将指令转化为干净、结构化的视觉隐喻（蓝图、展示图、原理图）。

3. 使用特定的、克制的调色板和字体系列，以获得最大的清晰度和专业影响力。

4. 所有视觉输出必须严格保持 16:9 的长宽比。

5. 以三联画（triptych）或基于网格的布局呈现信息，保持文本和视觉的平衡。

**输出格式要求（JSON）：**

{{
  "style_instructions": {{
    "design_aesthetic": "在此基础上，详细描述整体风格。参考示例：一种受建筑蓝图和高端技术期刊启发的干净、精致、极简主义的编辑风格。整体感觉是精准、清晰和充满智慧的优雅。",
    "background_color": "背景色描述及十六进制代码。参考示例：一种微妙的、有纹理的灰白色，十六进制代码 #F8F7F5，让人联想到高质量的绘图纸。",
    "primary_font": "标题字体名称及使用说明。参考示例：Neue Haas Grotesk Display Pro。用于所有幻灯片标题和主要标题。应使用粗体渲染，以增强冲击力和清晰度。",
    "secondary_font": "正文字体名称及使用说明。参考示例：Tiempos Text。用于所有正文、副标题和注释。其高可读性和经典感与干净的无衬线标题形成专业的对比。",
    "primary_text_color": "主要文字颜色描述及十六进制代码。参考示例：深板岩灰，#2F3542。",
    "accent_color": "强调色描述及十六进制代码，用于高光、图表和关键元素。参考示例：充满活力的智能蓝，#007AFF。",
    "visual_elements": "视觉元素的详细描述。参考示例：一致使用精细、准确的线条、示意图和干净的矢量图形。视觉效果是概念性和抽象的，旨在阐述想法而非描绘写实场景。布局空间感强且结构化，优先考虑信息层级和可读性。不包含页码、页脚、Logo 或页眉。"
  }},
  "outline": [...]
}}

**风格指令说明：**
- design_aesthetic: 根据具体内容和受众，使用独特且有创意的美学风格描述，避免通用的"极简主义"或"商务风格"等泛化描述。参考上述示例，创造符合内容主题的视觉隐喻。
- 字体选择要具体且有设计考量，说明为何选择该字体。可以参考示例中的等宽字体用于数据展示。
- 颜色选择要有情感和氛围的考量，不仅仅是十六进制代码。参考示例中的深色背景和高对比度配色方案。
- visual_elements要详细描述线条、形状、图像风格，以及布局的整体氛围。参考示例中的网格线、几何体和数据可视化风格。

**大纲结构有两种格式：**

1. 简单格式（适用于短PPT）：
"outline": [{{"title": "标题1", "points": ["要点1", "要点2"]}}, {{"title": "标题2", "points": ["要点1", "要点2"]}}]

2. 分章节格式（适用于长PPT）：
"outline": [
    {{
    "part": "第一部分：引言",
    "pages": [
        {{"title": "欢迎", "points": ["要点1", "要点2"]}},
        {{"title": "概述", "points": ["要点1", "要点2"]}}
    ]
    }}
]

**重要规则：**
- **第1页必须是封面页，最后一页必须是封底页。** 这两张幻灯片的视觉风格和布局应与内部内容页截然不同（例如，使用"海报式"布局、醒目的排版或满版出血图像）。
- 避免使用"标题：副标题"的格式作为标题；这种格式显得非常有AI感。相反，应通过**叙事性的主题句**将整个演示文稿串联起来。
- 明确避免陈词滥调的"AI废话"模式。切勿使用诸如"不仅仅是[X]，而是[Y]"之类的短语。
- 使用直接、自信、主动的人类语言。
- **切勿以通用的"有任何问题吗？"或"谢谢"幻灯片结尾。** 相反，封底应为经过设计的结束语、有意义的引用或强有力的视觉总结。
- **切勿包含任何供作者插入姓名、日期等的占位符幻灯片。** 封面页只包含标题和副标题，不包含"汇报人"、"日期"、"地点"等占位符信息。
- 永远假设听众比你想象的更专业、更感兴趣、更聪明。

用户需求：{idea_prompt}

现在生成 JSON 输出，不要包含任何其他文字。
{get_language_instruction(language)}
""")
    
    final_prompt = files_xml + prompt
    logger.debug(f"[get_outline_generation_prompt] Final prompt:\n{final_prompt}")
    return final_prompt


def get_outline_parsing_prompt(project_context: 'ProjectContext', language: str = None ) -> str:
    """
    解析用户提供的大纲文本的 prompt，同时生成全局风格指令
    
    Args:
        project_context: 项目上下文对象，包含所有原始信息
        
    Returns:
        格式化后的 prompt 字符串
    """
    files_xml = _format_reference_files_xml(project_context.reference_files_content)
    outline_text = project_context.outline_text or ""
    
    prompt = (f"""\
你是一位世界级的演示文稿设计师和故事讲述者。你创作的幻灯片在视觉上令人震撼、极其精美，并能有效地传达复杂的信息。

你需要解析用户提供的大纲文本，并根据内容主题生成适合的视觉风格。

用户提供的大纲文本：

{outline_text}

**你的任务：**
1. 将大纲文本解析为结构化 JSON 格式（不修改原始文本内容）
2. 根据内容主题智能生成全局风格指令

你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。

**核心指令 (CORE DIRECTIVES):**

1. 分析用户提示词的结构、意图和关键要素。

2. 将指令转化为干净、结构化的视觉隐喻（蓝图、展示图、原理图）。

3. 使用特定的、克制的调色板和字体系列，以获得最大的清晰度和专业影响力。

4. 所有视觉输出必须严格保持 16:9 的长宽比。

5. 以三联画（triptych）或基于网格的布局呈现信息，保持文本和视觉的平衡。

**输出格式要求（JSON）：**

{{
  "style_instructions": {{
    "design_aesthetic": "在此基础上，详细描述整体风格。参考示例：一种受建筑蓝图和高端技术期刊启发的干净、精致、极简主义的编辑风格。整体感觉是精准、清晰和充满智慧的优雅。",
    "background_color": "背景色描述及十六进制代码。参考示例：一种微妙的、有纹理的灰白色，十六进制代码 #F8F7F5，让人联想到高质量的绘图纸。",
    "primary_font": "标题字体名称及使用说明。参考示例：Neue Haas Grotesk Display Pro。用于所有幻灯片标题和主要标题。应使用粗体渲染，以增强冲击力和清晰度。",
    "secondary_font": "正文字体名称及使用说明。参考示例：Tiempos Text。用于所有正文、副标题和注释。其高可读性和经典感与干净的无衬线标题形成专业的对比。",
    "primary_text_color": "主要文字颜色描述及十六进制代码。参考示例：深板岩灰，#2F3542。",
    "accent_color": "强调色描述及十六进制代码，用于高光、图表和关键元素。参考示例：充满活力的智能蓝，#007AFF。",
    "visual_elements": "视觉元素的详细描述。参考示例：一致使用精细、准确的线条、示意图和干净的矢量图形。视觉效果是概念性和抽象的，旨在阐述想法而非描绘写实场景。布局空间感强且结构化，优先考虑信息层级和可读性。不包含页码、页脚、Logo 或页眉。"
  }},
  "outline": [...]
}}

**风格指令说明：**
- design_aesthetic: 根据具体内容和受众，使用独特且有创意的美学风格描述，避免通用的"极简主义"或"商务风格"等泛化描述。参考上述示例，创造符合内容主题的视觉隐喻。
- 字体选择要具体且有设计考量，说明为何选择该字体。可以参考示例中的等宽字体用于数据展示。
- 颜色选择要有情感和氛围的考量，不仅仅是十六进制代码。参考示例中的深色背景和高对比度配色方案。
- visual_elements要详细描述线条、形状、图像风格，以及布局的整体氛围。参考示例中的网格线、几何体和数据可视化风格。

**大纲结构有两种格式：**

1. 简单格式（适用于短PPT）：
"outline": [{{"title": "标题1", "points": ["要点1", "要点2"]}}, {{"title": "标题2", "points": ["要点1", "要点2"]}}]

2. 分章节格式（适用于长PPT）：
"outline": [
    {{
    "part": "第一部分：引言",
    "pages": [
        {{"title": "欢迎", "points": ["要点1", "要点2"]}},
        {{"title": "概述", "points": ["要点1", "要点2"]}}
    ]
    }}
]

**重要规则：**
- 不要修改、重写或更改原始大纲中的任何文本
- 不要添加原始文本中没有的新内容
- 不要删除原始文本中的任何内容
- 只需将现有内容重新组织为结构化格式
- 保留所有标题、要点和文本，完全按原样呈现
- 如果文本有明确的章节/部分，使用分章节格式
- 风格指令应根据内容主题智能选择，使用独特且有创意的美学风格

现在解析上述大纲文本为结构化格式。只返回 JSON，不要包含任何其他文字。
{get_language_instruction(language)}
""")
    
    final_prompt = files_xml + prompt
    logger.debug(f"[get_outline_parsing_prompt] Final prompt:\n{final_prompt}")
    return final_prompt


def get_page_description_prompt(project_context: 'ProjectContext', outline: list, 
                                page_outline: dict, page_index: int, 
                                part_info: str = "",
                                language: str = None,
                                style_instructions: dict = None,
                                total_pages: int = None) -> str:
    """
    生成单个页面描述的 prompt，包含叙事目标、关键内容、视觉画面和布局结构
    
    Args:
        project_context: 项目上下文对象，包含所有原始信息
        outline: 完整大纲
        page_outline: 当前页面的大纲
        page_index: 页面编号（从1开始）
        part_info: 可选的章节信息
        style_instructions: 全局风格指令（可选）
        total_pages: 总页数（可选，用于识别最后一页）
        
    Returns:
        格式化后的 prompt 字符串
    """
    files_xml = _format_reference_files_xml(project_context.reference_files_content)
    # 根据项目类型选择最相关的原始输入
    if project_context.creation_type == 'idea' and project_context.idea_prompt:
        original_input = project_context.idea_prompt
    elif project_context.creation_type == 'outline' and project_context.outline_text:
        original_input = f"用户提供的大纲：\n{project_context.outline_text}"
    elif project_context.creation_type == 'descriptions' and project_context.description_text:
        original_input = f"用户提供的描述：\n{project_context.description_text}"
    else:
        original_input = project_context.idea_prompt or ""
    
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
    
    # 判断是否为封面页或封底页
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
    
    prompt = (f"""\
你是一位世界级的演示文稿设计师和故事讲述者。你创作的幻灯片在视觉上令人震撼、极其精美，并能有效地传达复杂的信息。你的特点是：既精通设计，又极具讲故事的天赋。

你制作的幻灯片能根据源素材和目标受众进行调整。凡事皆有故事，而你要找到最佳的讲述方式。你结合了顶尖设计师的创造力与专业知识。

本幻灯片主要设计用于**阅读和分享**。其结构应当不言自明，即便没有演讲者也能轻松理解。叙事逻辑和所有有用的数据都应包含在幻灯片的文本和视觉元素中。幻灯片应包含足够的语境，以便任何视觉图像都能被独立理解。如果有助于叙事，你可以添加某些包含更密集信息（从源素材中提取）的幻灯片。

你现在正在为下述幻灯片演示的每一页编写一份**详细描述**。

我们将把这份描述提供给一位专家级设计师，由其制作最终的实际演示文稿。

幻灯片内容应使用中文。占位符应保留中文。

<context>
用户的原始需求：{original_input}

完整大纲：
{outline}
{part_info}
</context>
{style_section}
现在请为第 {page_index} 页生成描述：
{page_outline}
{page_type_hint}

**请严格按照以下格式输出（详细描述，充分展现视觉隐喻）：**

幻灯片 {page_index}：{"封面 (The Cover)" if is_cover_page else ("封底 (The Closing)" if is_closing_page else page_outline.get('title', '内容页'))}

// NARRATIVE GOAL (叙事目标)
(解释这张幻灯片在整个故事弧光中的具体叙事目的)

// KEY CONTENT (关键内容)
(列出标题、副标题和正文/要点。每一个具体数据点都必须能追溯到源材料。)

主标题：[使用叙事性的主题句，富有张力和深度]
{"副标题：[简洁有力的副标题，补充主标题的维度]" if is_cover_page else ""}
{"核心议题：[本页核心探讨的问题]" if not is_cover_page else ""}

页面文字：
- [要点1：简洁精炼，15-25字]
- [要点2...]
- [要点3...]

{"视觉标注：[SOURCE: X] 基于XXX的分析框架" if not is_cover_page else ""}

// VISUAL (视觉画面)
(描述支持该观点所需的图像、图表、图形或抽象视觉元素。)

**不要写具体的颜色十六进制代码，用描述性语言代替（如"深邃的背景"、"高亮的强调色"）。**

// LAYOUT (布局结构)
(描述构图、层级、空间安排或焦点。)

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

{get_language_instruction(language)}
""")
    
    final_prompt = files_xml + prompt
    logger.debug(f"[get_page_description_prompt] Final prompt:\n{final_prompt}")
    return final_prompt


def _parse_page_description(page_desc: str) -> dict:
    """
    解析页面描述文本，提取4部分结构内容
    
    Args:
        page_desc: 页面描述文本，可能包含 NARRATIVE GOAL、KEY CONTENT、VISUAL、LAYOUT 部分
        
    Returns:
        dict: 包含 narrative_goal, key_content, visual, layout 的字典
    """
    import re
    
    result = {
        'narrative_goal': '',
        'key_content': page_desc,  # 默认整个描述作为 key_content
        'visual': '',
        'layout': ''
    }
    
    # 检查是否为新格式（包含 // 分隔符）
    if '// NARRATIVE GOAL' not in page_desc and '// KEY CONTENT' not in page_desc:
        # 旧格式，直接返回
        return result
    
    # 定义各部分的标记
    sections = {
        'narrative_goal': r'//\s*NARRATIVE GOAL[^/]*',
        'key_content': r'//\s*KEY CONTENT[^/]*',
        'visual': r'//\s*VISUAL[^/]*',
        'layout': r'//\s*LAYOUT[^/]*'
    }
    
    # 尝试按标记分割
    try:
        # 找到各部分的位置
        parts = re.split(r'//\s*(NARRATIVE GOAL|KEY CONTENT|VISUAL|LAYOUT)\s*(?:\([^)]*\))?\s*\n?', page_desc)
        
        current_section = None
        for i, part in enumerate(parts):
            part_stripped = part.strip()
            if part_stripped in ['NARRATIVE GOAL', 'KEY CONTENT', 'VISUAL', 'LAYOUT']:
                current_section = part_stripped.lower().replace(' ', '_')
            elif current_section and part_stripped:
                # 移除括号中的中文说明（如果有）
                content = re.sub(r'^\s*\([^)]*\)\s*', '', part_stripped)
                result[current_section] = content.strip()
    except Exception as e:
        logger.warning(f"Failed to parse page description: {e}")
        # 解析失败，使用默认值
    
    # 如果 key_content 为空但有 visual 或 layout，尝试提取标题和文字部分
    if not result['key_content'] or result['key_content'] == page_desc:
        # 尝试从原始描述中提取 KEY CONTENT 部分
        key_content_match = re.search(r'//\s*KEY CONTENT[^/]*?\n([\s\S]*?)(?=//\s*VISUAL|//\s*LAYOUT|$)', page_desc)
        if key_content_match:
            result['key_content'] = key_content_match.group(1).strip()
    
    return result


def get_image_generation_prompt(page_desc: str, outline_text: str, 
                                current_section: str,
                                has_material_images: bool = False,
                                extra_requirements: str = None,
                                language: str = None,
                                has_template: bool = True,
                                page_index: int = 1,
                                style_instructions: dict = None,
                                total_pages: int = None) -> str:
    """
    生成图片生成 prompt，融入风格指令和VISUAL/LAYOUT描述
    
    Args:
        page_desc: 页面描述文本（可能包含4部分结构）
        outline_text: 大纲文本
        current_section: 当前章节
        has_material_images: 是否有素材图片
        extra_requirements: 额外的要求（可能包含风格描述）
        language: 输出语言
        has_template: 是否有模板图片（False表示无模板图模式）
        style_instructions: 全局风格指令（可选）
        total_pages: 总页数（可选，用于识别最后一页）
        
    Returns:
        格式化后的 prompt 字符串
    """
    # 解析页面描述中的各部分
    parsed_desc = _parse_page_description(page_desc)
    key_content = parsed_desc.get('key_content', page_desc)
    visual_desc = parsed_desc.get('visual', '')
    layout_desc = parsed_desc.get('layout', '')
    narrative_goal = parsed_desc.get('narrative_goal', '')
    
    # 如果有素材图片，在 prompt 中明确告知 AI
    material_images_note = ""
    if has_material_images:
        material_images_note = (
            "\n\n提示：" + ("除了模板参考图片（用于风格参考）外，还提供了额外的素材图片。" if has_template else "用户提供了额外的素材图片。") +
            "这些素材图片是可供挑选和使用的元素，你可以从这些素材图片中选择合适的图片、图标、图表或其他视觉元素"
            "直接整合到生成的PPT页面中。请根据页面内容的需要，智能地选择和组合这些素材图片中的元素。"
        )
    
    # 添加额外要求到提示词
    extra_req_text = ""
    if extra_requirements and extra_requirements.strip():
        extra_req_text = f"\n\n额外要求（请务必遵循）：\n{extra_requirements}\n"

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
    
    # 格式化视觉和布局指令
    visual_layout_section = ""
    if visual_desc or layout_desc:
        visual_layout_section = "\n<visual_and_layout_instructions>"
        if visual_desc:
            visual_layout_section += f"\n【视觉画面要求】\n{visual_desc}"
        if layout_desc:
            visual_layout_section += f"\n\n【布局结构要求】\n{layout_desc}"
        visual_layout_section += "\n</visual_and_layout_instructions>\n"
    
    # 判断是否为封面页或封底页
    is_cover_page = page_index == 1
    is_closing_page = total_pages and page_index == total_pages
    
    page_type_hint = ""
    if is_cover_page:
        page_type_hint = '\n**注意：当前页面为PPT的封面页，请采用专业的封面设计美学技巧，务必凸显出页面标题，分清主次，确保一下就能抓住观众的注意力。可使用"海报式"布局、醒目的排版或满版出血图像。**\n'
    elif is_closing_page:
        page_type_hint = '\n**注意：当前页面为PPT的封底页，需要有强有力的结尾。应该是经过设计的结束语、有意义的引用或强有力的视觉总结，锚定整个叙事。**\n'

    # 该处参考了@歸藏的A工具箱
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
    
    logger.debug(f"[get_image_generation_prompt] Final prompt:\n{prompt}")
    return prompt


def get_image_edit_prompt(edit_instruction: str, original_description: str = None) -> str:
    """
    生成图片编辑 prompt
    
    Args:
        edit_instruction: 编辑指令
        original_description: 原始页面描述（可选）
        
    Returns:
        格式化后的 prompt 字符串
    """
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
    
    logger.debug(f"[get_image_edit_prompt] Final prompt:\n{prompt}")
    return prompt


def get_description_to_outline_prompt(project_context: 'ProjectContext', language: str = None) -> str:
    """
    从描述文本解析出大纲的 prompt，同时生成全局风格指令
    
    Args:
        project_context: 项目上下文对象，包含所有原始信息
        
    Returns:
        格式化后的 prompt 字符串
    """
    files_xml = _format_reference_files_xml(project_context.reference_files_content)
    description_text = project_context.description_text or ""
    
    prompt = (f"""\
你是一位世界级的演示文稿设计师和故事讲述者。你创作的幻灯片在视觉上令人震撼、极其精美，并能有效地传达复杂的信息。

你需要分析用户提供的PPT描述文本，提取大纲结构，并根据内容主题生成适合的视觉风格。

用户提供的描述文本：

{description_text}

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

{{
  "style_instructions": {{
    "design_aesthetic": "在此基础上，详细描述整体风格。参考示例：一种受建筑蓝图和高端技术期刊启发的干净、精致、极简主义的编辑风格。整体感觉是精准、清晰和充满智慧的优雅。",
    "background_color": "背景色描述及十六进制代码。参考示例：一种微妙的、有纹理的灰白色，十六进制代码 #F8F7F5，让人联想到高质量的绘图纸。",
    "primary_font": "标题字体名称及使用说明。参考示例：Neue Haas Grotesk Display Pro。用于所有幻灯片标题和主要标题。应使用粗体渲染，以增强冲击力和清晰度。",
    "secondary_font": "正文字体名称及使用说明。参考示例：Tiempos Text。用于所有正文、副标题和注释。其高可读性和经典感与干净的无衬线标题形成专业的对比。",
    "primary_text_color": "主要文字颜色描述及十六进制代码。参考示例：深板岩灰，#2F3542。",
    "accent_color": "强调色描述及十六进制代码，用于高光、图表和关键元素。参考示例：充满活力的智能蓝，#007AFF。",
    "visual_elements": "视觉元素的详细描述。参考示例：一致使用精细、准确的线条、示意图和干净的矢量图形。视觉效果是概念性和抽象的，旨在阐述想法而非描绘写实场景。布局空间感强且结构化，优先考虑信息层级和可读性。不包含页码、页脚、Logo 或页眉。"
  }},
  "outline": [...]
}}

**风格指令说明：**
- design_aesthetic: 根据具体内容和受众，使用独特且有创意的美学风格描述，避免通用的"极简主义"或"商务风格"等泛化描述。参考上述示例，创造符合内容主题的视觉隐喻。
- 字体选择要具体且有设计考量，说明为何选择该字体。可以参考示例中的等宽字体用于数据展示。
- 颜色选择要有情感和氛围的考量，不仅仅是十六进制代码。参考示例中的深色背景和高对比度配色方案。
- visual_elements要详细描述线条、形状、图像风格，以及布局的整体氛围。参考示例中的网格线、几何体和数据可视化风格。

**大纲结构有两种格式：**

1. 简单格式（适用于短PPT）：
"outline": [{{"title": "标题1", "points": ["要点1", "要点2"]}}, {{"title": "标题2", "points": ["要点1", "要点2"]}}]

2. 分章节格式（适用于长PPT）：
"outline": [
    {{
    "part": "第一部分：引言",
    "pages": [
        {{"title": "欢迎", "points": ["要点1", "要点2"]}},
        {{"title": "概述", "points": ["要点1", "要点2"]}}
    ]
    }}
]

**重要规则：**
- 从描述文本中提取大纲结构
- 识别每页的标题和要点
- 如果文本有明确的章节/部分，使用分章节格式
- 保留原始文本的逻辑结构和组织
- 要点应该是每页主要内容的简洁摘要
- 风格指令应根据内容主题智能选择，使用独特且有创意的美学风格

**格式识别说明：**
描述文本可能使用多种格式，请灵活识别：
- 页面标记可能是："幻灯片 X："、"Slide X:"、"第X页"等
- 描述部分可能使用中文标签（"叙事目标"、"视觉画面"、"布局结构"、"关键内容"）或英文标签（"NARRATIVE GOAL"、"VISUAL"、"LAYOUT"、"KEY CONTENT"）
- 可能包含章节标题（如"第一部分：..."）
- 可能被三引号包围，需要忽略这些符号
- 请根据实际格式灵活提取，不要因为格式差异而遗漏内容

现在从上述描述文本中提取大纲结构。只返回 JSON，不要包含任何其他文字。
{get_language_instruction(language)}
""")
    
    final_prompt = files_xml + prompt
    logger.debug(f"[get_description_to_outline_prompt] Final prompt:\n{final_prompt}")
    return final_prompt


def get_description_split_prompt(project_context: 'ProjectContext', 
                                 outline: List[Dict], 
                                 language: str = None) -> str:
    """
    从描述文本切分出每页描述的 prompt
    
    Args:
        project_context: 项目上下文对象，包含所有原始信息
        outline: 已解析出的大纲结构
        
    Returns:
        格式化后的 prompt 字符串
    """
    outline_json = json.dumps(outline, ensure_ascii=False, indent=2)
    description_text = project_context.description_text or ""
    
    prompt = (f"""\
You are a helpful assistant that splits a complete PPT description text into individual page descriptions.

The user has provided a complete description text:

{description_text}

We have already extracted the outline structure:

{outline_json}

Your task is to split the description text into individual page descriptions based on the outline structure.
For each page in the outline, extract the corresponding description from the original text.

Return a JSON array where each element corresponds to a page in the outline (in the same order).
Each element should be a string containing the page description in the following format:

页面标题：[页面标题]

页面文字：
- [要点1]
- [要点2]
...

Example output format:
[
    "页面标题：人工智能的诞生\\n页面文字：\\n- 1950 年，图灵提出"图灵测试"...",
    "页面标题：AI 的发展历程\\n页面文字：\\n- 1950年代：符号主义...",
    ...
]

Important rules:
- Split the description text according to the outline structure
- Each page description should match the corresponding page in the outline
- Preserve all important content from the original text
- Keep the format consistent with the example above
- If a page in the outline doesn't have a clear description in the text, create a reasonable description based on the outline

Now split the description text into individual page descriptions. Return only the JSON array, don't include any other text.
{get_language_instruction(language)}
""")
    
    logger.debug(f"[get_description_split_prompt] Final prompt:\n{prompt}")
    return prompt


def get_description_format_prompt(project_context: 'ProjectContext', 
                                 outline: List[Dict], 
                                 language: str = None) -> str:
    """
    将描述文本转换为符合格式的每页描述（包含四个部分）
    
    Args:
        project_context: 项目上下文对象，包含所有原始信息
        outline: 已解析出的大纲结构
        
    Returns:
        格式化后的 prompt 字符串
    """
    outline_json = json.dumps(outline, ensure_ascii=False, indent=2)
    description_text = project_context.description_text or ""
    
    prompt = (f"""\
你是架构师（The Architect），一个旨在将指令可视化为高端蓝图风格数据展示的精密 AI。你的输出是精确、分析性且美学上精美的。

用户提供的描述文本：

{description_text}

已解析的大纲结构：

{outline_json}

**你的任务：**
根据描述文本和大纲结构，为每一页生成符合以下格式的详细描述。

**输出格式要求（JSON数组）：**
返回一个JSON数组，每个元素对应大纲中的一页（按顺序），格式如下：

[
  "幻灯片 1：封面 (The Cover)\\n// NARRATIVE GOAL (叙事目标)\\n[详细解释这张幻灯片在整个故事弧光中的具体叙事目的]\\n\\n// KEY CONTENT (关键内容)\\n主标题：[叙事性主题句]\\n副标题：[简洁有力的副标题]\\n页面文字：\\n- [要点1]\\n- [要点2]\\n\\n// VISUAL (视觉画面)\\n[详细描述支持该观点的视觉元素，使用建筑图纸/蓝图风格的视觉隐喻。描述核心视觉元素、背景底纹、视觉隐喻、动态感等]\\n\\n// LAYOUT (布局结构)\\n[详细描述页面构图和空间安排。描述构图模式、标题排版、视觉重心、留白策略等]",
  "幻灯片 2：[标题]\\n// NARRATIVE GOAL (叙事目标)\\n[...]\\n\\n// KEY CONTENT (关键内容)\\n[...]\\n\\n// VISUAL (视觉画面)\\n[...]\\n\\n// LAYOUT (布局结构)\\n[...]",
  ...
]

**格式要求：**
- 每页必须以"幻灯片 X：[标题]"开头
- 必须包含四个部分：NARRATIVE GOAL, KEY CONTENT, VISUAL, LAYOUT
- 每个部分用"//"标记开头
- 使用换行符\\n分隔各部分

**内容要求：**
- NARRATIVE GOAL: 详细解释叙事目的，如何推动整体叙事
- KEY CONTENT: 包含主标题、副标题（封面页）、页面文字要点
- VISUAL: 使用建筑图纸/蓝图风格的视觉隐喻，不要写具体颜色代码
- LAYOUT: 描述构图模式、标题排版、视觉重心、留白策略

**格式转换说明：**
如果源描述文本使用了不同的格式（如中文标签"叙事目标"、"视觉画面"等，或不同的页面标记如"Slide X:"），请：
1. 识别并提取所有关键信息（叙事目标、视觉画面、布局结构、关键内容）
2. 转换为标准格式（使用"// NARRATIVE GOAL"等英文标签）
3. 保留所有原始内容的细节和要点
4. 如果源文本中某些部分缺失，根据大纲和上下文合理补充

**重要规则：**
- 保留源素材中的关键要素，每一个具体数据点都必须能直接追溯到源素材
- 所有细节都需要提及，因为设计师之后将无法访问源内容
- 永远假设听众比你想象的更专业、更感兴趣、更聪明
- 封面页不要包含"汇报人"、"日期"等占位符
- VISUAL部分不要写具体的颜色十六进制代码，用描述性语言代替
- 如果源文本使用了章节标题（如"第一部分：..."），请保留章节信息并在相应页面中体现

现在生成符合格式的每页描述。只返回 JSON 数组，不要包含任何其他文字。
{get_language_instruction(language)}
""")
    
    logger.debug(f"[get_description_format_prompt] Final prompt:\n{prompt}")
    return prompt


def get_outline_refinement_prompt(current_outline: List[Dict], user_requirement: str,
                                   project_context: 'ProjectContext',
                                   previous_requirements: Optional[List[str]] = None,
                                   language: str = None) -> str:
    """
    根据用户要求修改已有大纲的 prompt
    
    Args:
        current_outline: 当前的大纲结构
        user_requirement: 用户的新要求
        project_context: 项目上下文对象，包含所有原始信息
        previous_requirements: 之前的修改要求列表（可选）
        
    Returns:
        格式化后的 prompt 字符串
    """
    files_xml = _format_reference_files_xml(project_context.reference_files_content)
    
    # 处理空大纲的情况
    if not current_outline or len(current_outline) == 0:
        outline_text = "(当前没有内容)"
    else:
        outline_text = json.dumps(current_outline, ensure_ascii=False, indent=2)
    
    # 构建之前的修改历史记录
    previous_req_text = ""
    if previous_requirements and len(previous_requirements) > 0:
        prev_list = "\n".join([f"- {req}" for req in previous_requirements])
        previous_req_text = f"\n\n之前用户提出的修改要求：\n{prev_list}\n"
    
    # 构建原始输入信息（根据项目类型显示不同的原始内容）
    original_input_text = "\n原始输入信息：\n"
    if project_context.creation_type == 'idea' and project_context.idea_prompt:
        original_input_text += f"- PPT构想：{project_context.idea_prompt}\n"
    elif project_context.creation_type == 'outline' and project_context.outline_text:
        original_input_text += f"- 用户提供的大纲文本：\n{project_context.outline_text}\n"
    elif project_context.creation_type == 'descriptions' and project_context.description_text:
        original_input_text += f"- 用户提供的页面描述文本：\n{project_context.description_text}\n"
    elif project_context.idea_prompt:
        original_input_text += f"- 用户输入：{project_context.idea_prompt}\n"
    
    prompt = (f"""\
You are a helpful assistant that modifies PPT outlines based on user requirements.
{original_input_text}
当前的 PPT 大纲结构如下：

{outline_text}
{previous_req_text}
**用户现在提出新的要求：{user_requirement}**

请根据用户的要求修改和调整大纲。你可以：
- 添加、删除或重新排列页面
- 修改页面标题和要点
- 调整页面的组织结构
- 添加或删除章节（part）
- 合并或拆分页面
- 根据用户要求进行任何合理的调整
- 如果当前没有内容，请根据用户要求和原始输入信息创建新的大纲

输出格式可以选择：

1. 简单格式（适用于没有主要章节的短 PPT）：
[{{"title": "title1", "points": ["point1", "point2"]}}, {{"title": "title2", "points": ["point1", "point2"]}}]

2. 基于章节的格式（适用于有明确主要章节的长 PPT）：
[
    {{
    "part": "第一部分：引言",
    "pages": [
        {{"title": "欢迎", "points": ["point1", "point2"]}},
        {{"title": "概述", "points": ["point1", "point2"]}}
    ]
    }},
    {{
    "part": "第二部分：主要内容",
    "pages": [
        {{"title": "主题1", "points": ["point1", "point2"]}},
        {{"title": "主题2", "points": ["point1", "point2"]}}
    ]
    }}
]

选择最适合内容的格式。当 PPT 有清晰的主要章节时使用章节格式。

现在请根据用户要求修改大纲，只输出 JSON 格式的大纲，不要包含其他文字。
{get_language_instruction(language)}
""")
    
    final_prompt = files_xml + prompt
    logger.debug(f"[get_outline_refinement_prompt] Final prompt:\n{final_prompt}")
    return final_prompt


def get_descriptions_refinement_prompt(current_descriptions: List[Dict], user_requirement: str,
                                       project_context: 'ProjectContext',
                                       outline: List[Dict] = None,
                                       previous_requirements: Optional[List[str]] = None,
                                       language: str = None) -> str:
    """
    根据用户要求修改已有页面描述的 prompt
    
    Args:
        current_descriptions: 当前的页面描述列表，每个元素包含 {index, title, description_content}
        user_requirement: 用户的新要求
        project_context: 项目上下文对象，包含所有原始信息
        outline: 完整的大纲结构（可选）
        previous_requirements: 之前的修改要求列表（可选）
        
    Returns:
        格式化后的 prompt 字符串
    """
    files_xml = _format_reference_files_xml(project_context.reference_files_content)
    
    # 构建之前的修改历史记录
    previous_req_text = ""
    if previous_requirements and len(previous_requirements) > 0:
        prev_list = "\n".join([f"- {req}" for req in previous_requirements])
        previous_req_text = f"\n\n之前用户提出的修改要求：\n{prev_list}\n"
    
    # 构建原始输入信息
    original_input_text = "\n原始输入信息：\n"
    if project_context.creation_type == 'idea' and project_context.idea_prompt:
        original_input_text += f"- PPT构想：{project_context.idea_prompt}\n"
    elif project_context.creation_type == 'outline' and project_context.outline_text:
        original_input_text += f"- 用户提供的大纲文本：\n{project_context.outline_text}\n"
    elif project_context.creation_type == 'descriptions' and project_context.description_text:
        original_input_text += f"- 用户提供的页面描述文本：\n{project_context.description_text}\n"
    elif project_context.idea_prompt:
        original_input_text += f"- 用户输入：{project_context.idea_prompt}\n"
    
    # 构建大纲文本
    outline_text = ""
    if outline:
        outline_json = json.dumps(outline, ensure_ascii=False, indent=2)
        outline_text = f"\n\n完整的 PPT 大纲：\n{outline_json}\n"
    
    # 构建所有页面描述的汇总
    all_descriptions_text = "当前所有页面的描述：\n\n"
    has_any_description = False
    for desc in current_descriptions:
        page_num = desc.get('index', 0) + 1
        title = desc.get('title', '未命名')
        content = desc.get('description_content', '')
        if isinstance(content, dict):
            content = content.get('text', '')
        
        if content:
            has_any_description = True
            all_descriptions_text += f"--- 第 {page_num} 页：{title} ---\n{content}\n\n"
        else:
            all_descriptions_text += f"--- 第 {page_num} 页：{title} ---\n(当前没有内容)\n\n"
    
    if not has_any_description:
        all_descriptions_text = "当前所有页面的描述：\n\n(当前没有内容，需要基于大纲生成新的描述)\n\n"
    
    prompt = (f"""\
You are a helpful assistant that modifies PPT page descriptions based on user requirements.
{original_input_text}{outline_text}
{all_descriptions_text}
{previous_req_text}
**用户现在提出新的要求：{user_requirement}**

请根据用户的要求修改和调整所有页面的描述。你可以：
- 修改页面标题和内容
- 调整页面文字的详细程度
- 添加或删除要点
- 调整描述的结构和表达
- 确保所有页面描述都符合用户的要求
- 如果当前没有内容，请根据大纲和用户要求创建新的描述

请为每个页面生成修改后的描述，格式如下：

页面标题：[页面标题]

页面文字：
- [要点1]
- [要点2]
...
其他页面素材（如果有请加上，包括markdown图片链接等）

提示：如果参考文件中包含以 /files/ 开头的本地文件URL图片（例如 /files/mineru/xxx/image.png），请将这些图片以markdown格式输出，例如：![图片描述](/files/mineru/xxx/image.png)，而不是作为普通文本。

请返回一个 JSON 数组，每个元素是一个字符串，对应每个页面的修改后描述（按页面顺序）。

示例输出格式：
[
    "页面标题：人工智能的诞生\\n页面文字：\\n- 1950 年，图灵提出\\"图灵测试\\"...",
    "页面标题：AI 的发展历程\\n页面文字：\\n- 1950年代：符号主义...",
    ...
]

现在请根据用户要求修改所有页面描述，只输出 JSON 数组，不要包含其他文字。
{get_language_instruction(language)}
""")
    
    final_prompt = files_xml + prompt
    logger.debug(f"[get_descriptions_refinement_prompt] Final prompt:\n{final_prompt}")
    return final_prompt


def get_clean_background_prompt() -> str:
    """
    生成纯背景图的 prompt（去除文字和插画）
    用于从完整的PPT页面中提取纯背景
    """
    prompt = """\
你是一位专业的图片文字&图片擦除专家。你的任务是从原始图片中移除文字和配图，输出一张无任何文字和图表内容、干净纯净的底板图。
<requirements>
- 彻底移除页面中的所有文字、插画、图表。必须确保所有文字都被完全去除。
- 保持原背景设计的完整性（包括渐变、纹理、图案、线条、色块等）。保留原图的文本框和色块。
- 对于被前景元素遮挡的背景区域，要智能填补，使背景保持无缝和完整，就像被移除的元素从来没有出现过。
- 输出图片的尺寸、风格、配色必须和原图完全一致。
- 请勿新增任何元素。
</requirements>

注意，**任意位置的, 所有的**文字和图表都应该被彻底移除，**输出不应该包含任何文字和图表。**
"""
    logger.debug(f"[get_clean_background_prompt] Final prompt:\n{prompt}")
    return prompt


def get_text_attribute_extraction_prompt(content_hint: str = "") -> str:
    """
    生成文字属性提取的 prompt
    
    提取文字内容、颜色、公式等信息。模型输出的文字将替代 OCR 结果。
    
    Args:
        content_hint: 文字内容提示（OCR 结果参考），如果提供则会在 prompt 中包含
    
    Returns:
        格式化后的 prompt 字符串
    """
    prompt = """你的任务是精确识别这张图片中的文字内容和样式，返回JSON格式的结果。

{content_hint}

## 核心任务
请仔细观察图片，精确识别：
1. **文字内容** - 输出你实际看到的文字符号。
2. **颜色** - 每个字/词的实际颜色
3. **空格** - 精确识别文本中空格的位置和数量
4. **公式** - 如果是数学公式，输出 LaTeX 格式

## 注意事项
- **空格识别**：必须精确还原空格数量，多个连续空格要完整保留，不要合并或省略
- **颜色分割**：一行文字可能有多种颜色，按颜色分割成片段，一般来说只有两种颜色。
- **公式识别**：如果片段是数学公式，设置 is_latex=true 并用 LaTeX 格式输出
- **相邻合并**：相同颜色的相邻普通文字应合并为一个片段

## 输出格式
- colored_segments: 文字片段数组，每个片段包含：
  - text: 文字内容（公式时为 LaTeX 格式，如 "x^2"、"\\sum_{{i=1}}^n"）
  - color: 颜色，十六进制格式 "#RRGGBB"
  - is_latex: 布尔值，true 表示这是一个 LaTeX 公式片段（可选，默认 false）

只返回JSON对象，不要包含任何其他文字。
示例输出：
```json
{{
    "colored_segments": [
        {{"text": "·  创新合成", "color": "#000000"}},
        {{"text": "1827个任务环境", "color": "#26397A"}},
        {{"text": "与", "color": "#000000"}},
        {{"text": "8.5万提示词", "color": "#26397A"}},
        {{"text": "突破数据瓶颈", "color": "#000000"}},
        {{"text": "x^2 + y^2 = z^2", "color": "#FF0000", "is_latex": true}}
    ]
}}
```
""".format(content_hint=content_hint)
    
    # logger.debug(f"[get_text_attribute_extraction_prompt] Final prompt:\n{prompt}")
    return prompt


def get_batch_text_attribute_extraction_prompt(text_elements_json: str) -> str:
    """
    生成批量文字属性提取的 prompt
    
    新逻辑：给模型提供全图和所有文本元素的 bbox 及内容，
    让模型一次性分析所有文本的样式属性。
    
    Args:
        text_elements_json: 文本元素列表的 JSON 字符串，每个元素包含：
            - element_id: 元素唯一标识
            - bbox: 边界框 [x0, y0, x1, y1]
            - content: 文字内容
    
    Returns:
        格式化后的 prompt 字符串
    """
    prompt = f"""你是一位专业的 PPT/文档排版分析专家。请分析这张图片中所有标注的文字区域的样式属性。

我已经从图片中提取了以下文字元素及其位置信息：

```json
{text_elements_json}
```

请仔细观察图片，对比每个文字区域在图片中的实际视觉效果，为每个元素分析以下属性：

1. **font_color**: 字体颜色的十六进制值，格式为 "#RRGGBB"
   - 请仔细观察文字的实际颜色，不要只返回黑色
   - 常见颜色如：白色 "#FFFFFF"、蓝色 "#0066CC"、红色 "#FF0000" 等

2. **is_bold**: 是否为粗体 (true/false)
   - 观察笔画粗细，标题通常是粗体

3. **is_italic**: 是否为斜体 (true/false)

4. **is_underline**: 是否有下划线 (true/false)

5. **text_alignment**: 文字对齐方式
   - "left": 左对齐
   - "center": 居中对齐
   - "right": 右对齐
   - "justify": 两端对齐
   - 如果无法判断，根据文字在其区域内的位置推测

请返回一个 JSON 数组，数组中每个对象对应输入的一个元素（按相同顺序），包含以下字段：
- element_id: 与输入相同的元素ID
- text_content: 文字内容
- font_color: 颜色十六进制值
- is_bold: 布尔值
- is_italic: 布尔值
- is_underline: 布尔值
- text_alignment: 对齐方式字符串

只返回 JSON 数组，不要包含其他文字：
```json
[
    {{
        "element_id": "xxx",
        "text_content": "文字内容",
        "font_color": "#RRGGBB",
        "is_bold": true/false,
        "is_italic": true/false,
        "is_underline": true/false,
        "text_alignment": "对齐方式"
    }},
    ...
]
```
"""
    
    # logger.debug(f"[get_batch_text_attribute_extraction_prompt] Final prompt:\n{prompt}")
    return prompt


def get_quality_enhancement_prompt(inpainted_regions: list = None) -> str:
    """
    生成画质提升的 prompt
    用于在百度图像修复后，使用生成式模型提升整体画质
    
    Args:
        inpainted_regions: 被修复区域列表，每个区域包含百分比坐标：
            - left, top, right, bottom: 相对于图片宽高的百分比 (0-100)
            - width_percent, height_percent: 区域宽高占图片的百分比
    """
    import json
    
    # 构建区域信息
    regions_info = ""
    if inpainted_regions and len(inpainted_regions) > 0:
        regions_json = json.dumps(inpainted_regions, ensure_ascii=False, indent=2)
        regions_info = f"""
以下是被抹除工具处理过的具体区域（共 {len(inpainted_regions)} 个矩形区域），请重点修复这些位置：

```json
{regions_json}
```

坐标说明（所有数值都是相对于图片宽高的百分比，范围0-100%）：
- left: 区域左边缘距离图片左边缘的百分比
- top: 区域上边缘距离图片上边缘的百分比  
- right: 区域右边缘距离图片左边缘的百分比
- bottom: 区域下边缘距离图片上边缘的百分比
- width_percent: 区域宽度占图片宽度的百分比
- height_percent: 区域高度占图片高度的百分比

例如：left=10 表示区域从图片左侧10%的位置开始。
"""
    
    prompt = f"""\
你是一位专业的图像修复专家。这张ppt页面图片刚刚经过了文字/对象抹除操作，抹除工具在指定区域留下了一些修复痕迹，包括：
- 色块不均匀、颜色不连贯
- 模糊的斑块或涂抹痕迹
- 与周围背景不协调的区域，比如不和谐的渐变色块
- 可能的纹理断裂或图案不连续
{regions_info}
你的任务是修复这些抹除痕迹，让图片看起来像从未有过对象抹除操作一样自然。

要求：
- **重点修复上述标注的区域**：这些区域刚刚经过抹除处理，需要让它们与周围背景完美融合
- 保持纹理、颜色、图案的连续性
- 提升整体画质，消除模糊、噪点、伪影
- 保持图片的原始构图、布局、色调风格
- 禁止添加任何文字、图表、插画、图案、边框等元素
- 除了上述区域，其他区域不要做任何修改，保持和原图像素级别地一致。
- 输出图片的尺寸必须与原图一致

请输出修复后的高清ppt页面背景图片，不要遗漏修复任何一个被涂抹的区域。
"""
#     prompt = f"""
# 你是一位专业的图像修复专家。请你修复上传的图像，去除其中的涂抹痕迹，消除所有的模糊、噪点、伪影，输出处理后的高清图像，其他区域保持和原图**完全相同**，颜色、布局、线条、装饰需要完全一致.
# {regions_info}
# """
    return prompt
