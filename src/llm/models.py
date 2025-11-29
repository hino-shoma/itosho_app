from pydantic import BaseModel, Field
from datetime import date

# 1. ツールとモデルの定義
class ExamInfo(BaseModel):
    """Schema for exam information."""
    exam_name: str = Field(..., description="資格名")
    exam_date: date = Field(..., description="資格試験日")
