# 自媒体视频自动化工具

用 Python + Streamlit 搭建的短视频创作辅助工具 MVP。

## 功能

| 步骤 | 功能 | 状态 |
|------|------|------|
| Step 1 | 输入模糊需求 | ✅ 可用 |
| Step 2 | AI 列举 8-12 种视频形式 | ✅ 可用 |
| Step 3 | 生成脚本 + 分镜表 | ✅ 可用 |
| Step 4 | 上传底图 + 生成分镜图 | ✅ 流程可用（mock 占位图） |
| Step 5 | 生成分镜视频 | ⏳ 占位 |

## 项目结构

```
zmt_video_auto_tool/
├── app.py            # Streamlit 入口（运行这个）
├── llm_service.py    # 语言模型调用（OpenAI / mock）
├── prompts.py        # 提示词模板
├── image_service.py  # 生图服务（底图 + 提示词 → 分镜图）
├── video_service.py  # 生视频服务（占位）
├── outputs/
│   ├── base_images/        # 用户上传的底图
│   └── storyboard_images/  # 生成的分镜图
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 进入项目目录

```bash
cd /Users/huxinyueshidameinv/Desktop/zmt_video_auto_tool
```

### 2. 激活虚拟环境

```bash
source .venv/bin/activate
```

如果还没有虚拟环境，先创建并安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 启动应用

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

### 4. （可选）配置 OpenAI API Key

不配置也能跑——Step 1-3 会使用 mock 假数据。

要使用真实 AI 生成视频形式和脚本分镜，在项目根目录创建 `.env` 文件：

```
OPENAI_API_KEY=sk-你的密钥
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.tu-zi.com/v1
```

保存后重启 Streamlit 即可。

## 使用流程

1. **Step 1**：输入需求，如「我想做美妆赛道自媒体账号」，点击「生成视频形式」
2. **Step 2**：从 8-12 种形式中点击选择一个（如「口播」「妆前妆后」）
3. **Step 3**：点击「生成脚本和分镜」，查看完整脚本和每个分镜的详细信息
4. **Step 4**：上传底图 → 预览 → 点击「生成分镜图（底图 + 分镜提示词）」
5. **Step 5**：第一版显示占位提示，后续版本接入生视频 API

## Step 4：上传底图生成分镜图

Step 4 支持「底图 + 分镜提示词」批量生成分镜图：

1. 完成 Step 3，确保已有分镜表
2. 在 Step 4 上传一张底图（png / jpg / jpeg），作为所有分镜共用的参考图
3. 页面会显示底图预览
4. 点击 **「生成分镜图（底图 + 分镜提示词）」**
5. 系统会遍历每个分镜，读取其 `image_prompt`，结合底图生成对应分镜图
6. 每个分镜结果区域展示：
   - 分镜编号
   - 生成的分镜图
   - 对应的 `image_prompt`
   - 当前使用的底图文件名

**文件保存位置：**

- 上传底图：`outputs/base_images/`
- 生成分镜图：`outputs/storyboard_images/`

**当前版本说明：** 尚未接入真实生图 API，点击生成后会基于底图创建 **mock 占位图**（带分镜编号和提示词标注），用于跑通完整流程。后续可在 `image_service.py` 的 `generate_storyboard_image()` 中接入 DALL·E 等 API。

## 分镜表字段说明

每个分镜包含：

- 分镜编号
- 画面内容
- 台词/字幕
- 场景
- 人物动作
- 镜头运动
- 生图提示词（英文，供 AI 绘图）
- 视频提示词（英文，供 AI 生视频）

## 常见问题

**Q：页面刷新后内容会消失吗？**  
A：不会。底图路径、生成结果等保存在 `st.session_state` 中，同一次会话内刷新不会丢失。

**Q：没有 API Key 能用吗？**  
A：可以。Step 1-3 会自动使用 mock 假数据；Step 4 会生成 mock 占位分镜图。

**Q：底图和分镜图存在哪里？**  
A：在项目目录下的 `outputs/base_images/` 和 `outputs/storyboard_images/`。

**Q：怎么停止应用？**  
A：在终端按 `Ctrl + C`。
