"""
AI Service - handles all AI model interactions
Based on demo.py and gemini_genai.py
TODO: use structured output API
"""
import os
import json
import re
import logging
import requests
from typing import List, Dict, Optional, Union
from textwrap import dedent
from PIL import Image
from tenacity import retry, stop_after_attempt, retry_if_exception_type
from .prompts import (
    get_outline_generation_prompt,
    get_outline_parsing_prompt,
    get_page_description_prompt,
    get_image_generation_prompt,
    get_image_edit_prompt,
    get_description_to_outline_prompt,
    get_description_split_prompt,
    get_description_format_prompt,
    get_outline_refinement_prompt,
    get_descriptions_refinement_prompt
)
from .ai_providers import get_text_provider, get_image_provider, TextProvider, ImageProvider
from config import get_config

logger = logging.getLogger(__name__)


class ProjectContext:
    """项目上下文数据类，统一管理 AI 需要的所有项目信息"""
    
    def __init__(self, project_or_dict, reference_files_content: Optional[List[Dict[str, str]]] = None):
        """
        Args:
            project_or_dict: 项目对象（Project model）或项目字典（project.to_dict()）
            reference_files_content: 参考文件内容列表
        """
        # 支持直接传入 Project 对象，避免 to_dict() 调用，提升性能
        if hasattr(project_or_dict, 'idea_prompt'):
            # 是 Project 对象
            self.idea_prompt = project_or_dict.idea_prompt
            self.outline_text = project_or_dict.outline_text
            self.description_text = project_or_dict.description_text
            self.creation_type = project_or_dict.creation_type or 'idea'
        else:
            # 是字典
            self.idea_prompt = project_or_dict.get('idea_prompt')
            self.outline_text = project_or_dict.get('outline_text')
            self.description_text = project_or_dict.get('description_text')
            self.creation_type = project_or_dict.get('creation_type', 'idea')
        
        self.reference_files_content = reference_files_content or []
    
    def to_dict(self) -> Dict:
        """转换为字典，方便传递"""
        return {
            'idea_prompt': self.idea_prompt,
            'outline_text': self.outline_text,
            'description_text': self.description_text,
            'creation_type': self.creation_type,
            'reference_files_content': self.reference_files_content
        }


