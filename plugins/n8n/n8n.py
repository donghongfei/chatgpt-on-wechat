# encoding:utf-8
import requests

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from config import conf
from plugins import *


@plugins.register(
    name="N8N",
    desire_priority=999,
    hidden=True,
    desc="接入N8N平台，可以使用如工作流等2",
    version="0.1",
    author="donghongfei",
)
class N8N(Plugin):
    """N8N插件：用于接入N8N平台，实现工作流等功能"""

    def __init__(self):
        """初始化N8N插件，加载配置并设置事件处理器"""
        super().__init__()
        try:
            self.config = super().load_config()
            # 从配置中获取 n8n webhook URL
            self.webhook_url = self.config.get("webhook_url", "")
            if not self.webhook_url:
                raise ValueError("webhook_url not configured")

            logger.info("[N8N] inited")
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.error("[N8N]初始化异常：%s", e)
            raise RuntimeError("[N8N] init failed, ignore") from e

    def on_receive_message(self, e_context: EventContext):
        """
        不做任何处理，也不让默认逻辑做任何处理，仅做拦截
        """

        # if e_context["context"].type not in [ContextType.TEXT, ContextType.SHARING]:
        #     return

        msg: ChatMessage = e_context["context"]["msg"]
        content = e_context["context"].content

        logger.debug("[N8N] on_receive_message. content: %s" % content)

        e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

    def on_handle_context(self, e_context: EventContext):
        """处理消息事件并转发到 n8n webhook

        Args:
            e_context (EventContext): 消息事件上下文
        """
        if e_context["context"].type not in [ContextType.TEXT, ContextType.SHARING]:
            logger.info(f"[N8N] on_handle_context，收到消息，但未处理. content: {e_context['context']}")
            return

        reply_content = "[N8N]\n消息已转发"

        try:
            # 获取消息内容
            content = e_context["context"].content
            msg: ChatMessage = e_context["context"]["msg"]

            # 构建发送到 n8n 的数据
            payload = {"content": content, "from_user": msg.from_user_id}

            # 发送到 n8n webhook
            response = requests.post(self.webhook_url, json=payload, headers={"Content-Type": "application/json"})

            if response.status_code == 200:
                response_json = response.json()
                code = response_json.get("code")
                message = response_json.get("message")

                if code == 0:
                    reply_content = f"[N8N]\n{message}"
                    logger.info(f"[N8N] Message forwarded to n8n successfully\n{response_json}")
                else:
                    reply_content = f"[N8N]\n转发失败: {message}"
                    logger.error(f"[N8N] Failed to forward message: {message}")

            else:
                reply_content = f"[N8N]\n转发失败: HTTP {response.status_code}"
                logger.error(f"[N8N] Failed to forward message: {response.text}")

        except Exception as e:
            logger.error(f"[N8N] on_handle_context 异常: {e}")
            reply_content = f"[N8N]\n转发失败，异常: {e}"

        reply = Reply()
        reply.type = ReplyType.TEXT
        reply.content = reply_content
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS

    def get_help_text(self, **kwargs):
        help_text = "用于接入N8N平台，实现工作流等功能\n"
        return help_text

    def save_to_flomo(self, noteValue):
        """通过post请求保存至flomo
        POST https://flomoapp.com/iwh/test/test/
        Content-type: application/json
        {
            "content": "Hello, #flomo https://flomoapp.com"
        }

        Args:
            noteValue (_type_): _description_
        """
        if self.flomo_api == "":
            return {"code": 1, "message": "flomo_api未配置"}

        headers = {"Content-type": "application/json"}
        data = {"content": f"#收件箱\n{noteValue}"}
        response = requests.post(self.flomo_api, headers=headers, data=json.dumps(data))
        return response.json()
