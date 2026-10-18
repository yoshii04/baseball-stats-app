import logging
import os
from repository.batting_repository import BattingRepository
from service.batting_service import BattingService
from view.batting_view import BattingView
from utils.number_util import to_marunum


class BattingController:
    def __init__(self):
        self.logger = logging.getLogger("app.controller")
        self.repository = BattingRepository()
        self.service = BattingService()
        self.view = BattingView()

    def load_records(self, excel_file: str, sheet_name: str):
        """Load batting records from Excel file"""
        self.logger.info("データ読み込み開始")
        records = self.repository.load_records(excel_file, sheet_name)
        self.logger.info("データ読み込み完了: %d 件", len(records))
        return records

    def show_summary(self, records):
        """Display summary of loaded records"""
        summary = self.service.summarize_hits(records)
        self.view.display_summary(summary)

    @staticmethod
    def _format_pitcher_entry(name: str, innings: int, outs: int) -> str:
        """投手1人分のエントリを '名前(X回)' 形式で返す"""
        if outs == 0:
            innings_str = f"{innings}回"
        elif outs == 1:
            innings_str = f"{innings}回1/3"
        else:
            innings_str = f"{innings}回2/3"
        return f"{name}({innings_str})"

    def export_game_inputs(
        self,
        records,
        output_dir: str,
        pitcher_map: dict | None = None,
    ) -> list[str]:
        """
        打撃成績レコードから試合入力ファイルを生成する。

        summary の (日付, 対戦相手, 試合番号) ごとに 1 ファイルを出力する。
        ファイル名: {date}_{opponent}_{game_number}.txt
        pitcher_map が指定された場合は pitcher 欄を自動入力する。
        既存ファイルの pitcher 欄が空の場合も更新する。

        pitcher_map の形式:
            { (date, opponent, game_number): [(pitcher_name, innings_pitched, outs), ...] }

        Returns:
            生成・更新したファイルのパスリスト
        """
        os.makedirs(output_dir, exist_ok=True)
        summary = self.service.summarize_hits(records)
        generated = []

        # 打撃レコード全体から試合一覧を収集（長打がない試合も含む）
        all_games: set[tuple] = set()
        for r in records:
            all_games.add((r.date, r.opponent, r.game_number))
        if pitcher_map:
            for key in pitcher_map:
                all_games.add(key)

        def fmt_players(players: dict) -> list[str]:
            return sorted(
                f"{p}{to_marunum(str(c))}" if c > 1 else p
                for p, c in players.items()
            )

        for date, opponent, game_number in sorted(all_games):
            by_hit_type = summary.get(date, {}).get(opponent, {}).get(game_number, {})
            doubles = fmt_players(by_hit_type.get("2塁打", {}))
            triples = fmt_players(by_hit_type.get("3塁打", {}))
            homeruns = fmt_players(by_hit_type.get("本塁打", {}))

            # pitcher 文字列を構築
            pitcher_str = ""
            if pitcher_map:
                entries = pitcher_map.get((date, opponent, game_number), [])
                pitcher_str = "、".join(
                    self._format_pitcher_entry(n, ip, outs)
                    for n, ip, outs in entries
                )

            safe_name = opponent.replace("/", "_").replace("\\", "_")
            filename = f"{date}_{safe_name}_{game_number}.txt"
            filepath = os.path.join(output_dir, filename)

            if os.path.exists(filepath):
                # 既存ファイルの pitcher 欄が空なら更新
                if pitcher_str:
                    self._update_pitcher_field(filepath, pitcher_str)
                else:
                    self.logger.info("試合入力ファイルスキップ（既存）: %s", filepath)
                continue

            lines = [
                f"date: {date}",
                f"opponent: {opponent}",
                f"game_number: {game_number}",
                "venue: ",
                f"pitcher: {pitcher_str}",
                f"doubles: {'、'.join(doubles)}",
                f"triples: {'、'.join(triples)}",
                f"homeruns: {'、'.join(homeruns)}",
            ]
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

            self.logger.info("試合入力ファイル生成: %s", filepath)
            generated.append(filepath)

        self.logger.info("試合入力ファイル生成完了: %d 件", len(generated))
        return generated

    def _update_pitcher_field(self, filepath: str, pitcher_str: str) -> None:
        """既存ファイルの pitcher 欄が空の場合のみ更新する"""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # "pitcher: " の後が空（改行のみ）の行だけ対象
        import re
        if re.search(r"^pitcher:\s*$", content, re.MULTILINE):
            updated = re.sub(
                r"^(pitcher:)\s*$",
                f"\\1 {pitcher_str}",
                content,
                flags=re.MULTILINE,
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated)
            self.logger.info("pitcher 欄を更新: %s", filepath)
        else:
            self.logger.info("pitcher 欄スキップ（既入力）: %s", filepath)

    def import_to_db(self, records):
        """Import records to database"""
        self.logger.info("DB登録開始")
        self.service.import_to_db(records)
        self.logger.info("DB登録完了")

    def show_batting_stats_list(self) -> None:
        """DBから打撃成績リストを取得して表示する"""
        self.logger.info("打撃成績リスト表示開始")
        stats = self.service.get_batting_stats_list()
        self.view.display_batting_stats(stats)
        self.logger.info("打撃成績リスト表示完了")
