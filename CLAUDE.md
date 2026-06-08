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
  → 有参考图? → images.edit()（图生图）
    → 失败? → images.generate()（文生图）
      → 失败? → mock 占位图
  → 无参考图? → images.generate()
    → 失败? → mock 占位图
```

## 当前进度

- **上次工作内容:** 项目代码审查，建立 CLAUDE.md 和 git 仓库
- **待完成:**
  1. 接入视频生成 API（Runway / Pika / Kling / 即梦 等）
  2. 改进分镜表生成的 prompt engineering（目前 LLM 生成质量有限）
  3. 考虑拆分 app.py（1200行单体文件，维护困难）
- **已知问题:**
  - `prompts.py` 中的 `VIDEO_TYPE_GENERATION_PROMPT` 等可能未被实际调用（app.py 直接用了内置的 `UNIVERSAL_VIDEO_TYPES` 列表）
  - `video_service.py` 只有 14 行，完全未实现
  - 备份文件 `*_backup_before_manual.py` 散落在项目根目录
  - `button` 和 `button:hover` 是空文件（可能是误创建的）

---

## 修改后务必更新本文件

每次完成重要改动后，请更新上面「当前进度」部分，确保下次会话能准确了解最新状态。
