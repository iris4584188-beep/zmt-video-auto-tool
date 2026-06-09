"""自媒体视频分镜自动化工具 - Streamlit 入口｜玫粉色可爱风主题"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


# =========================
# 1. 基础路径
# =========================

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "outputs"
PERSON_REF_DIR = OUTPUT_DIR / "reference_images" / "person"
PRODUCT_REF_DIR = OUTPUT_DIR / "reference_images" / "product"
STORYBOARD_IMAGE_DIR = OUTPUT_DIR / "storyboard_images"
STORYBOARD_VIDEO_DIR = OUTPUT_DIR / "storyboard_videos"

for folder in [
    OUTPUT_DIR,
    PERSON_REF_DIR,
    PRODUCT_REF_DIR,
    STORYBOARD_IMAGE_DIR,
    STORYBOARD_VIDEO_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)


# =========================
# 2. 页面配置 + 玫粉色主题
# =========================

st.set_page_config(
    page_title="自媒体视频分镜自动化工具",
    page_icon="💗",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --pink-main: #ff4f9a;
        --pink-deep: #d92d73;
        --pink-soft: #fff0f7;
        --pink-card: #fff8fb;
        --pink-border: #ffc3dd;
        --pink-light: #ffe6f1;
        --cream: #fffdf8;
        --text-main: #462538;
        --text-soft: #8a6478;
        --purple-soft: #f4eaff;
        --shadow-soft: 0 12px 34px rgba(255, 79, 154, 0.16);
    }

    .stApp {
        background:
            radial-gradient(circle at 8% 10%, rgba(255, 195, 221, 0.45), transparent 28%),
            radial-gradient(circle at 88% 12%, rgba(244, 234, 255, 0.55), transparent 32%),
            linear-gradient(180deg, #fff7fb 0%, #ffffff 48%, #fff8fb 100%);
        color: var(--text-main);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fff0f7 0%, #ffffff 100%);
        border-right: 1px solid #ffd0e4;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--text-main);
    }

    .hero-card {
        background: linear-gradient(135deg, #ffffff 0%, #fff0f7 50%, #fffdf8 100%);
        border: 1.5px solid var(--pink-border);
        border-radius: 30px;
        padding: 30px 32px;
        margin-bottom: 24px;
        box-shadow: var(--shadow-soft);
        position: relative;
        overflow: hidden;
    }

    .hero-card:before {
        content: "♡";
        position: absolute;
        right: 30px;
        top: 16px;
        color: #ff9ac4;
        font-size: 48px;
        font-weight: 900;
    }

    .tool-title {
        font-size: 38px;
        font-weight: 950;
        color: var(--text-main);
        letter-spacing: -0.8px;
        margin-bottom: 8px;
    }

    .tool-subtitle {
        color: var(--text-soft);
        font-size: 15px;
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid var(--pink-border);
        border-radius: 999px;
        display: inline-block;
        padding: 9px 16px;
        margin-bottom: 16px;
    }

    .hero-tip {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid #ffd0e4;
        color: #7d3d5c;
        border-radius: 20px;
        padding: 14px 16px;
        font-size: 14px;
        line-height: 1.75;
    }

    .section-card {
        background: rgba(255, 255, 255, 0.9);
        border: 1.5px solid var(--pink-border);
        border-radius: 26px;
        padding: 24px 26px;
        margin-bottom: 18px;
        box-shadow: var(--shadow-soft);
    }

    .mini-card {
        background: #fff8fb;
        border: 1px solid #ffd0e4;
        border-radius: 20px;
        padding: 16px 18px;
        margin-bottom: 12px;
    }

    .type-card {
        background: linear-gradient(135deg, #fff8fb 0%, #ffffff 100%);
        border: 1.5px solid var(--pink-border);
        border-radius: 22px;
        padding: 16px 18px;
        margin-top: 10px;
        color: var(--text-main);
    }

    .status-pill {
        display: inline-block;
        background: #fff0f7;
        border: 1px solid #ffc3dd;
        color: #9a315e;
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 13px;
        font-weight: 800;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .shot-tag {
        display: inline-block;
        background: linear-gradient(135deg, #ff67aa, #ff3f91);
        color: white;
        border-radius: 999px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 900;
        margin-bottom: 12px;
        box-shadow: 0 8px 18px rgba(255, 79, 154, 0.26);
    }

    .shot-title {
        font-size: 18px;
        font-weight: 950;
        color: #d92d73;
        margin-top: 12px;
        margin-bottom: 8px;
    }

    .shot-meta {
        font-size: 13px;
        color: #725066;
        line-height: 1.75;
        margin-bottom: 10px;
        background: #fff8fb;
        border: 1px solid #ffd6e8;
        border-radius: 18px;
        padding: 12px 14px;
    }

    .placeholder-box {
        height: 240px;
        border-radius: 22px;
        border: 1.5px dashed #ff9ac4;
        background:
            radial-gradient(#ffd3e6 14%, transparent 16%) 0 0 / 34px 34px,
            #fff8fb;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #c3487a;
        text-align: center;
        font-size: 15px;
        font-weight: 900;
        margin-bottom: 12px;
    }

    .prompt-title {
        font-size: 13px;
        font-weight: 900;
        color: #d92d73;
        margin-top: 8px;
        margin-bottom: 6px;
    }

    .thumb-caption {
        font-size: 12px;
        color: #8a6478;
        word-break: break-all;
        margin-top: 4px;
    }

    div[data-testid="stFileUploader"] {
        background: #fff8fb;
        border: 1.5px dashed #ffadd0;
        border-radius: 22px;
        padding: 12px;
    }

    .stButton > button {
        border-radius: 999px !important;
        border: 1.5px solid #ff8dbc !important;
        background: linear-gradient(135deg, #ff67aa 0%, #ff3f91 100%) !important;
        color: white !important;
        font-weight: 900 !important;
        box-shadow: 0 9px 20px rgba(255, 79, 154, 0.24) !important;
        transition: all 0.16s ease-in-out !important;
        min-height: 2.7rem;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 26px rgba(255, 79, 154, 0.32) !important;
        border-color: #ff4f9a !important;
    }

    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] div,
    div[data-testid="stNumberInput"] input {
        border-radius: 18px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: #fff0f7;
        border-radius: 999px;
        border: 1px solid #ffc3dd;
        color: #9a315e;
        padding: 8px 18px;
        font-weight: 800;
    }

    .stAlert {
        border-radius: 18px !important;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid #ffd0e4;
    }

    hr {
        border-color: #ffe0ee;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 3. 通用视频类型
# =========================

UNIVERSAL_VIDEO_TYPES = [
    {
        "type_name": "产品种草型-数字人口播+产品展示",
        "description": "AI数字人口播讲解产品，配合产品特写与使用展示，口播逻辑为痛点→卖点→产品介绍→号召购买。",
        "suitable_for": "美妆、护肤、数码、家居、食品、服饰、个护等全品类产品种草",
        "system_prompt": """你是内容电商资深编导，深谙产品种草型视频的底层逻辑，擅长将产品卖点融入口播文案中。

