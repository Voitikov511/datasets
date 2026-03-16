import io
from datetime import datetime
from pathlib import Path
import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image, ImageTk

import dataset

# Данные из задания 1
df = dataset.df

# Числовые колонки
NUMERIC_COLUMNS = [
    "Rating",
    "Refresh Rate (Hz)",
    "Price (USD)",
    "Rating.1",
]

# Индивидуальный маркер по ID 70156739:
# 7+0+1+5+6+7+3+9=38 -> 3+8=11 -> 1+1=2
# Маркер №2 = ">"
MARKER_STYLE = ">"


class DataScatterApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("data_scatter")
        self.master.geometry("1100x760")
        self.master.minsize(980, 700)
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.x_column = NUMERIC_COLUMNS[0]
        self.y_column = NUMERIC_COLUMNS[1]

        self.current_figure = None
        self.current_tk_image = None
        self.canvas_image_id = None

        self.build_interface()
        self.replace_plot()

    def build_interface(self) -> None:
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill="both", expand=True)

        self.left_frame = tk.Frame(self.main_frame, padx=10, pady=10)
        self.left_frame.pack(side="left", fill="y")

        self.center_frame = tk.Frame(self.main_frame, padx=10, pady=10)
        self.center_frame.pack(side="left", fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.master, padx=10, pady=10)
        self.bottom_frame.pack(side="bottom", fill="x")

        tk.Label(self.left_frame, text="Ось Y").pack(pady=(0, 10))

        for column in NUMERIC_COLUMNS:
            tk.Button(
                self.left_frame,
                text=column,
                width=20,
                command=lambda col=column: self.set_y_column(col),
            ).pack(pady=4)

        tk.Button(
            self.left_frame,
            text="Сохранить",
            width=20,
            command=self.save_plot,
        ).pack(side="bottom", pady=(20, 0))

        self.graph_canvas = tk.Canvas(
            self.center_frame,
            bg="white",
            bd=1,
            relief="sunken",
            highlightthickness=0,
        )
        self.graph_canvas.pack(fill="both", expand=True)

        tk.Label(self.bottom_frame, text="Ось X").pack(anchor="w")

        self.bottom_buttons_frame = tk.Frame(self.bottom_frame)
        self.bottom_buttons_frame.pack(fill="x", pady=(5, 0))

        for column in NUMERIC_COLUMNS:
            tk.Button(
                self.bottom_buttons_frame,
                text=column,
                width=20,
                command=lambda col=column: self.set_x_column(col),
            ).pack(side="left", padx=4)

    def set_x_column(self, column: str) -> None:
        self.x_column = column
        self.replace_plot()

    def set_y_column(self, column: str) -> None:
        self.y_column = column
        self.replace_plot()

    def create_plot_figure(self):
        fig, ax = plt.subplots(figsize=(8, 5.8), dpi=100)

        ax.scatter(
            df[self.x_column],
            df[self.y_column],
            marker=MARKER_STYLE,
        )

        ax.set_xlabel(self.x_column)
        ax.set_ylabel(self.y_column)
        ax.set_title(f"{self.y_column} / {self.x_column}")
        ax.grid(False)

        fig.tight_layout()
        return fig

    def figure_to_tk_image(self, fig):
        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        buffer = io.BytesIO()
        canvas.print_png(buffer)
        buffer.seek(0)

        image = Image.open(buffer)
        return ImageTk.PhotoImage(image)

    def clear_old_plot(self) -> None:
        if self.canvas_image_id is not None:
            self.graph_canvas.delete(self.canvas_image_id)
            self.canvas_image_id = None

        if self.current_figure is not None:
            plt.close(self.current_figure)
            self.current_figure = None

        self.current_tk_image = None

    def replace_plot(self) -> None:
        """
        Полностью заменяет отображаемый график новым.
        Это и есть процедура замены данных на отображаемом графике.
        """
        self.clear_old_plot()

        self.current_figure = self.create_plot_figure()
        self.current_tk_image = self.figure_to_tk_image(self.current_figure)

        self.graph_canvas.delete("all")
        self.canvas_image_id = self.graph_canvas.create_image(
            0,
            0,
            anchor="nw",
            image=self.current_tk_image,
        )

        self.graph_canvas.config(
            width=self.current_tk_image.width(),
            height=self.current_tk_image.height(),
            scrollregion=(0, 0, self.current_tk_image.width(), self.current_tk_image.height()),
        )

    def save_plot(self) -> None:
        if self.current_figure is None:
            return

        filename = datetime.now().strftime("graph%H_%M_%S.png")
        save_path = Path(__file__).resolve().parent / filename
        self.current_figure.savefig(save_path)

    def on_close(self) -> None:
        try:
            self.clear_old_plot()
            plt.close("all")
        except Exception:
            pass

        try:
            self.master.quit()
        except Exception:
            pass

        try:
            self.master.destroy()
        except Exception:
            pass


def main() -> None:
    root = tk.Tk()
    app = DataScatterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
