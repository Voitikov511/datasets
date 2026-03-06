import io
from datetime import datetime
from pathlib import Path
import tkinter as tk

import dataset
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image, ImageTk

# Данные из задания 1
df = dataset.df

# Числовые колонки для нашего датасета
NUMERIC_COLUMNS = [
    "Rating",
    "Refresh Rate (Hz)",
    "Price (USD)",
    "Rating.1"
]

# Студенческий ID
STUDENT_ID = "70156739"


def recursive_digit_sum(value: str) -> int:
    """Вычисляет рекурсивную сумму цифр до одной цифры."""
    digits_sum = sum(int(ch) for ch in value if ch.isdigit())
    while digits_sum >= 10:
        digits_sum = sum(int(ch) for ch in str(digits_sum))
    return digits_sum


def get_marker_by_student_id(student_id: str) -> str:
    """
    Возвращает маркер matplotlib по рекурсивной сумме цифр студенческого ID.
    Соответствие 1..9 взято по условию задания.
    """
    marker_map = {
        1: "^",   # треугольник вверх
        2: ">",   # треугольник вправо
        3: "o",   # круг
        4: "s",   # квадрат
        5: "P",   # заполненный плюс
        6: "h",   # шестиугольник
        7: "*",   # звезда
        8: "H",   # другой шестиугольник
        9: "<"    # треугольник влево
    }
    result = recursive_digit_sum(student_id)
    return marker_map[result]


MARKER_STYLE = get_marker_by_student_id(STUDENT_ID)


class DataScatterApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("data_scatter")
        self.master.geometry("980x700")
        self.master.minsize(900, 650)

        self.x_column = NUMERIC_COLUMNS[0]
        self.y_column = NUMERIC_COLUMNS[1]

        self.current_figure = None
        self.current_photo = None

        self.build_interface()
        self.update_plot()

    def build_interface(self) -> None:
        """Создает интерфейс приложения."""
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill="both", expand=True)

        self.left_frame = tk.Frame(self.main_frame, padx=10, pady=10)
        self.left_frame.pack(side="left", fill="y")

        self.center_frame = tk.Frame(self.main_frame, padx=10, pady=10)
        self.center_frame.pack(side="left", fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.master, padx=10, pady=10)
        self.bottom_frame.pack(side="bottom", fill="x")

        # Кнопки выбора оси Y слева
        self.left_title = tk.Label(self.left_frame, text="Ось Y")
        self.left_title.pack(pady=(0, 10))

        for column in NUMERIC_COLUMNS:
            button = tk.Button(
                self.left_frame,
                text=column,
                width=20,
                command=lambda col=column: self.set_y_column(col)
            )
            button.pack(pady=4)

        self.save_button = tk.Button(
            self.left_frame,
            text="Сохранить",
            width=20,
            command=self.save_plot
        )
        self.save_button.pack(side="bottom", pady=(20, 0))

        # Поле для графика
        self.canvas_label = tk.Label(self.center_frame, bd=1, relief="sunken")
        self.canvas_label.pack(fill="both", expand=True)

        # Кнопки выбора оси X снизу
        self.bottom_title = tk.Label(self.bottom_frame, text="Ось X")
        self.bottom_title.pack(anchor="w")

        self.bottom_buttons_frame = tk.Frame(self.bottom_frame)
        self.bottom_buttons_frame.pack(fill="x", pady=(5, 0))

        for column in NUMERIC_COLUMNS:
            button = tk.Button(
                self.bottom_buttons_frame,
                text=column,
                width=20,
                command=lambda col=column: self.set_x_column(col)
            )
            button.pack(side="left", padx=4)

    def set_x_column(self, column: str) -> None:
        """Устанавливает колонку для оси X."""
        self.x_column = column
        self.update_plot()

    def set_y_column(self, column: str) -> None:
        """Устанавливает колонку для оси Y."""
        self.y_column = column
        self.update_plot()

    def create_plot_figure(self):
        """Создает figure matplotlib с точечной диаграммой."""
        fig, ax = plt.subplots(figsize=(7, 5), dpi=100)

        ax.scatter(
            df[self.x_column],
            df[self.y_column],
            marker=MARKER_STYLE
        )

        ax.set_xlabel(self.x_column)
        ax.set_ylabel(self.y_column)
        ax.set_title(f"{self.y_column} / {self.x_column}")
        ax.grid(False)

        fig.tight_layout()
        return fig

    def render_figure_to_photoimage(self, fig):
        """Преобразует figure matplotlib в PhotoImage для tkinter."""
        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)

        image = Image.open(buf)
        photo = ImageTk.PhotoImage(image)
        return photo

    def update_plot(self) -> None:
        """Перестраивает график и обновляет изображение в интерфейсе."""
        if self.current_figure is not None:
            plt.close(self.current_figure)

        self.current_figure = self.create_plot_figure()
        self.current_photo = self.render_figure_to_photoimage(self.current_figure)

        self.canvas_label.configure(image=self.current_photo)

    def save_plot(self) -> None:
        """Сохраняет текущий график в PNG-файл с именем по шаблону graphHH_MM_SS.png."""
        if self.current_figure is None:
            return

        filename = datetime.now().strftime("graph%H_%M_%S.png")
        save_path = Path(__file__).resolve().parent / filename
        self.current_figure.savefig(save_path)


def main() -> None:
    root = tk.Tk()
    app = DataScatterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
