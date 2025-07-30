from typing import List, Dict
import logging
from langchain.schema import Document
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PDFPageChunkParser:

    def __init__(self,
                 embed_model_name: str = "intfloat/e5-large",
                 chunk_size_thresh: int = 5000):
        # 嵌入模型
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=embed_model_name,
            model_kwargs={"device": "cpu", "trust_remote_code": True},
            encode_kwargs={"normalize_embeddings": True},
        )
        # 语义切分器
        self.text_splitter = SemanticChunker(
            self.embedding_model,
            breakpoint_threshold_type="percentile"
        )
        self.chunk_size_thresh = chunk_size_thresh

    def parse_pdf_to_documents(self, pdf_path: str) -> List[Document]:
        # 加载 PDF 文档元素
        docs = self.load_pdf(pdf_path)
        log.info(f"[PDF] 加载元素数量: {len(docs)}")

        # 合并结构化段落
        merged = self.merge_structured_content(docs)
        log.info(f"[PDF] 合并后文档数: {len(merged)}")

        # 语义切片
        chunks = self.chunk_documents(merged)
        log.info(f"[PDF] 语义切片后 count: {len(chunks)}")
        return chunks

    def load_pdf(self, pdf_path: str) -> List[Document]:
        loader = UnstructuredPDFLoader(
            file_path=pdf_path,
            mode="elements",
            strategy="fast"  # 建议使用 hi_res 获取更多结构信息
        )
        return list(loader.lazy_load())

    from typing import List, Dict
    from langchain_core.documents import Document

    def merge_structured_content(self, docs: List[Document]) -> List[Document]:
        merged_data: List[Document] = []
        parent_dict: Dict[str, Document] = {}

        for doc in docs:
            meta = doc.metadata
            text = doc.page_content.strip()
            if not text:
                continue

            cat = meta.get('category')
            pid = meta.get('parent_id')
            eid = meta.get('element_id')

            if cat in ("Header", "Footer"):
                continue

            # 1. 顶级正文（没有 parent 的 NarrativeText）
            if cat == "NarrativeText" and not pid:
                meta['category_depth'] = 1
                meta['title'] = text[:30]  # 生成一个默认标题
                merged_data.append(doc)
                continue

            # 2. 标题节点
            if cat == "Title":
                meta['title'] = text  # 自身的标题
                if pid and pid in parent_dict:
                    parent = parent_dict[pid]
                    depth = parent.metadata.get('category_depth', 1) + 1
                    doc.page_content = parent.page_content + "\n" + text
                else:
                    depth = 1
                meta['category_depth'] = depth
                parent_dict[eid] = doc
                continue

            # 3. 子段落合并到父标题
            if cat in ("NarrativeText", "ListItem", "UncategorizedText") and pid:
                if pid in parent_dict:
                    parent = parent_dict[pid]
                    parent.page_content += "\n" + text
                    parent.metadata['category'] = "content"  # 合并后归为内容块
                else:
                    # 父标题不存在时，降级为顶级正文
                    meta['category_depth'] = 1
                    meta['title'] = text[:30]
                    merged_data.append(doc)
                continue

            # 4. 其它孤立块也作为顶级正文
            if cat in ("ListItem", "UncategorizedText") and not pid:
                meta['category_depth'] = 1
                meta['title'] = text[:30]
                merged_data.append(doc)

        # 最后将合并好的标题段落加入
        merged_data.extend(parent_dict.values())

        for doc in merged_data:
            if doc.metadata.get('category') != "Title":
                doc.metadata['category'] = "content"

        return merged_data

    def chunk_documents(self, docs: List[Document]) -> List[Document]:
        result = []
        for doc in docs:
            content = doc.page_content
            if len(content) > self.chunk_size_thresh:
                parts = self.text_splitter.split_documents([doc])
                result.extend(parts)
            else:
                result.append(doc)
        return result


# 示例用法
if __name__ == '__main__':
    parser = PDFPageChunkParser()
    pdf_file = "../papers/0a5e37e13244606ca95b585bd5bcb4e6.pdf"
    documents = parser.parse_pdf_to_documents(pdf_file)
    for d in documents:
        print(f"[Meta] {d.metadata}")
        print(f"[Text] {d.page_content[:200]}...")
        print("---")
