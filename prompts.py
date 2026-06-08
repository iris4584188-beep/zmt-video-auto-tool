# prompts.py

VIDEO_TYPE_GENERATION_PROMPT = """
你是一个专业短视频内容策划专家。

用户输入的模糊需求是：
{user_idea}

请你先判断用户想做的账号赛道，然后生成 8-12 个适合该赛道的视频类型。

要求：
1. 视频类型必须和用户输入的赛道强相关。
2. 如果用户输入健身赛道，不要出现妆前妆后、沉浸式护肤等美妆专属类型。
3. 如果用户输入美妆赛道，可以出现美妆vlog、妆前妆后、护肤流程、产品测评等类型。
4. 如果用户输入口播赛道，可以出现干货口播、观点输出、案例拆解等类型。
5. 每个视频类型都要包含 type_name、description、suitable_for、system_prompt。
6. 输出严格 JSON 数组，不要输出任何解释。

JSON 格式：
[
  {
    "type_name": "健身vlog",
    "description": "以第一视角记录训练、饮食和生活状态，适合打造真实健身人设",
    "suitable_for": "健身、减脂、塑形、运动生活方式账号",
    "system_prompt": "生成真实生活感、训练感、运动氛围强的健身vlog分镜表"
  }
]
"""

STORYBOARD_TABLE_PROMPT = """
你是一个专业短视频分镜导演，也是 AI 生图提示词专家。

用户模糊需求：
{user_idea}

用户选择的视频类型：
{selected_video_type}

该视频类型的系统提示词：
{type_system_prompt}

需要生成的分镜数量：
{shot_count}

请直接生成结构化分镜表，不要生成长篇视频脚本。

每个分镜必须包含以下字段：
1. shot_id：分镜编号
2. time_sequence：时序
3. subject：人物主体
4. subject_action：人物主体动作
5. scene：场景
6. shot_size：景别
7. camera_movement：镜头运动
8. lighting：光影
9. mood：氛围
10. subtitle：字幕/台词
11. negative_prompt：负面提示词
12. reference_type：参考图类型，只能是 none / person / product / both
13. image_prompt_cn：中文分镜图提示词
14. image_prompt_en：英文分镜图提示词
15. video_prompt：分镜视频提示词

生成 image_prompt_cn 和 image_prompt_en 时，必须围绕这些维度：
时序、人物主体、人物主体动作、景别、镜头运动、光影、氛围、负面提示词。

负面提示词示例：
不要棚拍摄影光的精致感、不要过度磨皮、不要夸张美颜、不要塑料感、不要水印、不要文字、不要杂乱背景。

输出严格 JSON 数组，不要输出解释。
"""

VIDEO_TYPE_PROMPTS = {
    "通用": "生成适合短视频平台的真实、清晰、可执行分镜表。",
    "健身": "重点突出训练动作、身体状态、运动氛围、真实健身房或居家运动场景。",
    "美妆": "重点突出妆容变化、产品使用、肤质状态、细节特写和真实生活感。",
    "口播": "重点突出人物表达、观点输出、字幕节奏、镜头稳定和内容逻辑。",
}