# 提示词中的 Few-Shot 示例清单

本文档列出了 `prompts.py` 中所有包含 few-shot 示例的部分。

---

## 📋 目录

1. [风格指令生成示例](#1-风格指令生成示例)
2. [大纲结构格式示例](#2-大纲结构格式示例)
3. [描述文本切分示例](#3-描述文本切分示例)
4. [页面描述格式示例](#4-页面描述格式示例)
5. [大纲修改格式示例](#5-大纲修改格式示例)
6. [页面描述修改示例](#6-页面描述修改示例)
7. [文字属性提取示例](#7-文字属性提取示例)
8. [批量文字属性提取示例](#8-批量文字属性提取示例)
9. [图片 URL 格式示例](#9-图片-url-格式示例)

---

## 1. 风格指令生成示例

### 位置
- `get_outline_generation_prompt()` (第150-156行)
- `get_outline_parsing_prompt()` (第247-253行)
- `get_description_to_outline_prompt()` (第708-714行)

### 示例内容

```json
{
  "style_instructions": {
    "design_aesthetic": "在此基础上，详细描述整体风格。参考示例：\"计算野兽派\"与\"精密工程学\"的结合。风格冷峻、理性，强调数据结构的美感。视觉隐喻应围绕\"信息压缩\"、\"切片\"和\"流体动力学\"展开。整体感觉像是一份来自未来的、针对语言模型经济学的解密报告。",
    "background_color": "背景色描述及十六进制代码。参考示例：深空灰 (Deep Space Grey), #1A1A1A。这为高亮数据提供了极佳的对比度，减少屏幕眩光，适合深度阅读。",
    "primary_font": "标题字体名称及使用说明。参考示例：Helvetica Now Display (Bold/Black)。用于极具冲击力的标题，字间距紧凑，传达权威感。",
    "secondary_font": "正文字体名称及使用说明。参考示例：JetBrains Mono。一种为代码和数据设计的等宽字体，用于正文、标注和数据点，强化\"计算\"和\"工程\"的语境。",
    "primary_text_color": "主要文字颜色描述及十六进制代码。参考示例：雾白 (Mist White), #E0E0E0。",
    "accent_color": "强调色描述及十六进制代码，用于高光、图表和关键元素。参考示例：信号橙 (Signal Orange), #FF5722 (代表成本/警示) 和 荧光青 (Cyber Cyan), #00BCD4 (代表效率/DeepSeek)。",
    "visual_elements": "视觉元素的详细描述。参考示例：细如发丝的白色网格线作为背景纹理。使用半透明的几何体表示\"令牌(Token)\"。图表应采用极简的线图或热力图风格。避免任何装饰性的插画，一切元素必须服务于数据表达。"
  }
}
```

### 说明
这些示例出现在 JSON 格式模板中，用于指导 AI 生成风格指令。每个字段都包含一个具体的参考示例，展示期望的输出格式和详细程度。

---

## 2. 大纲结构格式示例

### 位置
- `get_outline_generation_prompt()` (第169-181行)
- `get_outline_parsing_prompt()` (第264-278行)
- `get_description_to_outline_prompt()` (第725-739行)
- `get_outline_refinement_prompt()` (第947-966行)

### 示例内容

#### 简单格式（适用于短PPT）
```json
"outline": [{"title": "标题1", "points": ["要点1", "要点2"]}, {"title": "标题2", "points": ["要点1", "要点2"]}]
```

#### 分章节格式（适用于长PPT）
```json
"outline": [
    {
    "part": "第一部分：引言",
    "pages": [
        {"title": "欢迎", "points": ["要点1", "要点2"]},
        {"title": "概述", "points": ["要点1", "要点2"]}
    ]
    }
]
```

### 说明
展示两种大纲格式：简单格式用于短PPT，分章节格式用于长PPT。

---

## 3. 描述文本切分示例

### 位置
- `get_description_split_prompt()` (第798-803行)

### 示例内容

```
Example output format:
[
    "页面标题：人工智能的诞生\n页面文字：\n- 1950 年，图灵提出\"图灵测试\"...",
    "页面标题：AI 的发展历程\n页面文字：\n- 1950年代：符号主义...",
    ...
]
```

### 说明
展示如何将完整的描述文本切分为多个页面描述，每个元素是一个字符串，包含页面标题和页面文字。

---

## 4. 页面描述格式示例

### 位置
- `get_description_format_prompt()` (第853-857行)

### 示例内容

```json
[
  "幻灯片 1：封面 (The Cover)\n// NARRATIVE GOAL (叙事目标)\n[详细解释这张幻灯片在整个故事弧光中的具体叙事目的]\n\n// KEY CONTENT (关键内容)\n主标题：[叙事性主题句]\n副标题：[简洁有力的副标题]\n页面文字：\n- [要点1]\n- [要点2]\n\n// VISUAL (视觉画面)\n[详细描述支持该观点的视觉元素，使用建筑图纸/蓝图风格的视觉隐喻。描述核心视觉元素、背景底纹、视觉隐喻、动态感等]\n\n// LAYOUT (布局结构)\n[详细描述页面构图和空间安排。描述构图模式、标题排版、视觉重心、留白策略等]",
  "幻灯片 2：[标题]\n// NARRATIVE GOAL (叙事目标)\n[...]\n\n// KEY CONTENT (关键内容)\n[...]\n\n// VISUAL (视觉画面)\n[...]\n\n// LAYOUT (布局结构)\n[...]",
  ...
]
```

### 说明
展示完整的页面描述格式，包含四个部分：NARRATIVE GOAL、KEY CONTENT、VISUAL、LAYOUT。

---

## 5. 大纲修改格式示例

### 位置
- `get_outline_refinement_prompt()` (第947-966行)

### 示例内容

#### 格式1：简单格式
```json
[{"title": "title1", "points": ["point1", "point2"]}, {"title": "title2", "points": ["point1", "point2"]}]
```

#### 格式2：基于章节的格式
```json
[
    {
    "part": "第一部分：引言",
    "pages": [
        {"title": "欢迎", "points": ["point1", "point2"]},
        {"title": "概述", "points": ["point1", "point2"]}
    ]
    },
    {
    "part": "第二部分：主要内容",
    "pages": [
        {"title": "主题1", "points": ["point1", "point2"]},
        {"title": "主题2", "points": ["point1", "point2"]}
    ]
    }
]
```

### 说明
展示修改大纲时的两种输出格式，与大纲生成时的格式相同。

---

## 6. 页面描述修改示例

### 位置
- `get_descriptions_refinement_prompt()` (第1070-1075行)

### 示例内容

```
示例输出格式：
[
    "页面标题：人工智能的诞生\n页面文字：\n- 1950 年，图灵提出\"图灵测试\"...",
    "页面标题：AI 的发展历程\n页面文字：\n- 1950年代：符号主义...",
    ...
]
```

### 说明
展示修改页面描述时的输出格式，与描述文本切分的格式相同。

---

## 7. 文字属性提取示例

### 位置
- `get_text_attribute_extraction_prompt()` (第1143-1155行)

### 示例内容

```json
{
    "colored_segments": [
        {"text": "·  创新合成", "color": "#000000"},
        {"text": "1827个任务环境", "color": "#26397A"},
        {"text": "与", "color": "#000000"},
        {"text": "8.5万提示词", "color": "#26397A"},
        {"text": "突破数据瓶颈", "color": "#000000"},
        {"text": "x^2 + y^2 = z^2", "color": "#FF0000", "is_latex": true}
    ]
}
```

### 说明
展示文字属性提取的输出格式，包括：
- 文字内容
- 颜色（十六进制格式）
- LaTeX 公式标记（`is_latex` 字段）

---

## 8. 批量文字属性提取示例

### 位置
- `get_batch_text_attribute_extraction_prompt()` (第1215-1229行)

### 示例内容

```json
[
    {
        "element_id": "xxx",
        "text_content": "文字内容",
        "font_color": "#RRGGBB",
        "is_bold": true/false,
        "is_italic": true/false,
        "is_underline": true/false,
        "text_alignment": "对齐方式"
    },
    ...
]
```

### 说明
展示批量文字属性提取的输出格式，包含：
- `element_id`: 元素唯一标识
- `text_content`: 文字内容
- `font_color`: 颜色十六进制值
- `is_bold`: 是否为粗体
- `is_italic`: 是否为斜体
- `is_underline`: 是否有下划线
- `text_alignment`: 对齐方式

---

## 9. 图片 URL 格式示例

### 位置
- `get_descriptions_refinement_prompt()` (第1066行)

### 示例内容

```
提示：如果参考文件中包含以 /files/ 开头的本地文件URL图片（例如 /files/mineru/xxx/image.png），请将这些图片以markdown格式输出，例如：![图片描述](/files/mineru/xxx/image.png)，而不是作为普通文本。
```

### 说明
展示如何将本地文件 URL 图片转换为 markdown 格式。

---

## 📊 总结

### Few-Shot 示例统计

| 函数名 | 示例数量 | 示例类型 |
|--------|---------|---------|
| `get_outline_generation_prompt()` | 2组 | 风格指令、大纲格式 |
| `get_outline_parsing_prompt()` | 2组 | 风格指令、大纲格式 |
| `get_description_to_outline_prompt()` | 2组 | 风格指令、大纲格式 |
| `get_description_split_prompt()` | 1组 | 输出格式 |
| `get_description_format_prompt()` | 1组 | 输出格式 |
| `get_outline_refinement_prompt()` | 1组 | 输出格式 |
| `get_descriptions_refinement_prompt()` | 2组 | 输出格式、图片URL |
| `get_text_attribute_extraction_prompt()` | 1组 | 输出格式 |
| `get_batch_text_attribute_extraction_prompt()` | 1组 | 输出格式 |

### 示例类型分类

1. **风格指令示例** (3处)
   - `design_aesthetic`
   - `background_color`
   - `primary_font`
   - `secondary_font`
   - `primary_text_color`
   - `accent_color`
   - `visual_elements`

2. **大纲格式示例** (4处)
   - 简单格式
   - 分章节格式

3. **描述格式示例** (3处)
   - 页面描述切分格式
   - 页面描述完整格式（包含4部分）
   - 页面描述修改格式

4. **文字属性示例** (2处)
   - 单个文字属性提取
   - 批量文字属性提取

5. **其他示例** (1处)
   - 图片 URL markdown 格式

---

**文档版本**：v1.0.0  
**最后更新**：2024年1月



