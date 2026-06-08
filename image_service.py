"""图片生成服务：支持图生图、每张分镜自定义底图、失败回退 mock"""

import base64
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageOps

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "outputs"
STORYBOARD_IMAGE_DIR = OUTPUT_DIR / "storyboard_images"
BASE_IMAGE_DIR = OUTPUT_DIR / "base_images"

STORYBOARD_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
BASE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT_DIR / ".env")


def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_openai_api_key() -> str:
    return _get_env("OPENAI_API_KEY")


def get_openai_base_url() -> str:
    return _get_env("OPENAI_BASE_URL")


def get_image_model() -> str:
    return _get_env("IMAGE_MODEL", "gpt-image-1")


def get_image_size() -> str:
    return _get_env("IMAGE_SIZE", "1024x1024")


def get_image_quality() -> str:
    return _get_env("IMAGE_QUALITY", "auto")


def is_image_api_available() -> bool:
    return bool(get_openai_api_key()) and OpenAI is not None


def get_image_api_status_message() -> str:
    if not get_openai_api_key():
        return "未配置 OPENAI_API_KEY，当前会使用 mock 占位图"

    if OpenAI is None:
        return "openai SDK 未成功导入，当前会使用 mock 占位图"

    base_url = get_openai_base_url() or "官方默认地址"
    model = get_image_model()
    return f"真实生图模式：IMAGE_MODEL={model} | BASE_URL={base_url}"


def _get_client():
    if not is_image_api_available():
        return None

    kwargs = {"api_key": get_openai_api_key()}
    base_url = get_openai_base_url()
    if base_url:
        kwargs["base_url"] = base_url

    return OpenAI(**kwargs)


def _make_output_path(shot_id: Optional[int], suffix: str = ".png") -> Path:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    rand = uuid.uuid4().hex[:6]
    if shot_id is None:
        filename = f"storyboard_{timestamp}_{rand}{suffix}"
    else:
        filename = f"shot_{shot_id}_{timestamp}_{rand}{suffix}"
    return STORYBOARD_IMAGE_DIR / filename


def _read_image_file(path: str):
    return open(path, "rb")


def _download_image(url: str, output_path: Path) -> str:
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    return str(output_path)


def _save_b64_image(b64_data: str, output_path: Path) -> str:
    image_bytes = base64.b64decode(b64_data)
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    return str(output_path)


def save_base_image(uploaded_file, prefix: str = "base") -> str:
    suffix = Path(uploaded_file.name).suffix.lower() or ".png"
    filename = f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:6]}{suffix}"
    path = BASE_IMAGE_DIR / filename
    with open(path, "wb") as f:
        f.write(uploaded_file.getvalue())
    return str(path)


def _select_reference_images(
    reference_type: str = "none",
    base_image_path: Optional[str] = None,
    person_image_paths: Optional[List[str]] = None,
    product_image_paths: Optional[List[str]] = None,
) -> List[str]:
    """
    选择参考图逻辑：
    1. 如果用户这张分镜手动指定了底图，优先使用这张底图
    2. 否则再按 reference_type 自动选人物图 / 产品图
    """
    person_image_paths = person_image_paths or []
    product_image_paths = product_image_paths or []

    if base_image_path and Path(base_image_path).exists():
        return [base_image_path]

    reference_type = (reference_type or "none").lower().strip()

    if reference_type == "person":
        return [p for p in person_image_paths[:1] if Path(p).exists()]

    if reference_type == "product":
        return [p for p in product_image_paths[:1] if Path(p).exists()]

    if reference_type == "both":
        selected = []
        if person_image_paths:
            selected.append(person_image_paths[0])
        if product_image_paths:
            selected.append(product_image_paths[0])
        return [p for p in selected if Path(p).exists()]

    return []


