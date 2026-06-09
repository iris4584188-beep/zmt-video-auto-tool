"""图片生成服务：支持图生图、每张分镜自定义底图、失败回退 mock、跨分镜一致性"""

import base64
import os
import random
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
COMPOSITE_CACHE_DIR = OUTPUT_DIR / ".composite_cache"

STORYBOARD_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
BASE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
COMPOSITE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

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


def _composite_reference_images(
    person_paths: List[str],
    product_paths: List[str],
    chain_anchor: Optional[str] = None,
) -> Optional[str]:
    """合成参考图为单张 1024x1024 图片，用于 images.edit 的单图输入。

    三种模式：
    - 无 chain_anchor：2 列布局，左人物 + 右产品
    - 有 chain_anchor：3 列布局，左人物 + 中产品 + 右上一帧（主视觉参考区）
    结果缓存到 COMPOSITE_CACHE_DIR。
    """
    valid_person = [p for p in (person_paths or [])[:1] if Path(p).exists()]
    valid_product = [p for p in (product_paths or [])[:1] if Path(p).exists()]
    has_chain = chain_anchor and Path(chain_anchor).exists()

    if not valid_person and not valid_product and not has_chain:
        return None

    # 如果只有一种来源，直接返回
    if len(valid_person) + len(valid_product) + (1 if has_chain else 0) == 1:
        if valid_person:
            return valid_person[0]
        if valid_product:
            return valid_product[0]
        if has_chain:
            return chain_anchor

    # 构建缓存 key
    parts = []
    for p in valid_person:
        parts.append(f"p_{Path(p).stem}_{Path(p).stat().st_mtime}")
    for p in valid_product:
        parts.append(f"q_{Path(p).stem}_{Path(p).stat().st_mtime}")
    if has_chain:
        parts.append(f"c_{Path(chain_anchor).stem}")
    cache_path = COMPOSITE_CACHE_DIR / f"composite_{'_'.join(parts)}.png"

    if cache_path.exists():
        return str(cache_path)

    try:
        canvas = Image.new("RGB", (1024, 1024), (245, 245, 245))

        if has_chain:
            # 3 列布局：人物(左 1/6) | 产品(中 1/6) | 上一帧(右 4/6 主视觉)
            left_w = 240   # 两小列各 240px
            mid_x = 256    # 产品列起始
            right_x = 512  # 上一帧起始，512px 宽
            right_w = 512

            if valid_person:
                person_resized = ImageOps.contain(Image.open(valid_person[0]).convert("RGB"), (left_w - 8, 1020))
                px = (left_w - person_resized.width) // 2
                py = (1024 - person_resized.height) // 2
                canvas.paste(person_resized, (px, py))

            if valid_product:
                product_resized = ImageOps.contain(Image.open(valid_product[0]).convert("RGB"), (right_x - mid_x - 8, 1020))
                qx = mid_x + ((right_x - mid_x) - product_resized.width) // 2
                qy = (1024 - product_resized.height) // 2
                canvas.paste(product_resized, (qx, qy))

            # 上一帧 — 占右侧主区域，作为 images.edit 的主要视觉参考
            chain_img = Image.open(chain_anchor).convert("RGB")
            chain_resized = ImageOps.contain(chain_img, (right_w - 8, 1020))
            cx = right_x + (right_w - chain_resized.width) // 2
            cy = (1024 - chain_resized.height) // 2
            canvas.paste(chain_resized, (cx, cy))

            # 分隔线
            draw = ImageDraw.Draw(canvas)
            draw.rectangle((left_w, 0, left_w + 4, 1024), fill=(200, 200, 200))
            draw.rectangle((right_x - 4, 0, right_x, 1024), fill=(200, 200, 200))
        else:
            # 2 列布局（无 chain）：左人物 右产品
            person_resized = ImageOps.contain(Image.open(valid_person[0]).convert("RGB"), (480, 960))
            px = (480 - person_resized.width) // 2
            py = (1024 - person_resized.height) // 2
            canvas.paste(person_resized, (px, py))

            product_resized = ImageOps.contain(Image.open(valid_product[0]).convert("RGB"), (480, 480))
            qx = 512 + (512 - product_resized.width) // 2
            qy = (1024 - product_resized.height) // 2
            canvas.paste(product_resized, (qx, qy))

            draw = ImageDraw.Draw(canvas)
            draw.rectangle((505, 0, 519, 1024), fill=(220, 220, 220))

        canvas.save(cache_path)
        return str(cache_path)
    except Exception:
        # 合成失败时按优先级降级
        if has_chain:
            return chain_anchor
        if valid_person:
            return valid_person[0]
        if valid_product:
            return valid_product[0]
        return None


