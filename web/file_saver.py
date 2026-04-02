"""分析结果落盘。"""
import os
from datetime import datetime
from typing import Any, Dict, Optional

from web.config import Config


class FileSaver:
    """文件保存类"""

    @staticmethod
    def save_analysis(content: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
        """保存分析结果到文件"""
        try:
            os.makedirs(Config.SAVE_PATH, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if original_filename and original_filename.endswith(".pdf"):
                base_name = os.path.splitext(original_filename)[0]
                safe_filename = f"{base_name}_analysis_{timestamp}.md"
            else:
                safe_filename = f"analysis_{timestamp}.md"

            safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._- ")

            file_path = os.path.join(Config.SAVE_PATH, safe_filename)

            metadata = f"""---
title: 论文分析报告
generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
original_file: {original_filename if original_filename else '未知'}
---

"""
            full_content = metadata + content

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)

            relative_path = os.path.join(Config.SAVE_DIR, safe_filename)

            return {
                "success": True,
                "file_path": file_path,
                "relative_path": relative_path,
                "filename": safe_filename,
                "size": len(full_content),
            }
        except PermissionError as e:
            print(f"❌ 文件保存失败（权限不足）: {e}")
            return {"success": False, "error": f"权限不足: {str(e)}"}
        except OSError as e:
            print(f"❌ 文件保存失败（IO错误）: {e}")
            return {"success": False, "error": f"IO错误: {str(e)}"}
        except Exception as e:
            print(f"❌ 文件保存失败（未知错误）: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_save_directory() -> str:
        return Config.SAVE_PATH
