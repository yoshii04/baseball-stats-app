"""
野球分析Excel出力

使い方:
    python analytics.py --year 2026

出力:
    analytics_2026.xlsx（選手別打撃成績・打球方向・成績推移の3シート）
"""
import argparse
import logging
import os

from app_util import setup_logging
from controller.analytics_controller import AnalyticsController


def main():
    setup_logging()
    logger = logging.getLogger("app.main")

    parser = argparse.ArgumentParser(description="野球分析Excelを生成します")
    parser.add_argument(
        "--year", type=int, required=True,
        help="対象年度（例: 2026）",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="出力ファイルパス（省略時: analytics_{year}.xlsx）",
    )
    args = parser.parse_args()

    output_path = args.output or os.path.join(
        os.path.dirname(__file__), f"analytics_{args.year}.xlsx"
    )

    logger.info("analytics 開始: year=%d", args.year)

    controller = AnalyticsController()
    try:
        controller.generate_analytics(args.year, output_path)
        print(f"✓ 出力完了: {output_path}")
    except Exception as e:
        logger.error("エラーが発生しました: %s", e)
        raise
    finally:
        controller.close()

    logger.info("analytics 完了")


if __name__ == "__main__":
    main()