def _build_final_prompt(
    image_prompt: str,
    reference_type: str = "none",
    has_reference_images: bool = False,
    negative_prompt: str = "",
) -> str:
    lock_rules = []

    if has_reference_images and reference_type in ["person", "both"]:
        lock_rules.append(
            "基于上传参考图中的同一位人物进行图生图，保持人物身份、脸型、五官、发型、气质一致，不要换脸，不要改变性别，不要改变年龄感。"
        )

    if has_reference_images and reference_type in ["product", "both"]:
        lock_rules.append(
            "如画面涉及产品，请基于上传参考图中的同一产品进行图生图，保持产品包装、颜色、材质、外观形态一致。"
        )

    style_rules = (
        "整体画面真实自然，适合自媒体短视频分镜图，生活化、纪实感、手机随手拍质感，不要棚拍摄影光的精致感。"
    )

    if not negative_prompt:
        negative_prompt = (
            "不要棚拍摄影光的精致感，不要过度磨皮，不要夸张美颜，不要塑料感，"
            "不要人物变形，不要五官漂移，不要额外多手多脚，不要水印，不要文字，不要logo。"
        )

    final_prompt = "\n".join(
        [*lock_rules, image_prompt, style_rules, f"负面提示词：{negative_prompt}"]
    )

    return final_prompt.strip()


def _create_mock_image(
    shot_id: Optional[int],
    image_prompt: str,
    used_reference_images: Optional[List[str]] = None,
    error: str = "",
) -> str:
    used_reference_images = used_reference_images or []

    output_path = _make_output_path(shot_id, ".png")
    width, height = 1024, 1024

    if used_reference_images and Path(used_reference_images[0]).exists():
        try:
            img = Image.open(used_reference_images[0]).convert("RGB")
            img = ImageOps.contain(img, (width, height))
            canvas = Image.new("RGB", (width, height), (245, 245, 245))
            x = (width - img.width) // 2
            y = (height - img.height) // 2
            canvas.paste(img, (x, y))
            img = canvas
        except Exception:
            img = Image.new("RGB", (width, height), (245, 245, 245))
    else:
        img = Image.new("RGB", (width, height), (245, 245, 245))

    draw = ImageDraw.Draw(img)
    overlay_height = 280
    overlay_y = height - overlay_height
    draw.rectangle((0, overlay_y, width, height), fill=(0, 0, 0))

    short_prompt = image_prompt.replace("\n", " ")[:240]
    short_error = error.replace("\n", " ")[:180]

    lines = [
        f"分镜 {shot_id if shot_id is not None else ''} - MOCK 占位图",
        "API失败，已回退 mock",
        f"Error: {short_error}" if short_error else "",
        f"Prompt: {short_prompt}",
    ]

    y = overlay_y + 24
    for line in lines:
        if not line:
            continue
        draw.text((30, y), line, fill=(255, 230, 120))
        y += 44

    img.save(output_path)
    return str(output_path)


def _extract_and_save_image_from_response(response: Any, output_path: Path) -> str:
    if hasattr(response, "data") and response.data:
        item = response.data[0]

        if hasattr(item, "b64_json") and item.b64_json:
            return _save_b64_image(item.b64_json, output_path)

        if hasattr(item, "url") and item.url:
            return _download_image(item.url, output_path)

        if isinstance(item, dict):
            if item.get("b64_json"):
                return _save_b64_image(item["b64_json"], output_path)
            if item.get("url"):
                return _download_image(item["url"], output_path)

    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, list) and data:
            item = data[0]
            if item.get("b64_json"):
                return _save_b64_image(item["b64_json"], output_path)
            if item.get("url"):
                return _download_image(item["url"], output_path)

    raise RuntimeError(f"无法识别图片 API 返回格式：{response}")


def _try_image_edit(
    client: Any,
    final_prompt: str,
    reference_images: List[str],
    shot_id: Optional[int],
) -> str:
    output_path = _make_output_path(shot_id, ".png")
    model = get_image_model()
    size = get_image_size()

    opened_files = []
    try:
        for p in reference_images:
            opened_files.append(_read_image_file(p))

        image_arg = opened_files[0] if len(opened_files) == 1 else opened_files

        response = client.images.edit(
            model=model,
            image=image_arg,
            prompt=final_prompt,
            size=size,
        )

        return _extract_and_save_image_from_response(response, output_path)
    finally:
        for f in opened_files:
            try:
                f.close()
            except Exception:
                pass


