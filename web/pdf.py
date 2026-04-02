"""PDF 文本提取。"""
import io

import PyPDF2


class PDFProcessor:
    """PDF文件处理类"""

    @staticmethod
    def extract_text(file_stream: io.BytesIO) -> str:
        """从PDF文件中提取文本"""
        try:
            pdf_reader = PyPDF2.PdfReader(file_stream)
            text_content = []
            total_pages = len(pdf_reader.pages)

            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"[第{page_num + 1}/{total_pages}页]\n{text.strip()}")

            full_text = "\n\n".join(text_content)

            if not full_text.strip():
                raise Exception("无法从PDF中提取文本，可能是扫描件或加密文件")

            return full_text
        except PyPDF2.errors.PdfReadError as e:
            raise ValueError(f"PDF文件损坏或格式错误: {str(e)}") from e
        except Exception as e:
            raise Exception(f"PDF解析失败: {str(e)}") from e
