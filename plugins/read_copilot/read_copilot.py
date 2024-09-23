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
    name="ReadCopilot",
    desire_priority=999,
    hidden=True,
    desc="阅读助理",
    version="0.1",
    author="hongfei",
)
class ReadCopilot(Plugin):

    flomo_api = ""

    def __init__(self):
        super().__init__()
        try:
            self.config = super().load_config()
            self.flomo_api = self.config.get("flomo_api", "")
            logger.info("[ReadCopilot] inited")
            # self.handlers[Event.ON_RECEIVE_MESSAGE] = self.on_receive_message
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[ReadCopilot]初始化异常：{e}")
            raise "[ReadCopilot] init failed, ignore "

    def on_receive_message(self, e_context: EventContext):
        """
        不做任何处理，也不让默认逻辑做任何处理，仅做拦截
        """

        # if e_context["context"].type not in [ContextType.TEXT, ContextType.SHARING]:
        #     return

        msg: ChatMessage = e_context["context"]["msg"]
        content = e_context["context"].content

        logger.debug("[ReadCopilot] on_receive_message. content: %s" % content)

        e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [ContextType.TEXT, ContextType.SHARING]:
            logger.info(f"[ReadCopilot] on_handle_context，收到消息，但未处理. content: {e_context['context'].content}")
            return

        reply_content = f"[ReadCopilot]\n收到，but未处理"

        try:
            # 如果是链接或分享链接，则保存至flomo
            noteValue = e_context["context"].content
            response = self.save_to_flomo(noteValue)
            if response.get("code") == 0:
                reply_content = f"[ReadCopilot]\n{response.get('message')}"
            else:
                reply_content = f"[ReadCopilot]\n保存失败，异常: {response.get('message')}"
            logger.info(f"[ReadCopilot] save_to_flomo. response: {response}")

        except Exception as e:
            logger.error(f"[ReadCopilot] on_handle_context 异常: {e}")
            reply_content = f"[ReadCopilot]\n保存失败，异常: {e}"

        reply = Reply()
        reply.type = ReplyType.TEXT
        msg: ChatMessage = e_context["context"]["msg"]

        reply.content = reply_content
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "阅读助理，支持保存链接、分享的链接等"
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