class AIService:
    """Service for AI model interactions using pluggable providers"""
    
    def __init__(self, text_provider: TextProvider = None, image_provider: ImageProvider = None):
        """
        Initialize AI service with providers
        
        Args:
            text_provider: Optional pre-configured TextProvider. If None, created from factory.
            image_provider: Optional pre-configured ImageProvider. If None, created from factory.
        """
        config = get_config()

        # 优先使用 Flask app.config（可由 Settings 覆盖），否则回退到 Config 默认值
        try:
            from flask import current_app, has_app_context
        except ImportError:
            current_app = None  # type: ignore
            has_app_context = lambda: False  # type: ignore

        if has_app_context() and current_app and hasattr(current_app, "config"):
            self.text_model = current_app.config.get("TEXT_MODEL", config.TEXT_MODEL)
            self.image_model = current_app.config.get("IMAGE_MODEL", config.IMAGE_MODEL)
        else:
            self.text_model = config.TEXT_MODEL
            self.image_model = config.IMAGE_MODEL
        
        # Use provided providers or create from factory based on AI_PROVIDER_FORMAT (from Flask config or env var)
        self.text_provider = text_provider or get_text_provider(model=self.text_model)
        self.image_provider = image_provider or get_image_provider(model=self.image_model)
    
    @staticmethod
    def extract_image_urls_from_markdown(text: str) -> List[str]:
        """
        从 markdown 文本中提取图片 URL
        
        Args:
            text: Markdown 文本，可能包含 ![](url) 格式的图片
            
        Returns:
            图片 URL 列表（包括 http/https URL 和 /files/ 开头的本地路径）
        """
        if not text:
            return []
        
        # 匹配 markdown 图片语法: ![](url) 或 ![alt](url)
        pattern = r'!\[.*?\]\((.*?)\)'
        matches = re.findall(pattern, text)
        
        # 过滤掉空字符串，支持 http/https URL 和 /files/ 开头的本地路径（包括 mineru、materials 等）
        urls = []
        for url in matches:
            url = url.strip()
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('/files/')):
                urls.append(url)
        
        return urls
    
    @staticmethod
    def remove_markdown_images(text: str) -> str:
        """
        从文本中移除 Markdown 图片链接，只保留 alt text（描述文字）
        
        Args:
            text: 包含 Markdown 图片语法的文本
            
        Returns:
            移除图片链接后的文本，保留描述文字
        """
        if not text:
            return text
        
        # 将 ![描述文字](url) 替换为 描述文字
        # 如果没有描述文字（空的 alt text），则完全删除该图片链接
        def replace_image(match):
            alt_text = match.group(1).strip()
            # 如果有描述文字，保留它；否则删除整个链接
            return alt_text if alt_text else ''
        
        pattern = r'!\[(.*?)\]\([^\)]+\)'
        cleaned_text = re.sub(pattern, replace_image, text)
        
        # 清理可能产生的多余空行
        cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)
        
        return cleaned_text
    
    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((json.JSONDecodeError, ValueError)),
        reraise=True
    )
    def generate_json(self, prompt: str, thinking_budget: int = 1000) -> Union[Dict, List]:
        """
        生成并解析JSON，如果解析失败则重新生成
        
        Args:
            prompt: 生成提示词
            thinking_budget: 思考预算
            
        Returns:
            解析后的JSON对象（字典或列表）
            
        Raises:
            json.JSONDecodeError: JSON解析失败（重试3次后仍失败）
        """
        # 调用AI生成文本
        response_text = self.text_provider.generate_text(prompt, thinking_budget=thinking_budget)
        
        # 清理响应文本：移除markdown代码块标记和多余空白
        cleaned_text = response_text.strip().strip("```json").strip("```").strip()
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败，将重新生成。原始文本: {cleaned_text[:200]}... 错误: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((json.JSONDecodeError, ValueError)),
        reraise=True
    )
    def generate_json_with_image(self, prompt: str, image_path: str, thinking_budget: int = 1000) -> Union[Dict, List]:
        """
        带图片输入的JSON生成，如果解析失败则重新生成（最多重试3次）
        
        Args:
            prompt: 生成提示词
            image_path: 图片文件路径
            thinking_budget: 思考预算
            
        Returns:
            解析后的JSON对象（字典或列表）
            
        Raises:
            json.JSONDecodeError: JSON解析失败（重试3次后仍失败）
            ValueError: text_provider 不支持图片输入
        """
        # 调用AI生成文本（带图片）
        if hasattr(self.text_provider, 'generate_with_image'):
            response_text = self.text_provider.generate_with_image(
                prompt=prompt,
                image_path=image_path,
                thinking_budget=thinking_budget
            )
        elif hasattr(self.text_provider, 'generate_text_with_images'):
            response_text = self.text_provider.generate_text_with_images(
                prompt=prompt,
                images=[image_path],
                thinking_budget=thinking_budget
            )
        else:
            raise ValueError("text_provider 不支持图片输入")
        
        # 清理响应文本：移除markdown代码块标记和多余空白
        cleaned_text = response_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败（带图片），将重新生成。原始文本: {cleaned_text[:200]}... 错误: {str(e)}")
            raise
    
    @staticmethod
    def _convert_mineru_path_to_local(mineru_path: str) -> Optional[str]:
        """
        将 /files/mineru/{extract_id}/{rel_path} 格式的路径转换为本地文件系统路径（支持前缀匹配）
        
        Args:
            mineru_path: MinerU URL 路径，格式为 /files/mineru/{extract_id}/{rel_path}
            
        Returns:
            本地文件系统路径，如果转换失败则返回 None
        """
        from utils.path_utils import find_mineru_file_with_prefix
        
        matched_path = find_mineru_file_with_prefix(mineru_path)
        return str(matched_path) if matched_path else None
    
    @staticmethod
    def download_image_from_url(url: str) -> Optional[Image.Image]:
        """
        从 URL 下载图片并返回 PIL Image 对象
        
        Args:
            url: 图片 URL
            
        Returns:
            PIL Image 对象，如果下载失败则返回 None
        """
        try:
            logger.debug(f"Downloading image from URL: {url}")
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 从响应内容创建 PIL Image
            image = Image.open(response.raw)
            # 确保图片被加载
            image.load()
            logger.debug(f"Successfully downloaded image: {image.size}, {image.mode}")
            return image
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {str(e)}")
            return None
    
    def generate_outline(self, project_context: ProjectContext, language: str = None) -> tuple:
        """
        Generate PPT outline from idea prompt, including style instructions
        Based on demo.py gen_outline()
        
        Args:
            project_context: 项目上下文对象，包含所有原始信息
            
        Returns:
            tuple: (outline, style_instructions)
                - outline: List of outline items (may contain parts with pages or direct pages)
                - style_instructions: Dict with design aesthetic, colors, fonts, etc.
        """
        outline_prompt = get_outline_generation_prompt(project_context, language)
        result = self.generate_json(outline_prompt, thinking_budget=1000)
        
        # 解析新格式：{ "style_instructions": {...}, "outline": [...] }
        outline, style_instructions = self._extract_outline_and_style(result)
        return outline, style_instructions
    
    def parse_outline_text(self, project_context: ProjectContext, language: str = None) -> tuple:
        """
        Parse user-provided outline text into structured outline format, including style instructions
        This method analyzes the text and splits it into pages without modifying the original text
        
        Args:
            project_context: 项目上下文对象，包含所有原始信息
        
        Returns:
            tuple: (outline, style_instructions)
                - outline: List of outline items (may contain parts with pages or direct pages)
                - style_instructions: Dict with design aesthetic, colors, fonts, etc.
        """
        parse_prompt = get_outline_parsing_prompt(project_context, language)
        result = self.generate_json(parse_prompt, thinking_budget=1000)
        
        # 解析新格式：{ "style_instructions": {...}, "outline": [...] }
        outline, style_instructions = self._extract_outline_and_style(result)
        return outline, style_instructions
    
    def _extract_outline_and_style(self, result) -> tuple:
        """
        从AI返回结果中提取大纲和风格指令
        
        Args:
            result: AI返回的JSON结果，可能是新格式或旧格式
            
        Returns:
            tuple: (outline, style_instructions)
        """
        # 新格式：{ "style_instructions": {...}, "outline": [...] }
        if isinstance(result, dict) and 'outline' in result:
            outline = result.get('outline', [])
            style_instructions = result.get('style_instructions', {})
            return outline, style_instructions
        
        # 旧格式：直接返回数组（向后兼容）
        if isinstance(result, list):
            return result, {}
        
        # 其他情况，返回空
        logger.warning(f"Unexpected outline format: {type(result)}")
        return [], {}
    
    def flatten_outline(self, outline: List[Dict]) -> List[Dict]:
        """
        Flatten outline structure to page list
        Based on demo.py flatten_outline()
        """
        pages = []
        for item in outline:
            if "part" in item and "pages" in item:
                # This is a part, expand its pages
                for page in item["pages"]:
                    page_with_part = page.copy()
                    page_with_part["part"] = item["part"]
                    pages.append(page_with_part)
            else:
                # This is a direct page
                pages.append(item)
        return pages
    
    def generate_page_description(self, project_context: ProjectContext, outline: List[Dict], 
                                 page_outline: Dict, page_index: int, language='zh',
                                 style_instructions: dict = None, total_pages: int = None) -> str:
        """
        Generate description for a single page
        Based on demo.py gen_desc() logic
        
        Args:
            project_context: 项目上下文对象，包含所有原始信息
            outline: Complete outline
            page_outline: Outline for this specific page
            page_index: Page number (1-indexed)
            style_instructions: 全局风格指令（可选）
            total_pages: 总页数（可选，用于识别最后一页）
        
        Returns:
            Text description for the page
        """
        part_info = f"\nThis page belongs to: {page_outline['part']}" if 'part' in page_outline else ""
        
        desc_prompt = get_page_description_prompt(
            project_context=project_context,
            outline=outline,
            page_outline=page_outline,
            page_index=page_index,
            part_info=part_info,
            language=language,
            style_instructions=style_instructions,
            total_pages=total_pages
        )
        
        response_text = self.text_provider.generate_text(desc_prompt, thinking_budget=1000)
        
        return dedent(response_text)
    
    def generate_outline_text(self, outline: List[Dict]) -> str:
        """
        Convert outline to text format for prompts
        Based on demo.py gen_outline_text()
        """
        text_parts = []
        for i, item in enumerate(outline, 1):
            if "part" in item and "pages" in item:
                text_parts.append(f"{i}. {item['part']}")
            else:
                text_parts.append(f"{i}. {item.get('title', 'Untitled')}")
        result = "\n".join(text_parts)
        return dedent(result)
    
    def generate_image_prompt(self, outline: List[Dict], page: Dict, 
                            page_desc: str, page_index: int, 
                            has_material_images: bool = False,
                            extra_requirements: Optional[str] = None,
                            language='zh',
                            has_template: bool = True,
                            style_instructions: dict = None,
                            total_pages: int = None) -> str:
        """
        Generate image generation prompt for a page
        Based on demo.py gen_prompts()
        
        Args:
            outline: Complete outline
            page: Page outline data
            page_desc: Page description text
            page_index: Page number (1-indexed)
            has_material_images: 是否有素材图片（从项目描述中提取的图片）
            extra_requirements: Optional extra requirements to apply to all pages
            language: Output language
            has_template: 是否有模板图片（False表示无模板图模式）
            style_instructions: 全局风格指令（可选）
            total_pages: 总页数（可选，用于识别最后一页）
        
        Returns:
            Image generation prompt
        """
        outline_text = self.generate_outline_text(outline)
        
        # Determine current section
        if 'part' in page:
            current_section = page['part']
        else:
            current_section = f"{page.get('title', 'Untitled')}"
        
        # 在传给文生图模型之前，移除 Markdown 图片链接
        # 图片本身已经通过 additional_ref_images 传递，只保留文字描述
        cleaned_page_desc = self.remove_markdown_images(page_desc)
        
        prompt = get_image_generation_prompt(
            page_desc=cleaned_page_desc,
            outline_text=outline_text,
            current_section=current_section,
            has_material_images=has_material_images,
            extra_requirements=extra_requirements,
            language=language,
            has_template=has_template,
            page_index=page_index,
            style_instructions=style_instructions,
            total_pages=total_pages
        )
        
        return prompt
    
    def generate_image(self, prompt: str, ref_image_path: Optional[str] = None, 
                      aspect_ratio: str = "16:9", resolution: str = "2K",
                      additional_ref_images: Optional[List[Union[str, Image.Image]]] = None) -> Optional[Image.Image]:
        """
        Generate image using configured image provider
        Based on gemini_genai.py gen_image()
        
        Args:
            prompt: Image generation prompt
            ref_image_path: Path to reference image (optional). If None, will generate based on prompt only.
            aspect_ratio: Image aspect ratio
            resolution: Image resolution (note: OpenAI format only supports 1K)
            additional_ref_images: 额外的参考图片列表，可以是本地路径、URL 或 PIL Image 对象
        
        Returns:
            PIL Image object or None if failed
        
        Raises:
            Exception with detailed error message if generation fails
        """
        try:
            logger.debug(f"Reference image: {ref_image_path}")
            if additional_ref_images:
                logger.debug(f"Additional reference images: {len(additional_ref_images)}")
            logger.debug(f"Config - aspect_ratio: {aspect_ratio}, resolution: {resolution}")

            # 构建参考图片列表
            ref_images = []
            
            # 添加主参考图片（如果提供了路径）
            if ref_image_path:
                if not os.path.exists(ref_image_path):
                    raise FileNotFoundError(f"Reference image not found: {ref_image_path}")
                main_ref_image = Image.open(ref_image_path)
                ref_images.append(main_ref_image)
            
            # 添加额外的参考图片
            if additional_ref_images:
                for ref_img in additional_ref_images:
                    if isinstance(ref_img, Image.Image):
                        # 已经是 PIL Image 对象
                        ref_images.append(ref_img)
                    elif isinstance(ref_img, str):
                        # 可能是本地路径或 URL
                        if os.path.exists(ref_img):
                            # 本地路径
                            ref_images.append(Image.open(ref_img))
                        elif ref_img.startswith('http://') or ref_img.startswith('https://'):
                            # URL，需要下载
                            downloaded_img = self.download_image_from_url(ref_img)
                            if downloaded_img:
                                ref_images.append(downloaded_img)
                            else:
                                logger.warning(f"Failed to download image from URL: {ref_img}, skipping...")
                        elif ref_img.startswith('/files/mineru/'):
                            # MinerU 本地文件路径，需要转换为文件系统路径（支持前缀匹配）
                            local_path = self._convert_mineru_path_to_local(ref_img)
                            if local_path and os.path.exists(local_path):
                                ref_images.append(Image.open(local_path))
                                logger.debug(f"Loaded MinerU image from local path: {local_path}")
                            else:
                                logger.warning(f"MinerU image file not found (with prefix matching): {ref_img}, skipping...")
                        else:
                            logger.warning(f"Invalid image reference: {ref_img}, skipping...")
            
            logger.debug(f"Calling image provider for generation with {len(ref_images)} reference images...")
            
            # 使用 image_provider 生成图片
            return self.image_provider.generate_image(
                prompt=prompt,
                ref_images=ref_images if ref_images else None,
                aspect_ratio=aspect_ratio,
                resolution=resolution
            )
            
        except Exception as e:
            error_detail = f"Error generating image: {type(e).__name__}: {str(e)}"
            logger.error(error_detail, exc_info=True)
            raise Exception(error_detail) from e
    
    def edit_image(self, prompt: str, current_image_path: str,
                  aspect_ratio: str = "16:9", resolution: str = "2K",
                  original_description: str = None,
                  additional_ref_images: Optional[List[Union[str, Image.Image]]] = None) -> Optional[Image.Image]:
        """
        Edit existing image with natural language instruction
        Uses current image as reference
        
        Args:
            prompt: Edit instruction
            current_image_path: Path to current page image
            aspect_ratio: Image aspect ratio
            resolution: Image resolution
            original_description: Original page description to include in prompt
            additional_ref_images: 额外的参考图片列表，可以是本地路径、URL 或 PIL Image 对象
        
        Returns:
            PIL Image object or None if failed
        """
        # Build edit instruction with original description if available
        edit_instruction = get_image_edit_prompt(
            edit_instruction=prompt,
            original_description=original_description
        )
        return self.generate_image(edit_instruction, current_image_path, aspect_ratio, resolution, additional_ref_images)
    
    def parse_description_to_outline(self, project_context: ProjectContext, language='zh') -> tuple:
        """
        从描述文本解析出大纲结构，包括风格指令
        
        Args:
            project_context: 项目上下文对象，包含所有原始信息
        
        Returns:
            tuple: (outline, style_instructions)
                - outline: List of outline items (may contain parts with pages or direct pages)
                - style_instructions: Dict with design aesthetic, colors, fonts, etc.
        """
        parse_prompt = get_description_to_outline_prompt(project_context, language)
        result = self.generate_json(parse_prompt, thinking_budget=1000)
        
        # 解析新格式：{ "style_instructions": {...}, "outline": [...] }
        outline, style_instructions = self._extract_outline_and_style(result)
        return outline, style_instructions
    
    @staticmethod
    def _detect_formatted_description(description_text: str) -> bool:
        """
        检测描述文本是否符合格式化结构（包含页面标记和描述部分）
        
        支持多种格式变体：
        - "幻灯片 X："或"Slide X:"
        - 中文标签："叙事目标"、"视觉画面"、"布局结构"、"关键内容"
        - 英文标签："NARRATIVE GOAL"、"VISUAL"、"LAYOUT"、"KEY CONTENT"
        
        Args:
            description_text: 描述文本
            
        Returns:
            bool: 如果符合格式返回True，否则返回False
        """
        # 清理文本：移除可能的三引号包围
        text = description_text.strip()
        if text.startswith('"""') and text.endswith('"""'):
            text = text[3:-3].strip()
        elif text.startswith("'''") and text.endswith("'''"):
            text = text[3:-3].strip()
        
        # 检测页面标记（支持多种格式）
        slide_patterns = [
            r'幻灯片\s*\d+[:：]',  # 幻灯片 1：
            r'Slide\s*\d+[:：]',   # Slide 1:
            r'SLIDE\s*\d+[:：]',   # SLIDE 1:
            r'第\s*\d+\s*[页张]',  # 第1页、第1张
            r'Page\s*\d+[:：]',    # Page 1:
        ]
        has_slide_marker = any(re.search(pattern, text, re.IGNORECASE) for pattern in slide_patterns)
        
        # 检测描述部分标记（支持中英文）
        # 中文标签
        chinese_markers = [
            r'叙事目标',
            r'视觉画面',
            r'布局结构',
            r'关键内容',
        ]
        # 英文标签（支持 // 前缀或直接使用）
        english_markers = [
            r'//\s*NARRATIVE\s+GOAL',
            r'//\s*KEY\s+CONTENT',
            r'//\s*VISUAL',
            r'//\s*LAYOUT',
            r'NARRATIVE\s+GOAL',
            r'KEY\s+CONTENT',
        ]
        
        has_chinese_marker = any(re.search(marker, text) for marker in chinese_markers)
        has_english_marker = any(re.search(marker, text, re.IGNORECASE) for marker in english_markers)
        
        # 如果包含页面标记和至少一个描述部分标记，认为符合格式
        return has_slide_marker and (has_chinese_marker or has_english_marker)
    
    @staticmethod
    def _parse_formatted_description(description_text: str) -> List[str]:
        """
        解析格式化描述文本，切分为每页描述
        
        支持多种格式变体：
        - "幻灯片 X："、"Slide X:"、"第X页"等
        - 支持章节标题（如"第一部分：..."）
        
        Args:
            description_text: 格式化描述文本
            
        Returns:
            List[str]: 每页描述列表
        """
        # 清理文本：移除可能的三引号包围
        text = description_text.strip()
        if text.startswith('"""') and text.endswith('"""'):
            text = text[3:-3].strip()
        elif text.startswith("'''") and text.endswith("'''"):
            text = text[3:-3].strip()
        
        pages = []
        
        # 支持多种页面标记格式（带捕获组的模式，用于提取标题）
        slide_patterns = [
            (r'幻灯片\s*(\d+)[:：]\s*([^\n]*)', '幻灯片'),  # 幻灯片 1：标题
            (r'Slide\s*(\d+)[:：]\s*([^\n]*)', 'Slide'),   # Slide 1: Title
            (r'SLIDE\s*(\d+)[:：]\s*([^\n]*)', 'SLIDE'),    # SLIDE 1: TITLE
            (r'第\s*(\d+)\s*[页张][:：]?\s*([^\n]*)', '第'), # 第1页：标题
            (r'Page\s*(\d+)[:：]\s*([^\n]*)', 'Page'),     # Page 1: Title
        ]
        
        # 尝试所有模式，找到匹配的
        slide_matches = []
        matched_prefix = None
        for pattern, prefix in slide_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                slide_matches = matches
                matched_prefix = prefix
                logger.debug(f"使用页面标记模式: {prefix}, 找到 {len(matches)} 个匹配")
                break
        
        if not slide_matches:
            # 如果没有找到标准页面标记，尝试查找章节标题后的第一个页面
            # 例如："第一部分：绪论\nSlide 1: 封面"
            chapter_pattern = r'第[一二三四五六七八九十\d]+部分[:：]'
            chapter_match = re.search(chapter_pattern, text)
            if chapter_match:
                # 从章节标题后开始查找页面标记
                text_after_chapter = text[chapter_match.end():]
                offset = chapter_match.end()
                for pattern, prefix in slide_patterns:
                    matches = list(re.finditer(pattern, text_after_chapter, re.IGNORECASE))
                    if matches:
                        # 创建调整位置后的匹配对象
                        class AdjustedMatch:
                            def __init__(self, match, offset):
                                self._match = match
                                self._offset = offset
                            def start(self):
                                return self._match.start() + self._offset
                            def end(self):
                                return self._match.end() + self._offset
                            def group(self, *args):
                                return self._match.group(*args)
                        
                        slide_matches = [AdjustedMatch(m, offset) for m in matches]
                        matched_prefix = prefix
                        logger.debug(f"在章节后找到页面标记: {prefix}, 找到 {len(matches)} 个匹配")
                        break
        
        if not slide_matches:
            # 如果仍然没有找到，可能是单页描述或格式完全不同
            logger.warning("未找到页面标记，返回整个文本作为单页描述")
            return [text]
        
        # 为每页提取内容（从当前标记到下一个标记之间）
        for i, match in enumerate(slide_matches):
            start_pos = match.start()
            
            # 确定结束位置（下一个幻灯片标记的位置，或文本末尾）
            if i + 1 < len(slide_matches):
                end_pos = slide_matches[i + 1].start()
            else:
                end_pos = len(text)
            
            # 提取这一页的内容
            page_content = text[start_pos:end_pos].strip()
            
            if page_content:
                pages.append(page_content)
        
        return pages if pages else [text]
    
    def parse_description_to_page_descriptions(self, project_context: ProjectContext, 
                                               outline: List[Dict],
                                               language='zh') -> List[str]:
        """
        从描述文本切分出每页描述
        
        如果描述文本符合格式化结构（包含"幻灯片 X："和四个部分），直接切分。
        否则，使用AI生成符合格式的描述。
        
        Args:
            project_context: 项目上下文对象，包含所有原始信息
            outline: 已解析出的大纲结构
        
        Returns:
            List[str]: 每页描述列表，每个描述包含四个部分（NARRATIVE GOAL, KEY CONTENT, VISUAL, LAYOUT）
        """
        description_text = project_context.description_text or ""
        
        # 检测是否符合格式化结构
        if self._detect_formatted_description(description_text):
            logger.info("检测到格式化描述文本，直接切分...")
            pages = self._parse_formatted_description(description_text)
            
            # 验证页数是否匹配
            expected_pages = len(self.flatten_outline(outline))
            if len(pages) == expected_pages:
                logger.info(f"成功切分 {len(pages)} 页描述")
                return pages
            else:
                logger.warning(f"切分页数不匹配: 期望 {expected_pages} 页，实际 {len(pages)} 页。将使用AI生成。")
                # 页数不匹配时，继续使用AI生成
        
        # 不符合格式或页数不匹配，使用AI生成符合格式的描述
        logger.info("描述文本不符合格式或页数不匹配，使用AI生成符合格式的描述...")
        formatted_prompt = get_description_format_prompt(project_context, outline, language)
        descriptions = self.generate_json(formatted_prompt, thinking_budget=1500)
        
        # 确保返回的是字符串列表
        if isinstance(descriptions, list):
            return [str(desc) for desc in descriptions]
        else:
            raise ValueError("Expected a list of page descriptions, but got: " + str(type(descriptions)))
    
    def refine_outline(self, current_outline: List[Dict], user_requirement: str,
                      project_context: ProjectContext,
                      previous_requirements: Optional[List[str]] = None,
                      language='zh') -> List[Dict]:
        """
        根据用户要求修改已有大纲
        
        Args:
            current_outline: 当前的大纲结构
            user_requirement: 用户的新要求
            project_context: 项目上下文对象，包含所有原始信息
            previous_requirements: 之前的修改要求列表（可选）
        
        Returns:
            修改后的大纲结构
        """
        refinement_prompt = get_outline_refinement_prompt(
            current_outline=current_outline,
            user_requirement=user_requirement,
            project_context=project_context,
            previous_requirements=previous_requirements,
            language=language
        )
        outline = self.generate_json(refinement_prompt, thinking_budget=1000)
        return outline
    
    def refine_descriptions(self, current_descriptions: List[Dict], user_requirement: str,
                           project_context: ProjectContext,
                           outline: List[Dict] = None,
                           previous_requirements: Optional[List[str]] = None,
                           language='zh') -> List[str]:
        """
        根据用户要求修改已有页面描述
        
        Args:
            current_descriptions: 当前的页面描述列表，每个元素包含 {index, title, description_content}
            user_requirement: 用户的新要求
            project_context: 项目上下文对象，包含所有原始信息
            outline: 完整的大纲结构（可选）
            previous_requirements: 之前的修改要求列表（可选）
        
        Returns:
            修改后的页面描述列表（字符串列表）
        """
        refinement_prompt = get_descriptions_refinement_prompt(
            current_descriptions=current_descriptions,
            user_requirement=user_requirement,
            project_context=project_context,
            outline=outline,
            previous_requirements=previous_requirements,
            language=language
        )
        descriptions = self.generate_json(refinement_prompt, thinking_budget=1000)
        
        # 确保返回的是字符串列表
        if isinstance(descriptions, list):
            return [str(desc) for desc in descriptions]
        else:
            raise ValueError("Expected a list of page descriptions, but got: " + str(type(descriptions)))

