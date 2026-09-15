"""Xuất kết quả khảo sát ra Excel (2 sheet: danh sách lượt khảo sát + chi tiết câu trả lời)."""
from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

_HEADER_FONT = Font(bold=True)
_HEADER_FILL = PatternFill("solid", fgColor="DDE7F3")


def _style_header(ws) -> None:
    for cell in ws[1]:
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL


def _format_answer(answer) -> str:
    if answer.option_id and answer.option:
        return answer.option.option_text
    if answer.answer_text is not None:
        if answer.answer_text == "yes":
            return "Có"
        if answer.answer_text == "no":
            return "Không"
        return answer.answer_text
    if answer.answer_number is not None:
        return str(answer.answer_number)
    return ""


def build_workbook(survey, responses: list) -> io.BytesIO:
    wb = Workbook()

    ws1 = wb.active
    ws1.title = "Danh sách lượt khảo sát"
    headers1 = [
        "STT", "Ngày khảo sát", "Chi nhánh", "Dịch vụ", "Quầy", "Cán bộ",
        "Người trả lời", "Số điện thoại", "Email", "Địa chỉ",
    ]
    ws1.append(headers1)
    for i, r in enumerate(responses, start=1):
        ws1.append(
            [
                i,
                r.submitted_at.strftime("%d/%m/%Y %H:%M") if r.submitted_at else "",
                r.branch.name if r.branch else "",
                r.service_id or "",
                r.counter_id or "",
                r.employee.full_name if r.employee else "",
                r.respondent_name or "",
                r.respondent_phone or "",
                r.respondent_email or "",
                r.respondent_address or "",
            ]
        )
    _style_header(ws1)
    for col in range(1, len(headers1) + 1):
        ws1.column_dimensions[get_column_letter(col)].width = 20

    ws2 = wb.create_sheet("Chi tiết câu trả lời")
    headers2 = ["STT", "Ngày khảo sát", "Chi nhánh", "Cán bộ", "Khảo sát", "Câu hỏi", "Trả lời"]
    ws2.append(headers2)
    stt = 0
    for r in responses:
        for a in r.answers:
            stt += 1
            ws2.append(
                [
                    stt,
                    r.submitted_at.strftime("%d/%m/%Y %H:%M") if r.submitted_at else "",
                    r.branch.name if r.branch else "",
                    r.employee.full_name if r.employee else "",
                    survey.title,
                    a.question.question_text if a.question else "",
                    _format_answer(a),
                ]
            )
    _style_header(ws2)
    for col in range(1, len(headers2) + 1):
        ws2.column_dimensions[get_column_letter(col)].width = 32

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