【视频形式】AI数字人口播讲解 + 产品特写/使用展示画面。数字人出镜口播，画面穿插产品细节。

【分镜字段要求】
每个分镜必须包含：时序、主体（人物或产品本身）、主体动作、口播文案、景别、镜头运动、光影、氛围调性。

【口播文案核心逻辑】
① 结构顺序：讲痛点 → 引出卖点 → 产品介绍 → 号召购买
② 场景化表达：所有文案必须"场景化"，例如：
  - 痛点场景化："熬夜脸黑暗沉" → "有没有姐妹跟我一样，熬夜追剧到凌晨，第二天脸色暗沉得不敢化妆出门？"
  - 卖点场景化："提亮肤色" → "涂上它出门，回头率直接拉满"
  - 参数场景化："五万毫安大容量充电宝" → "充一次电能让你打游戏一整天不用焦虑电量"
③ 号召购买：结尾促单转化，引导下单

【社交媒体风格】
分镜碎且多、画面钩子强、节奏感强，适合短视频平台传播。

【品类识别】先识别产品所属品类赛道，确保产品使用方法符合产品本身特性。""",
    },
    {
        "type_name": "产品种草型-纯产品展示+画外音口播",
        "description": "无数字人出镜，纯产品展示画面配合画外音口播，口播逻辑为痛点→卖点→产品介绍→号召购买。",
        "suitable_for": "美妆、护肤、数码、家居、食品、服饰、个护等全品类产品种草",
        "system_prompt": """你是内容电商资深编导，深谙产品种草型视频的底层逻辑，擅长将产品卖点融入口播文案中。

【视频形式】纯产品展示画面 + 画外音口播。全程不出现数字人，口播文案以画外音形式呈现。

【分镜字段要求】
每个分镜必须包含：时序、主体（产品本身）、主体动作、口播文案、景别、镜头运动、光影、氛围调性。

【口播文案核心逻辑】
① 结构顺序：讲痛点 → 引出卖点 → 产品介绍 → 号召购买
② 场景化表达：所有文案必须"场景化"，例如：
  - 痛点场景化："熬夜脸黑暗沉" → "有没有姐妹跟我一样，熬夜追剧到凌晨，第二天脸色暗沉得不敢化妆出门？"
  - 卖点场景化："提亮肤色" → "涂上它出门，回头率直接拉满"
  - 参数场景化："五万毫安大容量充电宝" → "充一次电能让你打游戏一整天不用焦虑电量"
③ 号召购买：结尾促单转化，引导下单

【社交媒体风格】
分镜碎且多、画面钩子强、节奏感强，适合短视频平台传播。

