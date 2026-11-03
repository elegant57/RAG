md5_path = '/home/xuxin/Agent_learn/P4_RAG_program/md5.txt'

# Chroma Config
collection_name = 'RAG'
persist_directory = '/home/xuxin/Agent_learn/P4_RAG_program/chroma_db'

# Spliter Config
chunk_size = 1000
chunk_overlap = 100
separators = ["\n\n", "\n", ".", "!", "?", "。", "？", "！", " ", ""]
max_split_char_number = chunk_size * 1.5    # 文本分割的阈值

# retriever Config
similarity_threshold = 2        # 检索返回匹配的文档数量

embedding_model_name = "text-embedding-v4"
chat_model_name = "qwen3.7-max"

session_config = {
    'configurable': {
        'session_id': "user001"
    }
}