def _select_reference_images(
    reference_type: str = "none",
    base_image_path: Optional[str] = None,
    person_image_paths: Optional[List[str]] = None,
    product_image_paths: Optional[List[str]] = None,
    chain_anchor: Optional[str] = None,
) -> List[str]:
    """
    选择/合成参考图。返回单张图的列表（images.edit 只接受一个 image 参数）。

    优先级：
    1. 用户手动指定的底图
    2. chain_anchor 存在时：合成 person + product + chain_anchor 为单图
    3. 无 chain_anchor 时：按 reference_type 选图
    """
    person_image_paths = person_image_paths or []
    product_image_paths = product_image_paths or []

    if base_image_path and Path(base_image_path).exists():
        return [base_image_path]

    reference_type = (reference_type or "none").lower().strip()

    # 有链式锚点时，始终合成所有可用源为单图
    has_chain = chain_anchor and Path(chain_anchor).exists()

    if reference_type == "both" or has_chain:
        composite = _composite_reference_images(person_image_paths, product_image_paths, chain_anchor)
        return [composite] if composite else []

    if reference_type == "person":
        if has_chain:
            composite = _composite_reference_images(person_image_paths, [], chain_anchor)
            return [composite] if composite else []
        return [p for p in person_image_paths[:1] if Path(p).exists()]

    if reference_type == "product":
        if has_chain:
            composite = _composite_reference_images([], product_image_paths, chain_anchor)
            return [composite] if composite else []
        return [p for p in product_image_paths[:1] if Path(p).exists()]

    # "none" — 但有 chain_anchor 时也利用它
    if has_chain:
        return [chain_anchor]

    return []


def _build_final_prompt(
    image_prompt: str,
    reference_type: str = "none",
    has_reference_images: bool = False,
    has_chain: bool = False,
    negative_prompt: str = "",
) -> str:
    reference_type = (reference_type or "none").lower().strip()

    # --- 参考图身份锁定 ---
    lock_rules: List[str] = []

    if has_reference_images and reference_type in ["person", "both"]:
        lock_rules.append(
            "【身份锁定-人物】参考图中的人物必须保持一致：同一张脸、同一种五官、"
            "同一种发型、同一种气质、同一种年龄感。绝对不要换脸、不要改变性别、不要改变身份。"
        )

    if has_reference_images and reference_type in ["product", "both"]:
        lock_rules.append(
            "【身份锁定-产品】参考图中的产品必须保持一致：同一款包装、同一种颜色、"
            "同一种材质、同一种外观形态。绝对不要替换成其他产品。"
        )

    # --- 链式视觉延续 ---
    if has_chain:
        lock_rules.append(
            "【链式延续】垫图右上区域为上一分镜的输出图。"
            "必须延续上一分镜的光影调性、色彩风格、人物外貌和场景质感，"
            "只改变分镜提示词中指定的新动作和新构图，其他视觉元素原封不动继承。"
        )

    # --- 内容可见性指令 ---
    content_rules: List[str] = []
    if reference_type == "person":
        content_rules.append("【画面内容】画面中只出现人物主体，不出现任何产品。")
    elif reference_type == "product":
        content_rules.append("【画面内容】画面中只出现产品主体，不出现任何人物。")
    elif reference_type == "both":
        content_rules.append("【画面内容】画面中同时出现人物和产品，人物正在使用或展示产品。")
    elif reference_type == "none":
        content_rules.append("【画面内容】画面中只展示场景环境，不出现任何具体人物或产品。")

    style_rules = (
        "整体画面真实自然，适合自媒体短视频分镜图，生活化、纪实感、手机随手拍质感，不要棚拍摄影光的精致感。"
    )

    if not negative_prompt:
        negative_prompt = (
            "不要棚拍摄影光的精致感，不要过度磨皮，不要夸张美颜，不要塑料感，"
            "不要人物变形，不要五官漂移，不要额外多手多脚，不要水印，不要文字，不要logo。"
        )

    final_prompt = "\n".join(
        [*lock_rules, *content_rules, image_prompt, style_rules, f"负面提示词：{negative_prompt}"]
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
    seed: Optional[int] = None,
) -> str:
    output_path = _make_output_path(shot_id, ".png")
    model = get_image_model()
    size = get_image_size()

    opened_files = []
    try:
        for p in reference_images:
            opened_files.append(_read_image_file(p))

        # images.edit 只接受单张 image 参数
        image_arg = opened_files[0]

        kwargs: Dict[str, Any] = {
            "model": model,
            "image": image_arg,
            "prompt": final_prompt,
            "size": size,
        }

        if seed is not None:
            kwargs["extra_body"] = {"seed": seed}

        response = client.images.edit(**kwargs)
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
    seed: Optional[int] = None,
) -> str:
    output_path = _make_output_path(shot_id, ".png")
    model = get_image_model()
    size = get_image_size()

    kwargs: Dict[str, Any] = {
        "model": model,
        "prompt": final_prompt,
        "size": size,
    }

    if seed is not None:
        kwargs["extra_body"] = {"seed": seed}

    response = client.images.generate(**kwargs)
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
    seed: Optional[int] = None,
    chain_anchor: Optional[str] = None,
) -> Dict[str, Any]:
    raw_prompt = image_prompt or prompt or ""

    used_reference_images = _select_reference_images(
        reference_type=reference_type,
        base_image_path=base_image_path,
        person_image_paths=person_image_paths,
        product_image_paths=product_image_paths,
        chain_anchor=chain_anchor,
    )

    final_prompt = _build_final_prompt(
        image_prompt=raw_prompt,
        reference_type=reference_type,
        has_reference_images=bool(used_reference_images),
        has_chain=chain_anchor is not None and Path(chain_anchor).exists(),
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
            "seed": seed,
        }

    client = _get_client()

    if used_reference_images:
        try:
            image_path = _try_image_edit(
                client=client,
                final_prompt=final_prompt,
                reference_images=used_reference_images,
                shot_id=shot_id,
                seed=seed,
            )
            return {
                "image_path": image_path,
                "used_reference_images": used_reference_images,
                "mode": "real_api_edit",
                "error": "",
                "seed": seed,
            }
        except Exception as edit_error:
            try:
                image_path = _try_image_generate(
                    client=client,
                    final_prompt=final_prompt,
                    shot_id=shot_id,
                    seed=seed,
                )
                return {
                    "image_path": image_path,
                    "used_reference_images": used_reference_images,
                    "mode": "real_api_generate_fallback",
                    "error": f"图生图失败，已退回文生图。原错误：{edit_error}",
                    "seed": seed,
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
                    "seed": seed,
                }

    try:
        image_path = _try_image_generate(
            client=client,
            final_prompt=final_prompt,
            shot_id=shot_id,
            seed=seed,
        )
        return {
            "image_path": image_path,
            "used_reference_images": used_reference_images,
            "mode": "real_api_generate",
            "error": "",
            "seed": seed,
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
            "seed": seed,
        }


