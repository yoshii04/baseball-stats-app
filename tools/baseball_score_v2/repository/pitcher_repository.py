import logging
import pandas as pd
from model.pitcher_record import PitcherRecord
from utils.excel_util import safe_str, safe_int, safe_game_number


class PitcherRepository:
    def __init__(self):
        self.logger = logging.getLogger("app.repository")

    @staticmethod
    def _flatten_columns(header_rows: list[list]) -> list[str]:
        """
        2行分のヘッダーを列ごとに結合して平坦な列名リストを返す。
        BattingRepository._flatten_columns と同一ロジック。
        """
        import math
        row1, row2 = header_rows[0], header_rows[1]
        raw = []
        for c1, c2 in zip(row1, row2):
            parts = []
            for c in (c1, c2):
                s = str(c).strip() if c is not None else ""
                if s and s.lower() != "nan" and "Unnamed" not in s and not (
                    isinstance(c, float) and math.isnan(c)
                ):
                    parts.append(s)
            raw.append("".join(parts))

        seen: dict[str, int] = {}
        result = []
        for name in raw:
            if name not in seen:
                seen[name] = 1
                result.append(name)
            else:
                seen[name] += 1
                result.append(f"{name}_{seen[name]}")
        return result

    def load_records(self, excel_file: str, sheet_name: str) -> list[PitcherRecord]:
        records = []
        self.logger.info("Excelファイル読み込み開始（投手）: %s (%s)", excel_file, sheet_name)

        df_header = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            header=None,
            nrows=2,
            usecols="B:AZ"
        )
        combined_headers = self._flatten_columns(df_header.values.tolist())

        df = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            skiprows=2,
            header=None,
            usecols="B:AZ"
        )
        df.columns = combined_headers
        self.logger.info("読み込み列（投手）: %s", df.columns.tolist())

        # 試合番号列を探す（「試合」を含み「対戦」を含まない列）
        game_number_col = None
        for col in df.columns.tolist():
            if "試合" in col and "対戦" not in col:
                game_number_col = col
                break
        if game_number_col is None:
            self.logger.warning("試合番号列が見つかりませんでした。game_number=1 で処理します。")

        for _, row in df.iterrows():
            date = safe_str(row.get("日"))
            opponent = safe_str(row.get("対戦相手"))
            pitcher_name = safe_str(row.get("選手名"))

            if not date or not opponent or not pitcher_name:
                continue

            game_number = safe_game_number(row.get(game_number_col)) if game_number_col else 1
            record = PitcherRecord(
                date=date,
                opponent=opponent,
                pitcher_name=pitcher_name,
                game_number=game_number,
                pitch_count=safe_int(row.get("投球")),
                homerun_allowed=safe_int(row.get("塁打本塁打")),
                walks_allowed=safe_int(row.get("四死球")),
                strikeouts=safe_int(row.get("三振")),
                hits_allowed=safe_int(row.get("安打")),
                runs_allowed=safe_int(row.get("得点")),
                right_9=safe_int(row.get("右")),
                right_center=safe_int(row.get("右中")),
                center=safe_int(row.get("中")),
                left_center=safe_int(row.get("左中")),
                left_7=safe_int(row.get("左")),
            )
            records.append(record)

        self.logger.info("Excelファイル読み込み完了（投手）: %d 件", len(records))
        return records
