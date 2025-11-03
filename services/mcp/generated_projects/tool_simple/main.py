import argparse
import logging
from datetime import datetime
from pathlib import Path

class DataConverter:
    def __init__(self):
        self.data = None

    @staticmethod
    def setup_database(db_path: str, table_name: str):
        """データベースのセットアップ"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.close()

    def convert_csv_to_json(self, csv_file: Path):
        """CSVデータをJSON形式に変換する"""
        self.data = []
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                self.data.append(row)

    def print_data(self):
        """データの表示"""
        if not self.data:
            return

        print(f"CSVファイル: {csv_file}")
        print(f"Data: {self.data}")

    @staticmethod
    def setup_cli_args():
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command", help="sub-command")
        
        convert_command = subparsers.add_parser("convert", parents=[argparse.ArgumentParser()])
        convert_command.set_defaults(func=DataConverter.convert_csv_to_json)

        return parser, DataConverter


def main():
    """メイン関数"""
    # TODO: 実装を追加
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()
    cli_args, converter = args.setup_cli_args()
    
    data_converter = DataConverter()
    data_converter.data = convert_command.parse_args().data
    data_converter.setup_database(cli_args.db_path, "csv")
    data_converter.convert_csv_to_json(data_converter.data)