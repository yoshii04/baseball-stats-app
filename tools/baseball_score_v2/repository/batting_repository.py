import logging
import pandas as pd
from model.batting_record import BattingRecord
from utils.excel_util import safe_str, safe_int, safe_game_number

class BattingRepository:
    def __init__(self):
        self.logger = logging.getLogger("app.repository")
        
    @staticmethod
    def _flatten_columns(header_rows: list[list]) -> list[str]:
        """
        2行分のヘッダーを列ごとに結合して平坦な列名リストを返す。
        None・NaN・"Unnamed" は無視する。重複列名は _2, _3 と連番を付与する。
        例: [["試合", None], ["番号", "日"]] → ["試合番号", "日"]
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

        # 重複列名に連番サフィックスを付与（最初の出現はそのまま）
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

    def _find_game_number_col(self, columns: list[str]) -> str | None:
        """'試合' を含み '対戦' を含まない列名を試合番号列として返す。"""
        for col in columns:
            if "試合" in col and "対戦" not in col:
                return col
        self.logger.warning("試合番号列が見つかりませんでした。game_number=1 で処理します。")
        return None

    def load_records(self, excel_file: str, sheet_name: str):
        records = []
        self.logger.info("Excelファイル読み込み開始: %s (%s)", excel_file, sheet_name)
        # pandas は header=[0,1] と usecols の同時指定不可のため、
        # ヘッダー2行を別途読んで結合し、データ部分と合わせる
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

        game_number_col = self._find_game_number_col(df.columns.tolist())
        self.logger.info("読み込み列: %s", df.columns.tolist())

        # デバッグ: 試合回数列の先頭10行の実際の値を出力
        if game_number_col:
            sample = df[game_number_col].dropna().head(10).tolist()
            self.logger.info("'%s' 列のサンプル値: %s", game_number_col, sample)

        for _, row in df.iterrows():
            date = safe_str(row.get("日"))
            opponent = safe_str(row.get("対戦相手"))
            player = safe_str(row.get("選手名"))

            # 必須項目が欠けている行はスキップ（空行・集計行など）
            if not date or not opponent or not player:
                continue

            game_number = safe_game_number(row.get(game_number_col)) if game_number_col else 1

            at_bat_count = safe_int(row.get("打数"))
            hit_count = safe_int(row.get("安打"))
            double = safe_int(row.get("2塁打"))
            triple = safe_int(row.get("3塁打"))
            homerun = safe_int(row.get("塁打本塁打"))
            on_base_opportunity = safe_int(row.get("出塁機会"))
            on_base = safe_int(row.get("出塁"))

            # 以下の補正は at_bat_count が有効値（0以上）の場合のみ適用する
            # at_bat_count < 0 の場合は後続の try/except でスキップされる
            if at_bat_count >= 0:
                # 安打 > 打数 を補正（安打を打数で頭打ち）
                if hit_count > at_bat_count:
                    self.logger.warning(
                        "自動補正: date=%s, opponent=%s, player=%s — 安打 %d→%d（打数=%d）",
                        date, opponent, player, hit_count, at_bat_count, at_bat_count,
                    )
                    hit_count = at_bat_count

                # 長打計 > 安打 を補正（超過分を2塁打→3塁打→本塁打の順に削減）
                extra_bases = double + triple + homerun
                if extra_bases > hit_count:
                    excess = extra_bases - hit_count
                    cut = min(double, excess)
                    double -= cut
                    excess -= cut
                    cut = min(triple, excess)
                    triple -= cut
                    excess -= cut
                    homerun -= excess
                    self.logger.warning(
                        "自動補正: date=%s, opponent=%s, player=%s — 長打計を安打数(%d)に合わせて削減",
                        date, opponent, player, hit_count,
                    )

            # 出塁 > 出塁機会 を補正（出塁を出塁機会で頭打ち）
            if on_base_opportunity > 0 and on_base > on_base_opportunity:
                self.logger.warning(
                    "自動補正: date=%s, opponent=%s, player=%s — 出塁 %d→%d（出塁機会=%d）",
                    date, opponent, player, on_base, on_base_opportunity, on_base_opportunity,
                )
                on_base = on_base_opportunity

            try:
                record = BattingRecord(
                    date=date,
                    opponent=opponent,
                    player=player,
                    game_number=game_number,
                    double=double,
                    triple=triple,
                    homerun=homerun,
                    at_bat_count=at_bat_count,
                    hit_count=hit_count,
                    walk_count=safe_int(row.get("四死球")),
                    strike_out=safe_int(row.get("三振")),
                    stolen_base=safe_int(row.get("盗塁")),
                    on_base_opportunity=on_base_opportunity,
                    on_base=on_base,
                    right_9=safe_int(row.get("右")),
                    right_center=safe_int(row.get("右中")),
                    center=safe_int(row.get("中")),
                    left_center=safe_int(row.get("左中")),
                    left_7=safe_int(row.get("左")),
                )
            except ValueError as e:
                self.logger.warning(
                    "不正なレコードをスキップします: date=%s, opponent=%s, player=%s — %s",
                    date, opponent, player, e,
                )
                continue
            records.append(record)

        self.logger.info("Excelファイル読み込み完了: %d 件", len(records))
        return records
