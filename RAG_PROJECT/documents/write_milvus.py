import multiprocessing
import os
from multiprocessing import Queue

from documents.pdf_parser import PDFPageChunkParser
from documents.milvus_db import MilvusVectorSave
from utils.log_utils import log


def pdf_parser_process(pdf_dir: str, output_queue: Queue, batch_size: int = 20):
    """进程1：解析PDF文件夹并分批放入队列"""
    log.info(f"扫描PDF目录: {pdf_dir}")
    pdf_files = [
        os.path.join(pdf_dir, f)
        for f in os.listdir(pdf_dir)
        if f.lower().endswith('.pdf')
    ]

    if not pdf_files:
        log.warning("未找到任何PDF文件")
        output_queue.put(None)
        return

    parser = PDFPageChunkParser()
    doc_batch = []
    for file_path in pdf_files:
        try:
            docs = parser.parse_pdf_to_documents(file_path)
            if docs:
                doc_batch.extend(docs)

            if len(doc_batch) >= batch_size:
                output_queue.put(doc_batch.copy())
                doc_batch.clear()
        except Exception as e:
            log.error(f"解析失败 {file_path}: {e}")
            log.exception(e)

    if doc_batch:
        output_queue.put(doc_batch)

    output_queue.put(None)
    log.info(f"解析完成，共处理 {len(pdf_files)} 个 PDF 文件")

failed_docs = []  # 存储未能成功存入的文档
def milvus_writer_process(input_queue: Queue):
    """进程2：读取队列并写入 Milvus"""
    log.info("Milvus 写入进程启动...")
    mv = MilvusVectorSave()
    mv.create_connection()
    total = 0
    failed = 0
    while True:
        try:
            docs = input_queue.get()
            if docs is None:
                break
            try:
                mv.add_documents(docs)
                total += len(docs)
                log.info(f"已写入 {total} 个文档")
            except Exception as e:
                log.error(f"写入异常，将文档加入失败列表: {e}")
                log.exception(e)
                failed_docs.extend(docs)  # 将失败的文档添加到失败列表中
                failed += len(docs)
        except Exception as e:
            log.error("读取队列异常")
            log.exception(e)
    log.info(f"Milvus 写入完成，文档总数: {total}，失败文档数: {failed}")


    # 处理未能成功存入的文档
def handle_failed_docs(failed_docs):
    if failed_docs:
        log.info(f"开始处理 {len(failed_docs)} 个失败的文档")
        try:
            mv.add_documents(failed_docs)
            log.info("失败的文档已重新处理完成")
        except Exception as e:
            log.error("重新处理失败文档时发生异常")
            log.exception(e)



if __name__ == '__main__':
    pdf_dir = "../papers"  # 你的 PDF 文件目录
    queue_maxsize = 20

    mv = MilvusVectorSave()
    mv.create_collection()

    docs_queue = Queue(maxsize=queue_maxsize)

    parser_proc = multiprocessing.Process(target=pdf_parser_process, args=(pdf_dir, docs_queue))
    writer_proc = multiprocessing.Process(target=milvus_writer_process, args=(docs_queue,))

    parser_proc.start()
    writer_proc.start()

    parser_proc.join()
    writer_proc.join()

    print("✅ 所有 PDF 文件已处理完毕")
