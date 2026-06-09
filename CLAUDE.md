# CLAUDE.md — 自媒体视频分镜自动化工具

> **每次新会话开始时，Claude Code 会自动读取本文件以获取项目上下文。**
> 请保持本文件更新，特别是「当前进度」部分。

---

## 项目概述

用 Python + Streamlit 搭建的短视频创作辅助工具。核心流程：
**模糊需求 → 分镜表 → 分镜图（底图+提示词） → 分镜视频**

## 如何运行

```bash
cd /Users/huxinyueshidameinv/Desktop/zmt_video_auto_tool
source .venv/bin/activate
streamlit run app.py
# 浏览器访问 http://localhost:8501
```

## 技术栈

- **前端:** Streamlit 1.58（玫粉色自定义 CSS 主题）
- **LLM:** OpenAI API（通过 `api.tu-zi.com/v1` 代理），模型 `gpt-4o-mini`，response_format json_object
- **生图:** OpenAI Images API（模型 `gpt-image-1`），先尝试 `images.edit`（图生图），失败回退 `images.generate`（文生图），再失败回退 mock
- **生视频:** 当前仅占位，未接入任何 API
- **Python:** 3.14，依赖见 requirements.txt

## 项目结构

```
zmt_video_auto_tool/
├── app.py                # Streamlit 主入口（~1200行），5个页面用 radio 切换
├── llm_service.py        # LLM：生成分镜表 + 构建分镜图提示词
├── prompts.py            # 提示词模板（可能部分未被引用）
├── image_service.py      # 生图服务，支持 图生图/文生图/mock 三级回退
├── video_service.py      # 生视频服务（占位，14行）
├── outputs/
│   ├── reference_images/person/   # 上传的人物参考图
│   ├── reference_images/product/  # 上传的产品参考图
│   ├── storyboard_images/         # 生成的分镜图
│   └── storyboard_videos/         # 生成的分镜视频
├── utils/                # 几乎未使用
├── .env                  # API 密钥（已 gitignore）
├── .venv/                # 虚拟环境（已 gitignore）
├── requirements.txt
└── README.md
```

## 架构要点

### 5页工作流（app.py 中用 `st.session_state.current_page` radio 切换）

| 页面 | 功能 | 状态 |
|------|------|------|
| ① 需求与素材 | 输入需求、选视频类型、上传参考图、生成分镜表 | ✅ |
| ② 分镜表编辑 | Data Editor 编辑分镜字段、重新生成提示词 | ✅ |
| ③ 生成分镜图 | 单张/批量生成、支持每分镜独立选择垫底图 | ✅ |
| ④ 生成分镜视频 | 分镜图→视频 | ⏳ 占位 |
| ⑤ 状态与导出 | 统计面板 + CSV 导出 | ✅ |

### 分镜表数据结构（每个分镜字段）

`shot_id`, `time_sequence`, `subject`, `subject_action`, `scene`, `shot_size`, `camera_movement`, `lighting`, `mood`, `subtitle`, `negative_prompt`, `reference_type` (person/product/both/none), `image_prompt_cn`, `image_prompt_en`, `video_prompt`, `use_custom_base_image`, `selected_base_image_path`

### session_state 关键变量

- `user_idea`: 用户输入的需求文本
- `selected_video_type_detail`: 当前选中的视频类型 dict
- `shot_count`: 分镜数量（1-30）
- `person_reference_images` / `product_reference_images`: 上传参考图路径列表
- `storyboard_table`: 分镜表 list[dict]
- `storyboard_images`: 生成结果 list[dict]
- `storyboard_videos`: 视频结果 list[dict]
- `current_page`: 当前页面

### 生图回退链路

```
image_service.generate_storyboard_image()
  → 有参考图? → images.edit()（图生图）+ seed 一致性
    → 失败? → images.generate()（文生图）+ seed 一致性
      → 失败? → mock 占位图
  → 无参考图? → images.generate()
    → 失败? → mock 占位图
```

### 跨分镜一致性策略 (2026-06-08)

**链式逐帧传递（核心方案）：**
```
shot_1 的垫图 = 合成(person_ref + product_ref)
    ↓ images.edit + seed
 output_1 ──→ shot_2 的垫图 = 合成(person_ref + product_ref + output_1)
    ↓ images.edit + seed
 output_2 ──→ shot_3 的垫图 = 合成(person_ref + product_ref + output_2)
    ↓ images.edit + seed
 output_3 ...
```

1. **共享 seed** — 同批所有分镜使用同一个随机种子
2. **3 列参考图合成** — person(左1/6) + product(中1/6) + 上一帧(右4/6主视觉区)，合成为单张 1024x1024 垫图
3. **链式视觉延续** — prompt 注入【链式延续】指令：继承上一帧的光影调性、色彩风格、人物外貌、场景质感
4. **内容精准控制** — prompt 注入【画面内容】指令，按 reference_type 区分 person / product / both / none

## 当前进度

- **上次工作内容 (2026-06-08):**
  1. 视频类型改版：8 种通用类型 → 3 种产品种草型（数字人口播+产品展示 / 纯产品+画外音 / 沉浸式无口播），每种携带详细编导 system_prompt
  2. API 修复：适配 api.tu-zi.com 代理升级（gpt-4o-mini → gpt-5.4-mini + stream=True）
  3. 分镜图提示词重构：按 AGENT_TASK.md 的 5 核心维度（主体/主体动作/光影/氛围调性/景别）生成 AIGC 风格提示词
  4. 跨分镜一致性方案实施：共享 seed + 参考图合成 + 一致性锚点 + 内容精准控制
- **待完成:**
  1. 接入视频生成 API（Runway / Pika / Kling / 即梦 等）
  2. 考虑拆分 app.py（1200行单体文件，维护困难）
- **已知问题:**
  - `prompts.py` 中的 `VIDEO_TYPE_GENERATION_PROMPT` 等可能未被实际调用（app.py 直接用了内置的 `UNIVERSAL_VIDEO_TYPES` 列表）
  - `video_service.py` 只有 14 行，完全未实现
  - 备份文件 `*_backup_before_manual.py` 散落在项目根目录
  - `button` 和 `button:hover` 是空文件（可能是误创建的）

---

## 修改后务必更新本文件

每次完成重要改动后，请更新上面「当前进度」部分，确保下次会话能准确了解最新状态。
