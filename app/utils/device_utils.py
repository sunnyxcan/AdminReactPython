# backend/app/utils/device_utils.py

from user_agents import parse

def detect_device_info(user_agent_string: str) -> dict:
    """
    Mendeteksi jenis perangkat, OS, dan browser dari string User-Agent.
    Mengembalikan dictionary dengan informasi yang terstruktur.
    """
    if not user_agent_string:
        return {
            "device": "Unknown",
            "os": "Unknown",
            "browser": "Unknown"
        }

    user_agent = parse(user_agent_string)

    return {
        "device": {
            "is_mobile": user_agent.is_mobile,
            "is_tablet": user_agent.is_tablet,
            "is_pc": user_agent.is_pc,
            "is_touch_capable": user_agent.is_touch_capable,
            "is_bot": user_agent.is_bot
        },
        "os": {
            "family": user_agent.os.family,
            "version_string": user_agent.os.version_string
        },
        "browser": {
            "family": user_agent.browser.family,
            "version_string": user_agent.browser.version_string
        }
    }