【品类识别】先识别产品所属品类赛道，确保产品使用方法符合产品本身特性。""",
    },
    {
        "type_name": "产品种草型-沉浸式产品使用（无口播文案）",
        "description": "沉浸式产品使用展示，无口播无旁白，纯画面叙事，靠产品使用细节和氛围打动用户。",
        "suitable_for": "美妆、护肤、数码、家居、食品、服饰、个护等全品类产品种草",
        "system_prompt": """你是内容电商资深编导，深谙产品种草型视频的底层逻辑，擅长将产品卖点融入纯粹的视觉叙事中。

【视频形式】沉浸式产品使用展示，全程无口播文案、无旁白。纯粹依靠画面语言传达产品卖点。

【分镜字段要求】
每个分镜必须包含：时序、主体（产品本身）、主体动作、景别、镜头运动、光影、氛围调性。
⚠️ 重要：本类型不需要口播文案（subtitle 字段留空字符串即可）。

【社交媒体风格】
分镜碎且多、画面钩子强、节奏感强，适合短视频平台传播。用细节镜头和氛围感替代语言说服。

【品类识别】先识别产品所属品类赛道，确保产品使用方法符合产品本身特性，符合该品类其他产品的通用使用逻辑。""",
    },
]


# =========================
# 4. 导入服务
# =========================

try:
    from llm_service import (
        generate_storyboard_table,
        build_image_prompt_from_fields,
        get_llm_mode,
    )
except Exception as e:
    st.error(f"llm_service.py 导入失败：{e}")

    def get_llm_mode():
        return "mock"

    def build_image_prompt_from_fields(
        shot: Dict[str, Any],
        has_person_reference: bool = False,
        has_product_reference: bool = False,
    ) -> Dict[str, str]:
        """（fallback）按 AGENT_TASK.md 逻辑：提取 5 核心维度生成 AIGC 图片提示词"""
        subject = shot.get("subject", "一位内容创作者")
        subject_action = shot.get("subject_action", "自然站立面对镜头")
        lighting = shot.get("lighting", "自然柔光")
        mood = shot.get("mood", "真实自然，生活感强")
        shot_size = shot.get("shot_size", "中景")
        negative = shot.get("negative_prompt", "不要棚拍摄影光，不要过度磨皮，不要水印")

        cn = (
            f"{shot_size}，{subject}，{subject_action}，"
            f"{lighting}，{mood}。"
            f"整体画面为短视频分镜图质感，生活化自然纪实感强。"
            f"负面提示词：{negative}。"
        )
        return {"image_prompt_cn": cn, "image_prompt_en": cn}

    def generate_storyboard_table(
        user_idea: str,
        selected_video_type_detail: Dict[str, Any],
        shot_count: int,
        has_person_reference: bool = False,
        has_product_reference: bool = False,
    ) -> List[Dict[str, Any]]:
        type_name = selected_video_type_detail.get("type_name", "通用视频")
        is_no_voiceover = "无口播" in type_name
        is_pure_product = "纯产品展示" in type_name or "沉浸式" in type_name

        rows = []
        for i in range(1, shot_count + 1):
            if has_person_reference and not is_pure_product:
                subject = "基于上传人物参考图中的同一位人物"
            elif is_pure_product:
                subject = "产品主体"
            else:
                subject = "一位内容创作者（数字人）"
            row = {
                "shot_id": i,
                "time_sequence": f"分镜{i}",
                "subject": subject,
                "subject_action": "展示产品细节与使用效果" if is_pure_product else "完成当前分镜动作",
                "scene": "真实生活场景",
                "shot_size": "中景",
                "camera_movement": "手持轻微运动镜头",
                "lighting": "自然光",
                "mood": "真实自然，生活感强",
                "subtitle": "" if is_no_voiceover else f"{type_name} 口播文案 - 分镜{i}",
                "negative_prompt": "不要棚拍摄影光的精致感，不要过度磨皮，不要夸张美颜，不要塑料感，不要水印，不要文字",
                "reference_type": "person" if (has_person_reference and not is_pure_product) else "none",
                "video_prompt": "产品特写镜头自然连贯，保持真实短视频质感。" if is_pure_product else "人物动作自然连贯，镜头轻微移动，保持真实短视频质感。",
            }
            row.update(build_image_prompt_from_fields(row, has_person_reference, has_product_reference))
            rows.append(row)
        return rows

try:
    import image_service
except Exception as e:
    image_service = None
    st.error(f"image_service.py 导入失败：{e}")

try:
    import video_service
except Exception:
    video_service = None


# =========================
# 5. Session State
# =========================

def init_state():
    defaults = {
        "user_idea": "",
        "selected_video_type_detail": UNIVERSAL_VIDEO_TYPES[0],
        "shot_count": 8,
        "person_reference_images": [],
        "product_reference_images": [],
        "storyboard_table": [],
        "storyboard_images": [],
        "storyboard_videos": [],
        "current_page": "① 需求与素材",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# =========================
# 6. 工具函数
# =========================

def clean_filename(filename: str) -> str:
    keep = []
    for ch in filename:
        if ch.isalnum() or ch in [".", "_", "-", " "]:
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep)


def save_uploaded_files(uploaded_files, target_dir: Path, prefix: str) -> List[str]:
    paths = []
    for idx, file in enumerate(uploaded_files or []):
        suffix = Path(file.name).suffix.lower() or ".png"
        safe_name = clean_filename(Path(file.name).stem)
        save_name = f"{prefix}_{idx + 1}_{safe_name}{suffix}"
        save_path = target_dir / save_name

        with open(save_path, "wb") as f:
            f.write(file.getvalue())

        paths.append(str(save_path))
    return paths


def preview_images(paths: List[str], title: str):
    st.write(f"**{title}（共 {len(paths)} 张）**")
    if not paths:
        st.caption("暂未上传")
        return

    cols = st.columns(4)
    for i, path in enumerate(paths[:8]):
        with cols[i % 4]:
            st.image(path, width=130)
            st.markdown(
                f"<div class='thumb-caption'>{Path(path).name}</div>",
                unsafe_allow_html=True,
            )


def build_reference_pool() -> List[Dict[str, str]]:
    pool = []
    for i, path in enumerate(st.session_state.get("person_reference_images", []), start=1):
        pool.append({"label": f"人物图 {i} - {Path(path).name}", "path": path})
    for i, path in enumerate(st.session_state.get("product_reference_images", []), start=1):
        pool.append({"label": f"产品图 {i} - {Path(path).name}", "path": path})
    return pool


def get_image_result_by_shot_id(shot_id: int) -> Optional[Dict[str, Any]]:
    for item in st.session_state.get("storyboard_images", []):
        if int(item.get("shot_id", -1)) == int(shot_id):
            return item
    return None


def get_video_result_by_shot_id(shot_id: int) -> Optional[Dict[str, Any]]:
    for item in st.session_state.get("storyboard_videos", []):
        if int(item.get("shot_id", -1)) == int(shot_id):
            return item
    return None


def replace_result_by_shot_id(results: List[Dict[str, Any]], new_item: Dict[str, Any]) -> List[Dict[str, Any]]:
    shot_id = int(new_item.get("shot_id", -1))
    updated = []
    found = False

    for item in results:
        if int(item.get("shot_id", -999)) == shot_id:
            updated.append(new_item)
            found = True
        else:
            updated.append(item)

    if not found:
        updated.append(new_item)

    updated.sort(key=lambda x: int(x.get("shot_id", 999)))
    return updated


def create_simple_mock_image(shot_id: int, prompt: str) -> str:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (1024, 1024), color=(255, 240, 247))
    draw = ImageDraw.Draw(img)
    draw.text((70, 90), f"Shot {shot_id}", fill=(170, 45, 105))
    draw.text((70, 150), "Mock Image", fill=(170, 45, 105))
    draw.text((70, 240), prompt[:180], fill=(170, 45, 105))
    save_path = STORYBOARD_IMAGE_DIR / f"mock_shot_{shot_id}.png"
    img.save(save_path)
    return str(save_path)


def normalize_image_result(result: Any, shot_id: int, used_refs: List[str], prompt: str) -> Dict[str, Any]:
    if isinstance(result, str):
        return {
            "shot_id": shot_id,
            "image_path": result,
            "used_reference_images": used_refs,
            "mode": "real_or_service",
            "error": "",
        }

    if isinstance(result, dict):
        image_path = (
            result.get("image_path")
            or result.get("path")
            or result.get("file_path")
            or result.get("output_path")
        )
        return {
            "shot_id": shot_id,
            "image_path": image_path,
            "used_reference_images": result.get("used_reference_images", used_refs),
            "mode": result.get("mode", "real_or_service"),
            "error": result.get("error", ""),
        }

    mock_path = create_simple_mock_image(shot_id, prompt)
    return {
        "shot_id": shot_id,
        "image_path": mock_path,
        "used_reference_images": used_refs,
        "mode": "mock",
        "error": "图片服务返回格式无法识别，已使用 mock 占位图",
    }


def generate_one_storyboard_image(shot: Dict[str, Any], seed: Optional[int] = None) -> Dict[str, Any]:
    shot_id = int(shot.get("shot_id", 1))
    prompt = shot.get("image_prompt_cn") or shot.get("image_prompt_en") or ""
    negative_prompt = shot.get("negative_prompt", "")
    reference_type = shot.get("reference_type", "person")

    use_custom_base = bool(shot.get("use_custom_base_image", False))
    selected_base_image_path = shot.get("selected_base_image_path", "") if use_custom_base else ""

    used_refs = []
    if selected_base_image_path:
        used_refs = [selected_base_image_path]
    else:
        if reference_type == "person":
            used_refs = st.session_state.get("person_reference_images", [])
        elif reference_type == "product":
            used_refs = st.session_state.get("product_reference_images", [])
        elif reference_type == "both":
            used_refs = (
                st.session_state.get("person_reference_images", [])
                + st.session_state.get("product_reference_images", [])
            )

    if image_service and hasattr(image_service, "generate_storyboard_image"):
        try:
            result = image_service.generate_storyboard_image(
                image_prompt=prompt,
                base_image_path=selected_base_image_path if selected_base_image_path else None,
                reference_type=reference_type,
                person_image_paths=st.session_state.get("person_reference_images", []),
                product_image_paths=st.session_state.get("product_reference_images", []),
                shot_id=shot_id,
                negative_prompt=negative_prompt,
                seed=seed,
            )
            return normalize_image_result(result, shot_id, used_refs, prompt)
        except Exception as e:
            mock_path = create_simple_mock_image(shot_id, prompt)
            return {
                "shot_id": shot_id,
                "image_path": mock_path,
                "used_reference_images": used_refs,
                "mode": "mock",
                "error": str(e),
            }

    mock_path = create_simple_mock_image(shot_id, prompt)
    return {
        "shot_id": shot_id,
        "image_path": mock_path,
        "used_reference_images": used_refs,
        "mode": "mock",
        "error": "未检测到 image_service.generate_storyboard_image",
    }


def generate_one_storyboard_video(shot: Dict[str, Any]) -> Dict[str, Any]:
    shot_id = int(shot.get("shot_id", 1))
    image_result = get_image_result_by_shot_id(shot_id)

    if not image_result or not image_result.get("image_path"):
        return {
            "shot_id": shot_id,
            "video_path": "",
            "mode": "mock",
            "error": "没有对应分镜图，无法生成视频",
        }

    if video_service and hasattr(video_service, "generate_storyboard_video"):
        try:
            result = video_service.generate_storyboard_video(
                storyboard_image_path=image_result["image_path"],
                video_prompt=shot.get("video_prompt", ""),
            )
            if isinstance(result, dict):
                return {
                    "shot_id": shot_id,
                    "video_path": result.get("video_path") or result.get("path", ""),
                    "mode": result.get("mode", "real_or_service"),
                    "error": result.get("error", ""),
                }
            return {
                "shot_id": shot_id,
                "video_path": result,
                "mode": "real_or_service",
                "error": "",
            }
        except Exception as e:
            return {
                "shot_id": shot_id,
                "video_path": "",
                "mode": "mock",
                "error": str(e),
            }

    return {
        "shot_id": shot_id,
        "video_path": "",
        "mode": "mock",
        "error": "未检测到 video_service.generate_storyboard_video",
    }


# =========================
# 7. 左侧导航
# =========================

with st.sidebar:
    st.markdown("## 💗 工作台导航")

    page = st.radio(
        "选择步骤",
        [
            "① 需求与素材",
            "② 分镜表编辑",
            "③ 生成分镜图",
            "④ 生成分镜视频",
            "⑤ 状态与导出",
        ],
        key="current_page",
    )

    st.divider()
    st.markdown("### 🧁 当前进度")

    st.markdown(f"<span class='status-pill'>人物图 {len(st.session_state.person_reference_images)} 张</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='status-pill'>产品图 {len(st.session_state.product_reference_images)} 张</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='status-pill'>分镜表 {len(st.session_state.storyboard_table)} 条</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='status-pill'>分镜图 {len(st.session_state.storyboard_images)} 张</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='status-pill'>分镜视频 {len(st.session_state.storyboard_videos)} 条</span>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### ⚙️ API 状态")
    st.caption(f"LLM：{get_llm_mode()}")

    if image_service and hasattr(image_service, "get_image_api_status_message"):
        st.caption(f"生图：{image_service.get_image_api_status_message()}")
    else:
        st.caption("生图：未加载 image_service")

    if video_service and hasattr(video_service, "generate_storyboard_video"):
        st.caption("视频：已检测到 video_service")
    else:
        st.caption("视频：未接入或 mock 状态")


# =========================
# 8. 页面头部
# =========================

st.markdown(
    """
    <div class="hero-card">
        <div class="tool-title">💗 自媒体视频分镜自动化工具</div>
        <div class="tool-subtitle">输入需求与素材 → 生成分镜表 → 底图 + 提示词生成分镜图 → 分镜图生成视频</div>
        <div class="hero-tip">
            当前为玫粉色可爱风主题。左侧导航可以快速切换步骤，适合你后续把工具发给别人测试使用。
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# 页面 1：需求与素材
# =========================

