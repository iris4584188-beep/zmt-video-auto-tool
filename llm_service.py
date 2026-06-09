"""LLM 服务：生成分镜表 + 构建分镜图提示词"""

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# =========================
# 1. 环境变量
# =========================

def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _has_api_key() -> bool:
    return bool(_get_env("OPENAI_API_KEY"))


def _get_model() -> str:
    return _get_env("OPENAI_MODEL", "gpt-5.4-mini")


def _get_base_url() -> str:
    return _get_env("OPENAI_BASE_URL", "")


def get_llm_mode() -> str:
    if not _has_api_key() or OpenAI is None:
        return "mock 模式：未配置可用的 OpenAI / 代理 API"
    return f"真实 API 模式：{_get_model()}"


def _get_client():
    if not _has_api_key() or OpenAI is None:
        return None

    kwargs = {
        "api_key": _get_env("OPENAI_API_KEY"),
    }

    base_url = _get_base_url()
    if base_url:
        kwargs["base_url"] = base_url

    return OpenAI(**kwargs)


# =========================
# 2. 基础工具函数
# =========================

def _normalize_reference_type(value: str) -> str:
    value = (value or "").strip().lower()
    if value in ["person", "product", "both", "none"]:
        return value
    return "person"


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _subject_from_reference(has_person_reference: bool, user_idea: str) -> str:
    if "女性" in user_idea or "女生" in user_idea or "女孩" in user_idea:
        return "基于上传人物参考图中的同一位年轻女性人物"

    if "男性" in user_idea or "男生" in user_idea or "男孩" in user_idea:
        return "基于上传人物参考图中的同一位年轻男性人物"

    if has_person_reference:
        return "基于上传人物参考图中的同一位人物"

    return "一位内容创作者"


def _reference_type_for_mock(
    has_person_reference: bool,
    has_product_reference: bool,
) -> str:
    if has_person_reference and has_product_reference:
        return "both"
    if has_person_reference:
        return "person"
    if has_product_reference:
        return "product"
    return "none"


