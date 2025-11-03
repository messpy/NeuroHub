import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="CSVファイルを読み込み、統計処理、グラフ作成を行います。")
    parser.add_argument("--input", help="csvファイルのパス", required=True)
    args = parser.parse_args()

    # CSVファイルを開く
    with open(args.input, 'r', encoding='utf-8') as file:
        csv_data = list(csv.reader(file, delimiter=','))
    
    # CSVデータを統計処理
    total_count = len(csv_data)  # カテゴリーの数
    category_count = {}
    for row in csv_data:
        if not row:  # 一括検索時に空行を飛ばす
            continue

        category, value = row
        if category not in category_count:
            category_count[category] = {value: 1}
        else:
            category_count[category][value] += 1
    
    # 配列から数値を抽出
    for _, values in category_count.items():
        categories = [category for category, _values in values.items() if len(_values) > 0]
    
    # フィルター処理
    filtered_categories = set(categories)
    total_values = {value: sum(values.values()) for value, values in category_count.items()}
    
    # グラフ作成
    fig, ax = plt.subplots()
    bar_width = 0.35
    indices = [i+1 for i in range(len(filtered_categories))]
    bars = ax.bar(indices, total_values.values(), bar_width, label='Total')

    labels = [f'{category} - {value}' for category, value in filtered_categories]
    ax.set_xticks(indices)
    ax.set_xlabel('Categories')
    ax.set_ylabel('Count')
    ax.set_title(f'Category Statistics (Filtered: {len(filtered_categories)} categories)')
    
    for bar, label in zip(bars, labels):
        height = total_values[label]
        text = f'{height:.2f} ({bar.get_height()}%)'
        ax.text(bar.get_x() + bar_width, height - 0.15, text, ha='center', va='bottom')
    
    # ヘルプメッセージ
    print("\nUsage: python main.py --input <csv_file_path>")
    print("Example usage:\n")
    print(f"python main.py --input ./data.csv")

if __name__ == "__main__":
    main()