def _try_image_generate(
    client: Any,
    final_prompt: str,
    shot_id: Optional[int],
) -> str:
    output_path = _make_output_path(shot_id, ".png")
    model = get_image_model()
    size = get_image_size()

    response = client.images.generate(
        model=model,
        prompt=final_prompt,
        size=size,
    )

    return _extract_and_save_image_from_response(response, output_path)


def generate_storyboard_image(
    image_prompt: Optional[str] = None,
    prompt: Optional[str] = None,
    base_image_path: Optional[str] = None,
    reference_type: str = "none",
    person_image_paths: Optional[List[str]] = None,
    product_image_paths: Optional[List[str]] = None,
    shot_id: Optional[int] = None,
    negative_prompt: str = "",
) -> Dict[str, Any]:
    raw_prompt = image_prompt or prompt or ""

    used_reference_images = _select_reference_images(
        reference_type=reference_type,
        base_image_path=base_image_path,
        person_image_paths=person_image_paths,
        product_image_paths=product_image_paths,
    )

    final_prompt = _build_final_prompt(
        image_prompt=raw_prompt,
        reference_type=reference_type,
        has_reference_images=bool(used_reference_images),
        negative_prompt=negative_prompt,
    )

    if not is_image_api_available():
        image_path = _create_mock_image(
            shot_id=shot_id,
            image_prompt=final_prompt,
            used_reference_images=used_reference_images,
            error="未配置可用生图 API",
        )
        return {
            "image_path": image_path,
            "used_reference_images": used_reference_images,
            "mode": "mock",
            "error": "未配置可用生图 API",
        }

    client = _get_client()

    if used_reference_images:
        try:
            image_path = _try_image_edit(
                client=client,
                final_prompt=final_prompt,
                reference_images=used_reference_images,
                shot_id=shot_id,
            )
            return {
                "image_path": image_path,
                "used_reference_images": used_reference_images,
                "mode": "real_api_edit",
                "error": "",
            }
        except Exception as edit_error:
            try:
                image_path = _try_image_generate(
                    client=client,
                    final_prompt=final_prompt,
                    shot_id=shot_id,
                )
                return {
                    "image_path": image_path,
                    "used_reference_images": used_reference_images,
                    "mode": "real_api_generate_fallback",
                    "error": f"图生图失败，已退回文生图。原错误：{edit_error}",
                }
            except Exception as gen_error:
                image_path = _create_mock_image(
                    shot_id=shot_id,
                    image_prompt=final_prompt,
                    used_reference_images=used_reference_images,
                    error=f"图生图失败：{edit_error}；文生图失败：{gen_error}",
                )
                return {
                    "image_path": image_path,
                    "used_reference_images": used_reference_images,
                    "mode": "mock",
                    "error": f"图生图失败：{edit_error}；文生图失败：{gen_error}",
                }

    try:
        image_path = _try_image_generate(
            client=client,
            final_prompt=final_prompt,
            shot_id=shot_id,
        )
        return {
            "image_path": image_path,
            "used_reference_images": used_reference_images,
            "mode": "real_api_generate",
            "error": "",
        }
    except Exception as gen_error:
        image_path = _create_mock_image(
            shot_id=shot_id,
            image_prompt=final_prompt,
            used_reference_images=used_reference_images,
            error=str(gen_error),
        )
        return {
            "image_path": image_path,
            "used_reference_images": used_reference_images,
            "mode": "mock",
            "error": str(gen_error),
        }


def generate_storyboard_images(
    shots: List[Dict[str, Any]],
    base_image_path: Optional[str] = None,
    person_image_paths: Optional[List[str]] = None,
    product_image_paths: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    results = []
    for shot in shots:
        result = generate_storyboard_image(
            image_prompt=shot.get("image_prompt_cn") or shot.get("image_prompt_en") or "",
            base_image_path=shot.get("selected_base_image_path") if shot.get("use_custom_base_image") else base_image_path,
            reference_type=shot.get("reference_type", "none"),
            person_image_paths=person_image_paths,
            product_image_paths=product_image_paths,
            shot_id=shot.get("shot_id"),
            negative_prompt=shot.get("negative_prompt", ""),
        )
        result["shot_id"] = shot.get("shot_id")
        results.append(result)
    return results