def _call_chat_json(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    client = _get_client()
    if client is None:
        raise RuntimeError("未配置可用的 API Key，无法调用真实 LLM")

    # 代理（api.tu-zi.com）默认返回 SSE 流式格式，必须使用 stream=True
    stream = client.chat.completions.create(
        model=_get_model(),
        temperature=0.7,
        stream=True,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content_parts: List[str] = []
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content_parts.append(chunk.choices[0].delta.content)

    content = "".join(content_parts).strip() or "{}"
    return json.loads(content)


# =========================
# 3. 构建分镜图提示词
# =========================

def build_image_prompt_from_fields(
    shot: Dict[str, Any],
    has_person_reference: bool = False,
    has_product_reference: bool = False,
) -> Dict[str, str]:
    """将分镜表单个镜头转换为 AIGC 分镜图提示词。

    遵循 AGENT_TASK.md 的专业 AIGC 图片制作师逻辑：
    从分镜表中提取 5 个核心维度 —— 主体、主体动作、光影、氛围调性、景别，
    生成可直接用于图片生成大模型的高质量提示词。
    """
    reference_type = _normalize_reference_type(shot.get("reference_type", "person"))

    # --- 提取 5 个核心维度 ---
    subject = _safe_text(shot.get("subject"), "一位内容创作者")
    subject_action = _safe_text(shot.get("subject_action"), "自然站立，面对镜头")
    lighting = _safe_text(shot.get("lighting"), "自然柔光")
    mood = _safe_text(shot.get("mood"), "真实自然，生活感强")
    shot_size = _safe_text(shot.get("shot_size"), "中景")

    negative = _safe_text(
        shot.get("negative_prompt"),
        "不要棚拍摄影光的精致感，不要过度磨皮，不要夸张美颜，不要塑料感，不要人物变形，不要五官漂移，不要水印，不要文字",
    )

    # --- 参考图锁定指令（人物 / 产品） ---
    reference_instructions: List[str] = []

    if has_person_reference and reference_type in ["person", "both"]:
        reference_instructions.append(
            "基于上传人物参考图进行图生图，保持人物身份一致、脸型五官发型一致、气质一致，不改变性别和年龄感"
        )

    if has_product_reference and reference_type in ["product", "both"]:
        reference_instructions.append(
            "画面中产品基于上传产品参考图进行图生图，保持产品包装、颜色、材质、外观形态完全一致"
        )

    # --- 组装中文提示词 ---
    # 风格：专业 AIGC 图片提示词，自然语言描述，非键值对标签式
    cn_core = (
        f"{shot_size}，{subject}，{subject_action}，"
        f"{lighting}，{mood}"
    )

    cn_full_parts: List[str] = []
    if reference_instructions:
        cn_full_parts.append("【参考图锁定】" + "；".join(reference_instructions))
    cn_full_parts.append(cn_core)
    cn_full_parts.append(
        "整体画面为短视频分镜图质感，生活化、自然、纪实感强，适合自媒体视频图生图工作流"
    )
    cn_full_parts.append(f"负面提示词：{negative}")

    image_prompt_cn = "。".join(cn_full_parts) + "。"

    # --- 组装英文提示词 ---
    en_subject = subject
    en_action = subject_action
    en_lighting = lighting
    en_mood = mood
    en_shot_size = shot_size

    en_core = (
        f"{en_shot_size}, {en_subject}, {en_action}, "
        f"{en_lighting}, {en_mood}"
    )

    en_full_parts: List[str] = []

    if has_person_reference and reference_type in ["person", "both"]:
        en_full_parts.append(
            "Reference lock: Use the uploaded person reference image as img2img base. "
            "Keep same person identity, face, facial features, hairstyle, and overall vibe. "
            "Do not change gender or age impression."
        )

    if has_product_reference and reference_type in ["product", "both"]:
        en_full_parts.append(
            "Reference lock: If product appears, use the uploaded product reference image as img2img base. "
            "Keep same packaging, color, material, and appearance."
        )

    en_full_parts.append(en_core)
    en_full_parts.append(
        "Overall visual style: realistic short-video storyboard image, candid, natural, documentary-like, "
        "suitable for social media video production img2img workflow."
    )
    en_full_parts.append(f"Negative prompt: {negative}.")

    image_prompt_en = " ".join(en_full_parts)

    return {
        "image_prompt_cn": image_prompt_cn,
        "image_prompt_en": image_prompt_en,
    }


# =========================
# 4. Mock 分镜表
# =========================

def _mock_storyboard_table(
    user_idea: str,
    selected_video_type_detail: Dict[str, Any],
    shot_count: int,
    has_person_reference: bool,
    has_product_reference: bool,
) -> List[Dict[str, Any]]:
    type_name = _safe_text(selected_video_type_detail.get("type_name"), "通用视频")
    is_no_voiceover = "无口播" in type_name
    is_pure_product = "纯产品展示" in type_name or "沉浸式" in type_name
    subject_text = _subject_from_reference(has_person_reference, user_idea)
    default_reference_type = _reference_type_for_mock(
        has_person_reference,
        has_product_reference,
    )

    # 纯产品展示/沉浸式类型不出现人物
    if is_pure_product:
        subject_text = "产品主体"
        if not has_person_reference:
            default_reference_type = "product" if has_product_reference else "none"

    base_rows = [
        {
            "time_sequence": "开场",
            "subject_action": "产品进入画面，建立场景氛围" if is_pure_product else "出现在镜头中，进入画面并建立场景",
            "scene": "与产品相关的真实生活场景",
            "shot_size": "中景",
            "camera_movement": "手持轻微跟拍",
            "lighting": "自然光",
            "mood": "真实自然，生活感强",
            "subtitle": "开场建立情境，引出用户痛点" if not is_no_voiceover else "",
        },
        {
            "time_sequence": "过程前段",
            "subject_action": "产品特写，展示细节质感" if is_pure_product else "展示产品外观，配合口播引出卖点",
            "scene": "产品使用场景",
            "shot_size": "近景",
            "camera_movement": "缓慢推进",
            "lighting": "自然光与环境光",
            "mood": "专注自然，轻松记录",
            "subtitle": "从痛点引出卖点，场景化表达" if not is_no_voiceover else "",
        },
        {
            "time_sequence": "过程中段",
            "subject_action": "产品使用过程展示，突出核心卖点" if is_pure_product else "展示产品核心功能或使用效果",
            "scene": "产品核心使用场景",
            "shot_size": "中近景",
            "camera_movement": "轻微摇镜或手持感",
            "lighting": "自然光和室内光混合",
            "mood": "真实使用感，产品效果可见",
            "subtitle": "产品介绍，场景化呈现卖点" if not is_no_voiceover else "",
        },
        {
            "time_sequence": "结尾",
            "subject_action": "产品最终效果呈现，收尾" if is_pure_product else "收尾、总结、号召购买",
            "scene": "同一主题场景收尾",
            "shot_size": "中景",
            "camera_movement": "稳定镜头",
            "lighting": "柔和自然光",
            "mood": "轻松满意，完成感",
            "subtitle": "号召购买，促单转化" if not is_no_voiceover else "",
        },
    ]

    rows: List[Dict[str, Any]] = []

    for i in range(shot_count):
        base = base_rows[i % len(base_rows)]

        row = {
            "shot_id": i + 1,
            "time_sequence": base["time_sequence"],
            "subject": subject_text,
            "subject_action": base["subject_action"],
            "scene": base["scene"],
            "shot_size": base["shot_size"],
            "camera_movement": base["camera_movement"],
            "lighting": base["lighting"],
            "mood": base["mood"],
            "subtitle": f"{type_name} - {base['subtitle']}",
            "negative_prompt": "不要棚拍摄影光的精致感，不要过度磨皮，不要夸张美颜，不要塑料感，不要人物变形，不要五官漂移，不要水印，不要文字",
            "reference_type": default_reference_type,
            "video_prompt": "人物动作自然连贯，镜头轻微移动，保持真实短视频质感。",
        }

        row.update(
            build_image_prompt_from_fields(
                row,
                has_person_reference=has_person_reference,
                has_product_reference=has_product_reference,
            )
        )

        rows.append(row)

    return rows[:shot_count]


# =========================
# 5. 主函数：生成分镜表
# =========================

def generate_storyboard_table(
    user_idea: str,
    selected_video_type_detail: Dict[str, Any],
    shot_count: int,
    has_person_reference: bool = False,
    has_product_reference: bool = False,
) -> List[Dict[str, Any]]:
    if not _has_api_key() or OpenAI is None:
        return _mock_storyboard_table(
            user_idea=user_idea,
            selected_video_type_detail=selected_video_type_detail,
            shot_count=shot_count,
            has_person_reference=has_person_reference,
            has_product_reference=has_product_reference,
        )

    subject_rule = _subject_from_reference(has_person_reference, user_idea)
    type_name = _safe_text(selected_video_type_detail.get("type_name"), "通用视频")
    type_description = _safe_text(selected_video_type_detail.get("description"), "")
    type_system_prompt = _safe_text(selected_video_type_detail.get("system_prompt"), "")

    system_prompt = """
你是一个内容电商资深编导，非常懂产品种草型短视频的底层逻辑。
你需要根据用户的模糊需求，结合产品卖点和赛道受众痛点，输出一个适合图生图工作流的分镜表 JSON。

【核心规则】
1. 当前项目逻辑是"底图/参考图 + 分镜提示词 = 分镜图"。
2. 如果用户上传了人物参考图，主体必须默认为"基于上传人物参考图中的同一位人物"。
3. 不要擅自写成男性或女性，除非用户需求里明确写了性别。
4. 如果用户上传了产品参考图，涉及产品时要在 reference_type 中标注 product 或 both。
5. reference_type 只能是：person / product / both / none
6. 字段风格：所有分镜字段（主体、动作、场景、景别、镜头运动、光影、氛围）需使用适合 AI 图片生成场景的提示词风格，具象、画面感强。
7. 社交媒体风格：分镜碎且多、画面钩子强、节奏感强，适合短视频平台。
8. 品类识别：先识别产品所属品类赛道，确保产品使用方法符合产品本身特性。

【口播文案（subtitle 字段）说明】
- 视频类型中如果要求有口播文案，请遵循"痛点→卖点→产品介绍→号召购买"的结构，所有文案必须"场景化"表达。
- 视频类型中如果明确要求"无口播文案"，subtitle 字段留空字符串 ""。
- 口播文案风格示例：不要写"提亮肤色"，要写"涂上它出门，回头率直接拉满"；不要写"大容量电池"，要写"充一次电能让你打游戏一整天不用焦虑电量"。

【输出格式】
6. 输出必须是 JSON 对象，格式如下：
{
  "shots": [
    {
      "shot_id": 1,
      "time_sequence": "...",
      "subject": "...",
      "subject_action": "...",
      "scene": "...",
      "shot_size": "...",
      "camera_movement": "...",
      "lighting": "...",
      "mood": "...",
      "subtitle": "...",
      "negative_prompt": "...",
      "reference_type": "person",
      "video_prompt": "..."
    }
  ]
}
"""

    user_prompt = f"""
用户需求：{user_idea}

【选定的视频类型】{type_name}
【视频类型说明】{type_description}

【视频类型系统要求（必须严格遵守）】
{type_system_prompt}

分镜数量：{shot_count}

是否有人物参考图：{"是" if has_person_reference else "否"}
是否有产品参考图：{"是" if has_product_reference else "否"}

人物主体默认规则：{subject_rule}

请根据上述视频类型的系统要求生成分镜表。
注意：
- 如果有人物参考图，subject 默认沿用"参考图中的同一位人物"逻辑。
- 不能无依据地写"年轻男性"。
- 如果视频类型要求无口播文案，subtitle 字段全部留空字符串。
- 分镜内容要适合短视频图生图。
- 场景、动作、镜头、光影、氛围要具体。
"""

    try:
        data = _call_chat_json(system_prompt, user_prompt)
        raw_shots = data.get("shots", [])

        if not isinstance(raw_shots, list) or not raw_shots:
            raise ValueError("AI 没有返回有效 shots")

        normalized: List[Dict[str, Any]] = []

        for index, row in enumerate(raw_shots[:shot_count], start=1):
            if not isinstance(row, dict):
                row = {}

            subject = _safe_text(row.get("subject"))
            if not subject:
                subject = subject_rule

            if has_person_reference:
                if "男性" in subject and ("男性" not in user_idea and "男生" not in user_idea and "男" not in user_idea):
                    subject = subject_rule

            shot = {
                "shot_id": row.get("shot_id", index),
                "time_sequence": _safe_text(row.get("time_sequence"), f"分镜 {index}"),
                "subject": subject,
                "subject_action": _safe_text(row.get("subject_action"), "完成当前分镜动作"),
                "scene": _safe_text(row.get("scene"), "真实生活场景"),
                "shot_size": _safe_text(row.get("shot_size"), "中景"),
                "camera_movement": _safe_text(row.get("camera_movement"), "手持轻微运动镜头"),
                "lighting": _safe_text(row.get("lighting"), "自然光"),
                "mood": _safe_text(row.get("mood"), "真实、自然、生活感强"),
                "subtitle": _safe_text(
                    row.get("subtitle"),
                    "" if "无口播" in type_name else f"{type_name}口播-分镜{index}",
                ),
                "negative_prompt": _safe_text(
                    row.get("negative_prompt"),
                    "不要棚拍摄影光的精致感，不要过度磨皮，不要夸张美颜，不要塑料感，不要人物变形，不要五官漂移，不要水印，不要文字",
                ),
                "reference_type": _normalize_reference_type(
                    row.get(
                        "reference_type",
                        _reference_type_for_mock(
                            has_person_reference,
                            has_product_reference,
                        ),
                    )
                ),
                "video_prompt": _safe_text(
                    row.get("video_prompt"),
                    "人物动作自然连贯，镜头轻微移动，保持真实短视频质感。",
                ),
            }

            shot.update(
                build_image_prompt_from_fields(
                    shot,
                    has_person_reference=has_person_reference,
                    has_product_reference=has_product_reference,
                )
            )

            normalized.append(shot)

        while len(normalized) < shot_count:
            extra_rows = _mock_storyboard_table(
                user_idea=user_idea,
                selected_video_type_detail=selected_video_type_detail,
                shot_count=shot_count - len(normalized),
                has_person_reference=has_person_reference,
                has_product_reference=has_product_reference,
            )

            for item in extra_rows:
                item["shot_id"] = len(normalized) + 1
                normalized.append(item)

        return normalized[:shot_count]

    except Exception as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"⚠️ LLM API 调用失败，回退到 mock 模式", file=sys.stderr)
        print(f"   错误类型: {type(e).__name__}", file=sys.stderr)
        print(f"   错误信息: {e}", file=sys.stderr)
        print(f"   模型: {_get_model()}", file=sys.stderr)
        print(f"   Base URL: {_get_base_url() or '(默认)'}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        return _mock_storyboard_table(
            user_idea=user_idea,
            selected_video_type_detail=selected_video_type_detail,
            shot_count=shot_count,
            has_person_reference=has_person_reference,
            has_product_reference=has_product_reference,
        )


# =========================
# 6. 兼容旧函数名，防止 app.py 导入失败
# =========================

def generate_video_types_by_idea(user_idea: str) -> List[Dict[str, str]]:
    """（兼容旧函数名）返回三种产品种草型视频类型"""
    return [
        {
            "type_name": "产品种草型-数字人口播+产品展示",
            "description": "AI数字人口播讲解产品，配合产品特写与使用展示，口播逻辑为痛点→卖点→产品介绍→号召购买。",
            "suitable_for": "美妆、护肤、数码、家居、食品、服饰、个护等全品类产品种草",
            "system_prompt": "数字人口播+产品展示模式，口播文案需遵循痛点→卖点→产品介绍→号召购买的结构，所有文案场景化表达。",
        },
        {
            "type_name": "产品种草型-纯产品展示+画外音口播",
            "description": "无数字人出镜，纯产品展示画面配合画外音口播，口播逻辑为痛点→卖点→产品介绍→号召购买。",
            "suitable_for": "美妆、护肤、数码、家居、食品、服饰、个护等全品类产品种草",
            "system_prompt": "纯产品展示+画外音口播模式，全程不出现数字人，口播以画外音呈现。",
        },
        {
            "type_name": "产品种草型-沉浸式产品使用（无口播文案）",
            "description": "沉浸式产品使用展示，无口播无旁白，纯画面叙事。",
            "suitable_for": "美妆、护肤、数码、家居、食品、服饰、个护等全品类产品种草",
            "system_prompt": "沉浸式产品使用模式，无口播文案，纯靠画面语言传达产品卖点。",
        },
    ]