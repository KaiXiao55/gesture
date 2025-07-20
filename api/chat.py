from flask import Flask, request, jsonify
import os
import requests
import re
import json
from typing import List, Dict, Any

app = Flask(__name__)


class ChatLogic:
    def __init__(self):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_token = os.getenv("DEEPSEEK_API_TOKEN", "")

        self.system_prompt = """你是一个手势助手。用户会向你发送消息，你需要理解用户的情感和意图，
然后用一个合适的手势来回应。你的回复应该简短友好，像朋友之间的对话。
记住：你的主要任务是选择合适的手势，而不是长篇大论。"""

    def _clean_response(self, content: str) -> str:
        """清理模型的回复内容"""
        content = re.sub(r"\*\*.*?\*\*", "", content)
        content = re.sub(r"\n\s*\n", "\n", content)
        return content.strip()

    def get_response(self, messages: List[Dict[str, str]]) -> Dict:
        """获取模型回复"""
        full_messages = [{"role": "system", "content": self.system_prompt}] + messages

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        payload = {
            "model": "deepseek-chat",
            "messages": full_messages,
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False,
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=15
            )
            response.raise_for_status()
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"].get("content", "")
                cleaned_content = self._clean_response(content)

                return {"text": cleaned_content or "明白了！", "success": True}

        except Exception as e:
            print(f"API Error: {e}")
            return {"text": "抱歉，我现在无法回复。", "success": False}


class GestureSelector:
    """根据回复内容选择合适的手势"""

    @staticmethod
    def select_gesture(text):
        text = text.lower()

        # 检查问句
        if any(
            word in text
            for word in [
                "怎么样",
                "什么",
                "为什么",
                "如何",
                "哪里",
                "多少",
                "？",
                "吗",
                "呢",
            ]
        ):
            if any(greeting in text for greeting in ["你好", "嗨", "hello", "hi"]):
                return "wave"
            return "thinking"

        # 检查数字
        numbers = re.findall(r"([0-9]|10)", text)
        if numbers:
            return numbers[-1]

        # 中文数字
        chinese_numbers = {
            "零": "0",
            "一": "1",
            "二": "2",
            "三": "3",
            "四": "4",
            "五": "5",
            "六": "6",
            "七": "7",
            "八": "8",
            "九": "9",
            "十": "10",
        }
        for cn, num in chinese_numbers.items():
            if cn in text:
                return num

        # 关键词映射
        gesture_keywords = {
            "heart": [
                "爱",
                "喜欢",
                "亲",
                "么么",
                "想你",
                "爱你",
                "心",
                "宝贝",
                "❤",
                "💕",
            ],
            "thumbsUp": [
                "好",
                "棒",
                "赞",
                "厉害",
                "优秀",
                "不错",
                "真好",
                "太好了",
                "great",
                "excellent",
            ],
            "clap": ["恭喜", "祝贺", "太棒了", "鼓掌", "精彩", "加油"],
            "ok": [
                "ok",
                "好的",
                "没问题",
                "可以",
                "行",
                "明白",
                "了解",
                "知道了",
                "收到",
            ],
            "peace": ["和平", "友好", "冷静", "友谊", "平静", "peace", "calm"],
            "wave": ["你好", "嗨", "再见", "拜拜", "hello", "hi", "bye", "欢迎"],
            "facepalm": [
                "无语",
                "晕",
                "无奈",
                "崩溃",
                "受不了",
                "天啊",
                "醉了",
                "尴尬",
            ],
            "middleFinger": ["傻", "笨", "蠢", "烦", "滚", "讨厌", "恶心"],
            "thinking": ["想", "思考", "考虑", "琢磨", "分析", "嗯", "不确定", "或许"],
            "rock": ["摇滚", "酷", "炫", "燃", "激情", "rock", "cool", "awesome"],
        }

        # 检查关键词
        for gesture, keywords in gesture_keywords.items():
            if any(keyword in text for keyword in keywords):
                return gesture

        # 默认手势
        return "ok" if len(text) > 20 else "wave"


# 全局实例
chat_logic = ChatLogic()


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        history = data.get("history", [])

        # 获取回复
        response = chat_logic.get_response(history)

        # 选择手势
        gesture = GestureSelector.select_gesture(response["text"])

        return jsonify({"text": response["text"], "gesture": gesture})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"text": "抱歉，出现了一些问题。", "gesture": "facepalm"})


# Vercel handler
handler = app