def generate_storyboard_images(
    shots: List[Dict[str, Any]],
    base_image_path: Optional[str] = None,
    person_image_paths: Optional[List[str]] = None,
    product_image_paths: Optional[List[str]] = None,
    progress_callback: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """批量生成分镜图，链式传递保证跨分镜人物/产品/风格完全一致。

    链式策略（核心）：
    ① 共享 seed — 整批同一个随机种子，保证视觉风格一致。
    ② 首帧合成 — shot_1 的垫图为 person + product 的合成图。
    ③ 逐帧链式 — shot_N 的垫图 = person + product + shot_{N-1} 的输出合成图。
       images.edit 看到前一帧的完整画面，自动延续人物外貌、产品外观、光影色调。
    ④ 内容指令 — prompt 注入【画面内容】，精确控制每镜出现什么元素。
    """
    if not shots:
        return []

    batch_seed = random.randint(1, 2_147_483_647)

    # 统一 subject 描述（所有涉及人物的分镜使用相同人物描述）
    person_subject_template = ""
    for shot in shots:
        ref_type = (shot.get("reference_type") or "none").lower().strip()
        if ref_type in ["person", "both"]:
            person_subject_template = shot.get("subject", "")
            if person_subject_template:
                break

    results: List[Dict[str, Any]] = []
    chain_anchor: Optional[str] = None  # 关键：前一张的输出路径

    for idx, shot in enumerate(shots):
        shot_id = shot.get("shot_id")

        # 统一人物描述
        if person_subject_template:
            ref_type = (shot.get("reference_type") or "none").lower().strip()
            if ref_type in ["person", "both"]:
                shot["subject"] = person_subject_template

        result = generate_storyboard_image(
            image_prompt=shot.get("image_prompt_cn") or shot.get("image_prompt_en") or "",
            base_image_path=shot.get("selected_base_image_path") if shot.get("use_custom_base_image") else base_image_path,
            reference_type=shot.get("reference_type", "none"),
            person_image_paths=person_image_paths,
            product_image_paths=product_image_paths,
            shot_id=shot_id,
            negative_prompt=shot.get("negative_prompt", ""),
            seed=batch_seed,
            chain_anchor=chain_anchor,  # ← 传入前一张的输出
        )
        result["shot_id"] = shot_id
        results.append(result)

        # 链式传递：当前输出成为下一张的 chain_anchor
        if result.get("image_path") and Path(result["image_path"]).exists():
            chain_anchor = result["image_path"]

        if progress_callback:
            progress_callback((idx + 1) / len(shots))

    return results