if page == "① 需求与素材":
    st.header("💗 ① 输入需求与素材配置")

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.25, 0.8])

    with col1:
        st.subheader("📝 输入你的模糊需求")
        user_idea = st.text_area(
            "模糊需求",
            value=st.session_state.get("user_idea", ""),
            placeholder="例如：我想做一个健身vlog，人物主体是上传参考图中的同一位年轻女性，主题是肩部训练记录",
            height=140,
            label_visibility="collapsed",
        )
        st.session_state.user_idea = user_idea
        st.caption("建议写清楚：人物主体、赛道、主题、风格、产品卖点。比如：同一位年轻女性、真实随手拍、不要棚拍感。")

    with col2:
        st.subheader("🎀 选择视频类型")

        type_names = [x["type_name"] for x in UNIVERSAL_VIDEO_TYPES]
        current_name = st.session_state.selected_video_type_detail.get("type_name", UNIVERSAL_VIDEO_TYPES[0]["type_name"])
        default_index = type_names.index(current_name) if current_name in type_names else 0

        selected_name = st.selectbox(
            "视频类型",
            options=type_names,
            index=default_index,
            label_visibility="collapsed",
        )

        selected_detail = next(x for x in UNIVERSAL_VIDEO_TYPES if x["type_name"] == selected_name)
        st.session_state.selected_video_type_detail = selected_detail

        st.markdown(
            f"""
            <div class="type-card">
                <b>当前选择：{selected_detail['type_name']}</b><br>
                <span style="color:#8a6478;font-size:13px;">{selected_detail['description']}</span><br><br>
                <span style="color:#8a6478;font-size:13px;"><b>适合：</b>{selected_detail['suitable_for']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)

    setup_col1, setup_col2 = st.columns([0.8, 1.2])

    with setup_col1:
        st.subheader("🧩 设置分镜数量")
        st.session_state.shot_count = st.slider(
            "分镜数量",
            min_value=1,
            max_value=30,
            value=int(st.session_state.get("shot_count", 8)),
        )
        st.caption("提示：15 秒视频通常 3-5 个分镜；30 秒视频通常 6-10 个分镜。")

    with setup_col2:
        st.subheader("🖼️ 上传参考图")
        st.caption("人物图和产品图总数量建议不超过 9 张。分镜图生成时可单独选择是否垫底图。")

        upload_col1, upload_col2 = st.columns(2)

        with upload_col1:
            person_files = st.file_uploader(
                "上传人物图",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="person_uploader",
            )

        with upload_col2:
            product_files = st.file_uploader(
                "上传产品图",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="product_uploader",
            )

    person_count = len(person_files or [])
    product_count = len(product_files or [])
    total_count = person_count + product_count

    if total_count > 9:
        st.error("人物图 + 产品图总数不能超过 9 张，请减少图片数量。")
    else:
        if person_files is not None:
            st.session_state.person_reference_images = save_uploaded_files(person_files, PERSON_REF_DIR, "person")
        if product_files is not None:
            st.session_state.product_reference_images = save_uploaded_files(product_files, PRODUCT_REF_DIR, "product")

    tab1, tab2 = st.tabs(["人物图预览", "产品图预览"])
    with tab1:
        preview_images(st.session_state.person_reference_images, "人物图")
    with tab2:
        preview_images(st.session_state.product_reference_images, "产品图")

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("💗 生成分镜表", use_container_width=True):
        if not st.session_state.user_idea.strip():
            st.error("请先输入需求。")
        else:
            with st.spinner("正在生成分镜表..."):
                rows = generate_storyboard_table(
                    user_idea=st.session_state.user_idea,
                    selected_video_type_detail=st.session_state.selected_video_type_detail,
                    shot_count=int(st.session_state.shot_count),
                    has_person_reference=bool(st.session_state.person_reference_images),
                    has_product_reference=bool(st.session_state.product_reference_images),
                )

            normalized_rows = []
            for row in rows:
                row["use_custom_base_image"] = False
                row["selected_base_image_path"] = ""
                normalized_rows.append(row)

            st.session_state.storyboard_table = normalized_rows
            st.session_state.storyboard_images = []
            st.session_state.storyboard_videos = []
            st.success(f"已生成 {len(rows)} 条分镜。可以去左侧「② 分镜表编辑」查看。")


# =========================
# 页面 2：分镜表编辑
# =========================

elif page == "② 分镜表编辑":
    st.header("🧁 ② 生成并编辑分镜表")

    if not st.session_state.storyboard_table:
        st.info("请先到左侧「① 需求与素材」生成分镜表。")
    else:
        editable_columns = [
            "shot_id",
            "time_sequence",
            "subject",
            "subject_action",
            "scene",
            "shot_size",
            "camera_movement",
            "lighting",
            "mood",
            "subtitle",
            "reference_type",
            "negative_prompt",
        ]

        df = pd.DataFrame(st.session_state.storyboard_table)
        for col in editable_columns:
            if col not in df.columns:
                df[col] = ""

        edited_df = st.data_editor(
            df[editable_columns],
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
        )

        for i, row in enumerate(edited_df.to_dict("records")):
            for k, v in row.items():
                st.session_state.storyboard_table[i][k] = v

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🎀 生成分镜图提示词E", use_container_width=True):
                new_rows = []
                for row in st.session_state.storyboard_table:
                    rebuilt = build_image_prompt_from_fields(
                        row,
                        has_person_reference=bool(st.session_state.person_reference_images),
                        has_product_reference=bool(st.session_state.product_reference_images),
                    )
                    row["image_prompt_cn"] = rebuilt["image_prompt_cn"]
                    row["image_prompt_en"] = rebuilt["image_prompt_en"]
                    new_rows.append(row)

                st.session_state.storyboard_table = new_rows
                st.success("已重新生成所有分镜图提示词。")
                st.rerun()

        with col_b:
            if st.button("🫧 清空分镜图和分镜视频结果", use_container_width=True):
                st.session_state.storyboard_images = []
                st.session_state.storyboard_videos = []
                st.success("已清空生成结果。")
                st.rerun()


# =========================
# 页面 3：生成分镜图
# =========================

elif page == "③ 生成分镜图":
    st.header("🎀 ③ 生成分镜图")

    if not st.session_state.storyboard_table:
        st.info("请先到左侧「① 需求与素材」生成分镜表。")
    else:
        st.caption("每张分镜都可以单独选择是否垫底图，也可以先修改提示词，再生成图片。")

        top_col1, top_col2, top_col3 = st.columns([1, 1, 1])

        with top_col1:
            if st.button("💗 一键生成全部分镜图", use_container_width=True):
                with st.spinner("正在批量生成分镜图（保持人物/产品一致性）..."):
                    if image_service and hasattr(image_service, "generate_storyboard_images"):
                        progress = st.progress(0)

                        def update_progress(fraction):
                            progress.progress(fraction)

                        results = image_service.generate_storyboard_images(
                            shots=st.session_state.storyboard_table,
                            person_image_paths=st.session_state.get("person_reference_images", []),
                            product_image_paths=st.session_state.get("product_reference_images", []),
                            progress_callback=update_progress,
                        )
                        # 规范化结果
                        normalized = []
                        for r in results:
                            shot_id = r.get("shot_id", 0)
                            shot = next((s for s in st.session_state.storyboard_table if s.get("shot_id") == shot_id), None)
                            prompt = ""
                            if shot:
                                prompt = shot.get("image_prompt_cn") or shot.get("image_prompt_en") or ""
                            normalized.append(normalize_image_result(r, shot_id, r.get("used_reference_images", []), prompt))
                        results = normalized

                        st.session_state.storyboard_images = results
                        st.session_state.storyboard_videos = []
                        seed_info = results[0].get("seed") if results else ""
                        st.success(f"已生成 {len(results)} 张分镜图（一致性 seed: {seed_info}）。")
                    else:
                        st.error("image_service.generate_storyboard_images 不可用")
                    progress.empty()
                st.rerun()

        with top_col2:
            if st.button("🫧 清空已生成分镜图", use_container_width=True):
                st.session_state.storyboard_images = []
                st.session_state.storyboard_videos = []
                st.success("已清空分镜图。")
                st.rerun()

        with top_col3:
            st.info(f"当前共有 {len(st.session_state.storyboard_table)} 个分镜")

        reference_pool = build_reference_pool()
        card_cols = st.columns(3)

        for idx, shot in enumerate(st.session_state.storyboard_table):
            shot_id = int(shot.get("shot_id", idx + 1))
            image_result = get_image_result_by_shot_id(shot_id)

            with card_cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"<span class='shot-tag'>分镜 {shot_id}</span>", unsafe_allow_html=True)

                    if image_result and image_result.get("image_path") and Path(str(image_result["image_path"])).exists():
                        st.image(image_result["image_path"], use_container_width=True)
                    else:
                        st.markdown(
                            "<div class='placeholder-box'>暂无生成图<br>先看提示词<br>再点击按钮生成</div>",
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        f"<div class='shot-title'>{shot.get('subtitle', shot.get('time_sequence', '未命名分镜'))}</div>",
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"""
                        <div class='shot-meta'>
                        <b>时序：</b>{shot.get('time_sequence', '')}<br>
                        <b>主体：</b>{shot.get('subject', '')}<br>
                        <b>动作：</b>{shot.get('subject_action', '')}<br>
                        <b>场景：</b>{shot.get('scene', '')}<br>
                        <b>景别：</b>{shot.get('shot_size', '')}<br>
                        <b>镜头：</b>{shot.get('camera_movement', '')}<br>
                        <b>光影：</b>{shot.get('lighting', '')}<br>
                        <b>氛围：</b>{shot.get('mood', '')}<br>
                        <b>参考图类型：</b>{shot.get('reference_type', 'none')}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if image_result:
                        st.caption(f"生成状态：{image_result.get('mode', '')}")
                        if image_result.get("error"):
                            st.warning(image_result.get("error"))

                        used_refs = image_result.get("used_reference_images", [])
                        if used_refs:
                            with st.expander("查看本次生成使用的参考图路径"):
                                for ref in used_refs:
                                    st.caption(ref)

                    use_custom_default = bool(shot.get("use_custom_base_image", False))
                    use_custom = st.checkbox(
                        "这张分镜使用垫底图",
                        value=use_custom_default,
                        key=f"use_custom_base_{shot_id}",
                    )
                    shot["use_custom_base_image"] = use_custom

                    if use_custom:
                        if reference_pool:
                            labels = [x["label"] for x in reference_pool]
                            current_path = shot.get("selected_base_image_path", "")
                            default_index = 0

                            if current_path:
                                for j, item in enumerate(reference_pool):
                                    if item["path"] == current_path:
                                        default_index = j
                                        break

                            selected_label = st.selectbox(
                                "选择这张分镜使用的底图",
                                options=labels,
                                index=default_index,
                                key=f"base_selector_{shot_id}",
                            )

                            selected_path = next(item["path"] for item in reference_pool if item["label"] == selected_label)
                            shot["selected_base_image_path"] = selected_path
                            st.image(selected_path, width=120, caption="当前底图")
                        else:
                            st.info("你还没有上传任何参考图，所以暂时不能垫底图。")
                            shot["selected_base_image_path"] = ""
                    else:
                        shot["selected_base_image_path"] = ""

                    st.markdown("<div class='prompt-title'>中文分镜图提示词</div>", unsafe_allow_html=True)
                    new_prompt_cn = st.text_area(
                        "中文分镜图提示词",
                        value=shot.get("image_prompt_cn", ""),
                        key=f"prompt_cn_{shot_id}",
                        height=180,
                        label_visibility="collapsed",
                    )
                    shot["image_prompt_cn"] = new_prompt_cn

                    with st.expander("负面提示词 / 英文提示词"):
                        new_negative = st.text_area(
                            "负面提示词",
                            value=shot.get("negative_prompt", ""),
                            key=f"negative_{shot_id}",
                            height=90,
                        )
                        shot["negative_prompt"] = new_negative

                        new_prompt_en = st.text_area(
                            "英文提示词",
                            value=shot.get("image_prompt_en", ""),
                            key=f"prompt_en_{shot_id}",
                            height=120,
                        )
                        shot["image_prompt_en"] = new_prompt_en

                    if st.button(
                        f"💗 生成 / 重新生成分镜 {shot_id}",
                        key=f"gen_image_{shot_id}",
                        use_container_width=True,
                    ):
                        with st.spinner(f"正在生成分镜 {shot_id} 图片..."):
                            new_result = generate_one_storyboard_image(shot)

                        st.session_state.storyboard_images = replace_result_by_shot_id(
                            st.session_state.storyboard_images,
                            new_result,
                        )
                        st.session_state.storyboard_videos = []
                        st.success(f"分镜 {shot_id} 已生成。")
                        st.rerun()


# =========================
# 页面 4：生成视频
# =========================

elif page == "④ 生成分镜视频":
    st.header("🎬 ④ 生成分镜视频")

    if not st.session_state.storyboard_images:
        st.info("请先到左侧「③ 生成分镜图」生成分镜图。")
    else:
        if st.button("💗 一键生成全部分镜视频", use_container_width=True):
            results = []
            progress = st.progress(0)

            for idx, shot in enumerate(st.session_state.storyboard_table):
                result = generate_one_storyboard_video(shot)
                results.append(result)
                progress.progress((idx + 1) / len(st.session_state.storyboard_table))

            st.session_state.storyboard_videos = results
            st.success(f"已处理 {len(results)} 条分镜视频。")

        if st.session_state.storyboard_videos:
            for idx, shot in enumerate(st.session_state.storyboard_table):
                shot_id = int(shot.get("shot_id", idx + 1))
                result = get_video_result_by_shot_id(shot_id)

                with st.expander(f"分镜视频 {shot_id}"):
                    if result and result.get("video_path") and Path(str(result["video_path"])).exists():
                        st.video(result["video_path"])
                        st.caption(result["video_path"])
                    else:
                        st.warning("当前没有真实视频结果。")

                    if result and result.get("error"):
                        st.warning(result["error"])

                    new_video_prompt = st.text_area(
                        "分镜视频提示词",
                        value=shot.get("video_prompt", ""),
                        key=f"video_prompt_{shot_id}",
                        height=120,
                    )
                    shot["video_prompt"] = new_video_prompt


# =========================
# 页面 5：状态与导出
# =========================

elif page == "⑤ 状态与导出":
    st.header("📦 ⑤ 状态与导出")

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("人物图", len(st.session_state.person_reference_images))
    c2.metric("产品图", len(st.session_state.product_reference_images))
    c3.metric("分镜图", len(st.session_state.storyboard_images))
    c4.metric("分镜视频", len(st.session_state.storyboard_videos))

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.storyboard_table:
        st.subheader("分镜表预览")
        st.dataframe(pd.DataFrame(st.session_state.storyboard_table), use_container_width=True)

        csv = pd.DataFrame(st.session_state.storyboard_table).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "💗 下载分镜表 CSV",
            data=csv,
            file_name="storyboard_table.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("当前还没有分镜表。")