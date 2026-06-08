"""分镜视频生成服务（第一版占位，暂未接入真实 API）。"""


def generate_storyboard_videos(storyboard: list[dict]) -> dict:
    """
    根据分镜表生成分镜视频。
    第一版返回占位信息，后续可接入 Runway、Pika 等。
    """
    return {
        "status": "not_connected",
        "message": "暂未接入视频 API",
        "videos": [],
    }
