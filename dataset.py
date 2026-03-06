import io
from pathlib import Path
import pandas as pd

# Файл dataset.csv должен находиться в той же папке, что и dataset.py
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.csv"
REPORT_PATH = BASE_DIR / "report.txt"

# Глобальный DataFrame
df = pd.read_csv(DATASET_PATH)

# Счётные (числовые) колонки
COUNTABLE_COLUMNS = [
    "Rating",
    "Refresh Rate (Hz)",
    "Price (USD)",
    "Rating.1"
]

# Категориальные колонки
CATEGORICAL_COLUMNS = [
    "Brand",
    "Model",
    "Selling Platform"
]


def get_info_string(dataframe):
    buffer = io.StringIO()
    dataframe.info(buf=buffer)
    return buffer.getvalue()


def build_report(dataframe):
    report_lines = []

    # Размер датасета
    report_lines.append(str(dataframe.shape))

    # Информация о колонках
    report_lines.append(get_info_string(dataframe))

    # Количество пропусков
    report_lines.append(dataframe.isna().sum().to_string())

    # Статистика для числовых колонок
    report_lines.append("Колонка>\tсреднее\tмедиана\tотклонение")
    for col in COUNTABLE_COLUMNS:
        mean_val = dataframe[col].mean()
        median_val = dataframe[col].median()
        std_val = dataframe[col].std()

        line = f"{col}>\t{mean_val:.2f};\t{median_val:.2f};\t{std_val:.2f}"
        report_lines.append(line)

    # Частоты категориальных значений
    for col in CATEGORICAL_COLUMNS:
        report_lines.append(col)
        report_lines.append(dataframe[col].value_counts(dropna=False).to_string())

    return "\n".join(report_lines)


def main():
    report = build_report(df)

    print(report)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)


if __name__ == "__main__":
    main()
