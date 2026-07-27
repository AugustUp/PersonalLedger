"""Build an Excel FileResponse for exports (manual 8.5, 11.5)."""
import os
import tempfile
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse

from app.utils.excel import write_export

_XLSX_MIME = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def build_export_response(headers: dict, rows: list[dict], filename: str,
                          background: BackgroundTasks) -> FileResponse:
    fd, path = tempfile.mkstemp(suffix=".xlsx", prefix="export_")
    os.close(fd)
    write_export(headers, rows, path)
    background.add_task(os.unlink, path)
    return FileResponse(path, filename=filename, media_type=_XLSX_MIME)
