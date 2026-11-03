from langchain_community.chat_models.tongyi import ChatTongyi
from vector_store import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from langchain_core.runnables import RunnableWithMessageHistory, RunnableLambda
from file_history_store import get_history

def print_prompt(prompt):
    print('='*90)
    print(prompt.to_string())
    print('='*90)

    return prompt

class RagService(object):
    def __init__(self, ):
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name)
        )

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ('system', "以我提供的资料为主，简介和专业的回答用户问题。参考资料：{context}"),
                ('system', '并且我提供用户的对话历史记录，如下：'),
                MessagesPlaceholder('history'),
                ('user', "请回答用户提问：{input}")
            ]
        )

        self.chat_model = ChatTongyi(model=config.chat_model_name, streaming=True)

        self.chain = self.__get_chain()

    def __get_chain(self):
        """获取最终执行链"""
        retriever = self.vector_service.get_retriever()
        def format_func(docs: list[Document]):
            if not docs:
                return "无相关参考资料"
            prompt = ''
            for doc in docs:
                prompt += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"
            return prompt
        
        def format_for_retriever(value: dict) -> str:
            return value['input']

        def format_for_prompt_template(value):
            # {input:{input:..., history"...}, context:...} -> {input, context, history}
            new_value = {}
            new_value['input'] = value['input']['input']
            new_value['context'] = value['context']
            new_value['history'] = value['input']['history']
            return new_value
            

        chain = (
            {
                'input': RunnablePassthrough(),
                'context': RunnableLambda(format_for_retriever) | retriever | format_func
            } | RunnableLambda(format_for_prompt_template) | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )

        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key='input',
            history_messages_key='history'
        )

        return conversation_chain

# if __name__ == '__main__':
#     configs = {
#         'configurable': {
#             'session_id': "user001"
#         }
#     }
#     res = RagService().chain.invoke({'input': '怎么有效防止异味产生'}, config = configs)
#     print(res)