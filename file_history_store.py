import os, json
from typing import Sequence
from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory
# message_to dict：单个消息对象（BaseMessage实例） -> 字典
# messages_from_dict：[字典、字典……] -> [消息、消息……]
# AIMessage、HumanMessage、SystemMessage 都是 BaseMessage 的子类

class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id, session_path):
        self.session_id = session_id
        self.session_path = session_path
        # 完整的文件路径
        self.file_path = os.path.join(session_path, session_id)     # 检查父文件夹是否存在

        # 确保文件夹是存在的
        os.makedirs(os.path.dirname(self.file_path), exist_ok = True)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        # Sequence序列，类似list、tuple
        all_messages = list(self.messages)
        all_messages.extend(messages)

        # 将数据同步写入到本地文件当中
        # 类对象写入文件 -> 一堆二进制
        # 为了方便，可以将 BaseMessage 消息转化为字典（借助json模块以json字符串写入文件）
        # 官方 message_to_dict：单个消息对象（BaseMessage实例） -> 字典
        # new_messages = []
        # for message in all_messages:
        #     d = message_to_dict(message)
        #     new_messages.append(d)
        # 等价于
        new_messages = [message_to_dict(message) for message in all_messages]
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(new_messages, f)

    @property           # @property 装饰器将 messages 方法变成成员属性用
    def messages(self) -> list[BaseMessage]:
        # 当前文件内：list[字典]
        try:
            with open(self.file_path, "r", encoding='utf-8') as f:
                messages_data = json.load(f)    # 返回值是：list[字典]
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def clear(self) -> None:
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump([], f)

def get_history(session_id):
    return FileChatMessageHistory(session_id, '/home/xuxin/Agent_learn/P4_RAG_program/chat_history')
