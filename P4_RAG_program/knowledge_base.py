"""
知识库
"""
import os
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime

def check_md5(md5_str: str) -> bool:
    """
    检查传入的md5字符串是否已经被处理过了，
    return False（md5未处理过）     True（已经处理过，已有记录）
    """

    if not os.path.exists(config.md5_path):
        # 进入 if 表示文件不存在，那肯定不存在该条md5
        # 用 w 的方式打开该文件，就创建了该文件
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()     # 处理字符串前后的空格和回车
            if line == md5_str:
                return True
        return False
    
def save_md5(md5_str: str) -> None:
    """
    将传入的md5字符串，记录到文件内保存
    """
    # 'a'表示追加
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')

def get_string_md5(input_str: str, encoding='utf-8'):
    """
    将传入的字符串转换为md5字符串
    """
    # 将字符串转换为bytes字节数据
    str_bytes = input_str.encode(encoding=encoding)

    # 创建md5对象
    md5_obj = hashlib.md5()     # 得到md5对象
    md5_obj.update(str_bytes)   # 更新内容(传入即将转换的字节数组)
    md5_hex = md5_obj.hexdigest()   # 得到md5的十六进制字符串

    return md5_hex

class KnowledgeBaseService():
    def __init__(self):
        # 如果文件夹不存在则创建，如果存在则跳过
        os.makedirs(config.persist_directory, exist_ok=True)

        self.chroma = Chroma(
            collection_name = config.collection_name,        # 数据库表名
            embedding_function = DashScopeEmbeddings(model='text-embedding-v4'),
            persist_directory = config.persist_directory  # 数据库本地存储文件夹
        )   # 向量存储的实例 Chroma 向量库对象

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size = config.chunk_size,         # 分割后文本的最大长度
            chunk_overlap = config.chunk_overlap,   # 连续文本段之间的字符重叠数量
            length_function = len,                  # 使用 Python 自带的 len 函数做长度统计的依据
            separators = config.separators            # 自然段落划分的符号
        )   # 文本分割器对象
    
    def uploader_by_str(self, data: str, filename):
        """将传入的字符串进行向量化，存入向量数据库中"""
        # 先得到传入字符的 md5 值
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            print("【跳过】内容已经存在知识库中")
            return "【跳过】内容已经存在知识库中"
        
        if len(data) > config.max_split_char_number:
            knowledge_chunks: list[str] = self.spliter.split_text(data)
        else:
            knowledge_chunks = [data]

        metadata = {
            "source": filename,
            # 2026-10-26 18:0:0
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "小欣",
            "content_md5": md5_hex
        }
        self.chroma.add_texts(      # 内容加载到向量库
            # iterable -> list \ tuple
            knowledge_chunks,
            metadatas=[metadata for _ in knowledge_chunks]      # list[dict]
        )
        save_md5(md5_hex)

        print("【成功】内容已经成功载入向量库")
        return "【成功】内容已经成功载入向量库"

    def delete_collection(self, collection_name: str):
        """删除指定集合，并清理对应的 MD5 记录"""

        client = self.chroma._client
        collection = client.get_collection(name=collection_name)

        # 获取该集合中所有数据对应的 MD5
        result = collection.get(include=["metadatas"])
        md5_set = {
            m["content_md5"]
            for m in result["metadatas"]
            if m and m.get("content_md5")
        }

        # 删除集合
        client.delete_collection(name=collection_name)

        # 检查这些 MD5 是否仍被其他集合使用
        remaining_md5 = set()

        for md5 in md5_set:
            for col in client.list_collections():
                other = client.get_collection(name=col.name)

                if other.get(
                    where={"content_md5": md5},
                    limit=1,
                    include=[]
                )["ids"]:
                    remaining_md5.add(md5)
                    break

        # 删除不再使用的 MD5 记录
        deleted_md5 = md5_set - remaining_md5

        if os.path.exists(config.md5_path) and deleted_md5:
            with open(config.md5_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            with open(config.md5_path, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.strip() not in deleted_md5:
                        f.write(line)

        print(f"【成功】已删除集合：{collection_name}")
        print(f"【成功】已清理 {len(deleted_md5)} 条 MD5 记录")

    def delete_elements(self, ids: list[str] = None, filename: str = None):
        """
        删除当前集合中的数据，并同步清理 MD5。

        ids: 根据向量 ID 删除
        filename: 根据上传文件名删除
        两个参数同时传入时，删除同时满足条件的数据。
        """

        if ids is None and filename is None:
            raise ValueError("必须传入 ids 或 filename")

        # 查询需要删除的数据
        kwargs = {"include": ["metadatas"]}

        if ids is not None:
            kwargs["ids"] = ids

        if filename is not None:
            kwargs["where"] = {"source": filename}

        result = self.chroma.get(**kwargs)

        delete_ids = result["ids"]

        if not delete_ids:
            print("【跳过】没有找到需要删除的数据")
            return

        # 记录待删除数据对应的 MD5
        md5_set = {
            m["content_md5"]
            for m in result["metadatas"]
            if m and m.get("content_md5")
        }

        # 删除向量数据
        self.chroma.delete(ids=delete_ids)

        # 检查对应的 MD5 是否还有其他数据在使用
        client = self.chroma._client
        deleted_md5 = set()

        for md5 in md5_set:
            still_exists = False

            for col in client.list_collections():
                collection = client.get_collection(name=col.name)

                remaining = collection.get(
                    where={"content_md5": md5},
                    limit=1,
                    include=[]
                )

                if remaining["ids"]:
                    still_exists = True
                    break

            if not still_exists:
                deleted_md5.add(md5)

        # 删除不再使用的 MD5
        if os.path.exists(config.md5_path) and deleted_md5:
            with open(config.md5_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            with open(config.md5_path, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.strip() not in deleted_md5:
                        f.write(line)

        print(f"【成功】已删除 {len(delete_ids)} 条向量数据")
        print(f"【成功】已清理 {len(deleted_md5)} 条 MD5 记录")

if __name__ == '__main__':
    service = KnowledgeBaseService()
    service.uploader_by_str("徐欣", 'testfile')
    # service.delete_elements(filename='testfile')