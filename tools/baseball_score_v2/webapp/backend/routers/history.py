"""実行履歴エンドポイント"""
import json
import os
import sys
from typing import Optional

from fastapi import APIRouter, Depends

from auth import verify_token

# run_logger は baseball_score_v2 ルート配下にある
_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from utils.run_logger import read_logs

router = APIRouter(dependencies=[Depends(verify_token)])


@router.get("")
def get_history(
    date: Optional[str] = None,
    step: Optional[str] = None,
    last: Optional[int] = None,
):
    """
    実行履歴一覧を返す。

    Query params:
        date: "YYYY-MM-DD" で絞り込み
        step: ステップ名（validate / generate / import_db / analytics）で絞り込み
        last: 最新 N 件のみ返す（デフォルト: 全件）
    """
    records = read_logs(date=date, step=step, last=last)
    return {"records": records, "total": len(records)}
