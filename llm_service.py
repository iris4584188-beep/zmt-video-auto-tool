"""LLM 服务：生成分镜表 + 构建分镜图提示词"""

import json
import os
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
    return _get_env("OPENAI_MODEL", "gpt-4o-mini")


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

    response = client.chat.completions.create(
        model=_get_model(),
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or "{}"
    return json.loads(content)


# =========================
# 3. 构建分镜图提示词
# =========================

def build_image_prompt_from_fields(
    shot: Dict[str, Any],
    has_person_reference: bool = False,
    has_product_reference: bool = False,
) -> Dict[str, str]:
    reference_type = _normalize_reference_type(shot.get("reference_type", "person"))

    negative = _safe_text(
        shot.get("negative_prompt"),
        "不要棚拍摄影光的精致感，不要过度磨皮，不要夸张美颜，不要塑料感，不要人物变形，不要五官漂移，不要额外多手多脚，不要水印，不要文字",
    )

    subject = _safe_text(shot.get("subject"), "基于参考图中的同一位人物")
    subject_action = _safe_text(shot.get("subject_action"), "完成当前分镜动作")
    scene = _safe_text(shot.get("scene"), "真实生活场景")
    shot_size = _safe_text(shot.get("shot_size"), "中景")
    camera_movement = _safe_text(shot.get("camera_movement"), "手持轻微运动镜头")
    lighting = _safe_text(shot.get("lighting"), "自然光")
    mood = _safe_text(shot.get("mood"), "真实、自然、生活感强")
    time_sequence = _safe_text(shot.get("time_sequence"), "")
    subtitle = _safe_text(shot.get("subtitle"), "")

    person_lock = ""
    if has_person_reference and reference_type in ["person", "both"]:
        person_lock = (
            "【人物主体】基于上传人物参考图中的同一位人物进行图生图，"
            "保持人物主体身份一致、脸型一致、五官一致、发型一致、气质一致，"
            "不要随意改变性别，不要随意改变年龄感，不要换脸。"
        )

    product_lock = ""
    if has_product_reference and reference_type in ["product", "both"]:
        product_lock = (
            "【产品主体】如画面涉及产品，请基于上传产品参考图中的同一产品进行图生图，"
            "保持产品包装、颜色、材质、外观形态一致，不要替换成其他产品。"
        )

    cn_parts = [
        person_lock,
        product_lock,
        f"【视频主题】{subtitle}" if subtitle else "",
        f"【时序】{time_sequence}" if time_sequence else "",
        f"【人物主体】{subject}",
        f"【人物主体动作】{subject_action}",
        f"【场景】{scene}",
        f"【景别】{shot_size}",
        f"【镜头运动】{camera_movement}",
        f"【光影】{lighting}",
        f"【氛围】{mood}",
        "【画面要求】整体画面为真实短视频图生图效果，生活化、自然、纪实感强，适合自媒体视频分镜图。",
        f"【负面提示词】{negative}",
    ]

    image_prompt_cn = " ".join([x for x in cn_parts if x])

    person_lock_en = ""
    if has_person_reference and reference_type in ["person", "both"]:
        person_lock_en = (
            "Use the uploaded person reference image as image-to-image guidance. "
            "Keep the same person identity, same face, same facial features, same hairstyle, same overall vibe. "
            "Do not change gender, age impression, or identity."
        )

    product_lock_en = ""
    if has_product_reference and reference_type in ["product", "both"]:
        product_lock_en = (
            "If the frame contains a product, use the uploaded product reference image as image-to-image guidance. "
            "Keep the same packaging, same color, same material, and same overall appearance."
        )

    en_parts = [
        person_lock_en,
        product_lock_en,
        f"Video theme: {subtitle}." if subtitle else "",
        f"Time sequence: {time_sequence}." if time_sequence else "",
        f"Subject: {subject}.",
        f"Subject action: {subject_action}.",
        f"Scene: {scene}.",
        f"Shot size: {shot_size}.",
        f"Camera movement: {camera_movement}.",
        f"Lighting: {lighting}.",
        f"Mood: {mood}.",
        "Visual style: realistic short-video storyboard image, candid, natural, lifestyle, documentary-like.",
        f"Negative prompt: {negative}.",
    ]

    image_prompt_en = " ".join([x for x in en_parts if x])

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
    subject_text = _subject_from_reference(has_person_reference, user_idea)
    default_reference_type = _reference_type_for_mock(
        has_person_reference,
        has_product_reference,
    )

    base_rows = [
        {
            "time_sequence": "开场",
            "subject_action": "出现在镜头中，进入画面并建立场景",
            "scene": "与主题相关的真实生活场景",
            "shot_size": "中景",
            "camera_movement": "手持轻微跟拍",
            "lighting": "自然光",
            "mood": "真实自然，生活感强",
            "subtitle": "开场建立情境",
        },
        {
            "time_sequence": "过程前段",
            "subject_action": "展示准备动作或进入主要流程",
            "scene": "主题相关场景",
            "shot_size": "近景",
            "camera_movement": "缓慢推进",
            "lighting": "自然光与环境光",
            "mood": "专注自然，轻松记录",
            "subtitle": "过程展示",
        },
        {
            "time_sequence": "过程中段",
            "subject_action": "完成核心动作或展示重点内容",
            "scene": "主题相关核心场景",
            "shot_size": "中近景",
            "camera_movement": "轻微摇镜或手持感",
            "lighting": "自然光和室内光混合",
            "mood": "真实训练感/使用感",
            "subtitle": "重点内容展示",
        },
        {
            "time_sequence": "结尾",
            "subject_action": "收尾、总结、看向镜头或展示结果",
            "scene": "同一主题场景收尾",
            "shot_size": "中景",
            "camera_movement": "稳定镜头",
            "lighting": "柔和自然光",
            "mood": "轻松满意，完成感",
            "subtitle": "结尾收束",
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
你是一个擅长自媒体 AIKOL 视频分镜策划的助手。
你需要根据用户的模糊需求，输出一个适合图生图工作流的分镜表 JSON。

重要规则：
1. 当前项目逻辑是“底图/参考图 + 分镜提示词 = 分镜图”。
2. 如果用户上传了人物参考图，主体必须默认为“基于上传人物参考图中的同一位人物”。
3. 不要擅自写成男性或女性，除非用户需求里明确写了性别。
4. 如果用户上传了产品参考图，涉及产品时要在 reference_type 中标注 product 或 both。
5. reference_type 只能是：person / product / both / none
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

视频类型：{type_name}
视频类型说明：{type_description}
视频类型系统要求：{type_system_prompt}

分镜数量：{shot_count}

是否有人物参考图：{"是" if has_person_reference else "否"}
是否有产品参考图：{"是" if has_product_reference else "否"}

人物主体默认规则：{subject_rule}

请生成分镜表。
注意：
- 如果有人物参考图，subject 默认沿用“参考图中的同一位人物”逻辑。
- 不能无依据地写“年轻男性”。
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
                "subtitle": _safe_text(row.get("subtitle"), f"{type_name}分镜{index}"),
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

    except Exception:
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
    return [
        {
            "type_name": "种草推荐类",
            "description": "通过自然展示、使用体验、结果呈现来推荐产品、服务、方法或生活方式。",
            "suitable_for": "美妆、护肤、健身、穿搭、好物、生活方式、本地生活等账号",
            "system_prompt": "生成种草推荐类分镜表，重点突出产品/方法的使用场景、真实体验、自然露出和结果反馈。",
        },
        {
            "type_name": "Vlog记录类",
            "description": "以第一视角或日常记录方式展示人物一天中的生活、工作、训练或使用过程。",
            "suitable_for": "生活方式、健身、美妆、学习、职场、旅行、个人IP账号",
            "system_prompt": "生成Vlog记录类分镜表，重点突出真实生活感、时间流动、人物状态和自然随手拍氛围。",
        },
    ]