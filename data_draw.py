import io
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, colorchooser

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image, ImageTk, ImageDraw

import dataset

# Данные из задания 1
df = dataset.df

NUMERIC_COLUMNS = [
    "Rating",
    "Refresh Rate (Hz)",
    "Price (USD)",
    "Rating.1",
]

CATEGORICAL_COLUMNS = [
    "Brand",
    "Model",
    "Selling Platform",
]

ALL_COLUMNS = NUMERIC_COLUMNS + CATEGORICAL_COLUMNS

# Индивидуальные параметры
MARKER_STYLE = ">"
DEFAULT_CMAP = "inferno"
DEFAULT_LINE_WIDTH = 6
DEFAULT_BRUSH_COLOR = "#0f4327"

CMAP_OPTIONS = [
    "viridis", "plasma", "inferno", "magma", "cividis",
    "Greys", "Purples", "Blues", "Greens", "Oranges",
    "Reds", "YlOrBr", "YlOrRd", "OrRd", "PuRd",
    "RdPu", "BuPu", "GnBu", "PuBu", "YlGnBu",
    "PuBuGn", "BuGn", "YlGn", "binary", "gist_yarg",
    "spring", "summer", "autumn", "winter",
]


class DataDrawApp:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("data_draw")
        self.master.geometry("1240x860")
        self.master.minsize(1080, 760)
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.x_column = ALL_COLUMNS[0]
        self.y_column = ALL_COLUMNS[1]
        self.cmap_name = tk.StringVar(value=DEFAULT_CMAP)
        self.line_width_var = tk.IntVar(value=DEFAULT_LINE_WIDTH)

        self.brush_color = DEFAULT_BRUSH_COLOR
        self.draw_mode = False
        self.is_drawing = False

        self.current_figure = None
        self.base_image = None
        self.overlay_image = None
        self.overlay_draw = None
        self.current_tk_image = None
        self.canvas_image_id = None

        self.current_line_backup = None

        self.build_interface()
        self.bind_events()
        self.replace_plot()

    def build_interface(self) -> None:
        self.top_frame = tk.Frame(self.master, padx=10, pady=8)
        self.top_frame.pack(side="top", fill="x")

        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill="both", expand=True)

        self.left_frame = tk.Frame(self.main_frame, padx=10, pady=10)
        self.left_frame.pack(side="left", fill="y")

        self.center_frame = tk.Frame(self.main_frame, padx=10, pady=10)
        self.center_frame.pack(side="left", fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.master, padx=10, pady=10)
        self.bottom_frame.pack(side="bottom", fill="x")

        tk.Label(self.top_frame, text="Цветовая схема (cmap):").pack(side="left")

        self.cmap_combobox = ttk.Combobox(
            self.top_frame,
            textvariable=self.cmap_name,
            values=CMAP_OPTIONS,
            state="readonly",
            width=16,
        )
        self.cmap_combobox.pack(side="left", padx=(8, 18))
        self.cmap_combobox.bind("<<ComboboxSelected>>", self.on_cmap_change)

        self.draw_button = tk.Button(
            self.top_frame,
            text="Рисование",
            width=14,
            relief="raised",
            command=self.toggle_draw_mode,
        )
        self.draw_button.pack(side="left", padx=(0, 16))

        tk.Label(self.top_frame, text="Толщина:").pack(side="left")
        self.line_width_spinbox = tk.Spinbox(
            self.top_frame,
            from_=1,
            to=50,
            width=5,
            textvariable=self.line_width_var,
        )
        self.line_width_spinbox.pack(side="left", padx=(6, 16))

        tk.Label(self.top_frame, text="Цвет:").pack(side="left")
        self.color_button = tk.Button(
            self.top_frame,
            width=3,
            bg=self.brush_color,
            activebackground=self.brush_color,
            command=self.choose_color,
        )
        self.color_button.pack(side="left", padx=(6, 0))

        tk.Label(self.left_frame, text="Ось Y").pack(pady=(0, 10))

        for column in ALL_COLUMNS:
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

        for column in ALL_COLUMNS:
            tk.Button(
                self.bottom_buttons_frame,
                text=column,
                width=16,
                command=lambda col=column: self.set_x_column(col),
            ).pack(side="left", padx=3)

    def bind_events(self) -> None:
        self.graph_canvas.bind("<ButtonPress-1>", self.start_draw)
        self.graph_canvas.bind("<B1-Motion>", self.draw_motion)
        self.graph_canvas.bind("<ButtonRelease-1>", self.end_draw)
        self.graph_canvas.bind("<Button-3>", self.cancel_draw_mode)
        self.master.bind("<Control-z>", self.undo_last_line)

    def on_cmap_change(self, event=None) -> None:
        self.exit_draw_mode()
        self.replace_plot()

    def set_x_column(self, column: str) -> None:
        self.exit_draw_mode()
        self.x_column = column
        self.replace_plot()

    def set_y_column(self, column: str) -> None:
        self.exit_draw_mode()
        self.y_column = column
        self.replace_plot()

    def choose_color(self) -> None:
        result = colorchooser.askcolor(color=self.brush_color, title="Выбор цвета")
        if result and result[1]:
            self.brush_color = result[1]
            self.color_button.configure(
                bg=self.brush_color,
                activebackground=self.brush_color,
            )

    def toggle_draw_mode(self) -> None:
        if self.draw_mode:
            self.exit_draw_mode()
        else:
            self.draw_mode = True
            self.draw_button.configure(relief="sunken")
            self.graph_canvas.configure(cursor="pencil")

    def exit_draw_mode(self) -> None:
        self.draw_mode = False
        self.is_drawing = False
        self.draw_button.configure(relief="raised")
        self.graph_canvas.configure(cursor="")

    def cancel_draw_mode(self, event=None) -> None:
        self.exit_draw_mode()

    def is_numeric(self, column: str) -> bool:
        return column in NUMERIC_COLUMNS

    def is_categorical(self, column: str) -> bool:
        return column in CATEGORICAL_COLUMNS

    def get_colors(self, count: int):
        cmap = plt.get_cmap(self.cmap_name.get())
        if count <= 1:
            return [cmap(0.6)]
        return [cmap(i / max(count - 1, 1)) for i in range(count)]

    def create_scatter_plot(self, ax) -> None:
        ax.scatter(
            df[self.x_column],
            df[self.y_column],
            marker=MARKER_STYLE,
        )
        ax.set_xlabel(self.x_column)
        ax.set_ylabel(self.y_column)
        ax.set_title(f"{self.y_column} / {self.x_column}")

    def create_histogram(self, ax) -> None:
        series = df[self.x_column].dropna()
        _, _, patches = ax.hist(series, bins=10)

        colors = self.get_colors(len(patches))
        for patch, color in zip(patches, colors):
            patch.set_facecolor(color)

        ax.set_xlabel(self.x_column)
        ax.set_ylabel("Частота")
        ax.set_title(f"Гистограмма: {self.x_column}")

    def create_pie_chart(self, ax) -> None:
        counts = df[self.x_column].value_counts(dropna=False)
        colors = self.get_colors(len(counts))

        ax.pie(
            counts.values,
            labels=counts.index.astype(str),
            autopct="%1.1f%%",
            colors=colors,
        )
        ax.set_title(f"Круговая диаграмма: {self.x_column}")

    def create_bar_chart(self, ax) -> None:
        counts = df[self.x_column].value_counts(dropna=False)
        colors = self.get_colors(len(counts))

        ax.bar(
            counts.index.astype(str),
            counts.values,
            color=colors,
        )
        ax.set_xlabel(self.x_column)
        ax.set_ylabel("Количество")
        ax.set_title(f"Столбчатая диаграмма: {self.x_column}")

    def create_boxplot(self, ax) -> None:
        grouped = []
        labels = []

        grouped_series = df[[self.x_column, self.y_column]].dropna().groupby(self.y_column)

        for category, group in grouped_series:
            grouped.append(group[self.x_column].values)
            labels.append(str(category))

        bp = ax.boxplot(
            grouped,
            tick_labels=labels,
            patch_artist=True,
            vert=False,
        )

        colors = self.get_colors(len(bp["boxes"]))
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)

        ax.set_xlabel(self.x_column)
        ax.set_ylabel(self.y_column)
        ax.set_title(f"Коробочная диаграмма: {self.x_column} / {self.y_column}")

    def create_plot_figure(self):
        fig, ax = plt.subplots(figsize=(8, 5.8), dpi=100)

        x_is_num = self.is_numeric(self.x_column)
        y_is_num = self.is_numeric(self.y_column)
        x_is_cat = self.is_categorical(self.x_column)
        y_is_cat = self.is_categorical(self.y_column)

        if x_is_num and y_is_num and self.x_column == self.y_column:
            self.create_histogram(ax)
        elif x_is_cat and y_is_cat and self.x_column == self.y_column:
            self.create_pie_chart(ax)
        elif x_is_cat and y_is_num:
            self.create_bar_chart(ax)
        elif x_is_num and y_is_cat:
            self.create_boxplot(ax)
        else:
            self.create_scatter_plot(ax)

        fig.tight_layout()
        return fig

    def figure_to_pil_image(self, fig):
        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        buffer = io.BytesIO()
        canvas.print_png(buffer)
        buffer.seek(0)

        return Image.open(buffer).convert("RGBA")

    def compose_current_image(self):
        return Image.alpha_composite(self.base_image.copy(), self.overlay_image)

    def clear_old_plot(self) -> None:
        if self.canvas_image_id is not None:
            self.graph_canvas.delete(self.canvas_image_id)
            self.canvas_image_id = None

        if self.current_figure is not None:
            plt.close(self.current_figure)
            self.current_figure = None

        self.base_image = None
        self.overlay_image = None
        self.overlay_draw = None
        self.current_tk_image = None
        self.current_line_backup = None

    def replace_plot(self) -> None:
        """
        Полная замена данных и графика на экране.
        Старый график удаляется, новый строится заново.
        """
        self.clear_old_plot()

        self.current_figure = self.create_plot_figure()
        self.base_image = self.figure_to_pil_image(self.current_figure)
        self.overlay_image = Image.new("RGBA", self.base_image.size, (255, 255, 255, 0))
        self.overlay_draw = ImageDraw.Draw(self.overlay_image)

        self.render_canvas()

    def render_canvas(self) -> None:
        composed = self.compose_current_image()
        self.current_tk_image = ImageTk.PhotoImage(composed)

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

    def point_inside_graph(self, x: int, y: int) -> bool:
        if self.base_image is None:
            return False
        return 0 <= x < self.base_image.width and 0 <= y < self.base_image.height

    def draw_square(self, x: int, y: int) -> None:
        size = self.line_width_var.get()
        half = size // 2
        x0 = x - half
        y0 = y - half
        x1 = x + half
        y1 = y + half
        self.overlay_draw.rectangle([x0, y0, x1, y1], fill=self.brush_color)

    def start_draw(self, event) -> None:
        if not self.draw_mode:
            return
        if not self.point_inside_graph(event.x, event.y):
            return

        self.is_drawing = True
        self.current_line_backup = self.overlay_image.copy()

        self.draw_square(event.x, event.y)
        self.render_canvas()

    def draw_motion(self, event) -> None:
        if not self.draw_mode or not self.is_drawing:
            return
        if not self.point_inside_graph(event.x, event.y):
            return

        self.draw_square(event.x, event.y)
        self.render_canvas()

    def end_draw(self, event) -> None:
        if not self.draw_mode:
            return
        self.is_drawing = False

    def undo_last_line(self, event=None) -> None:
        if self.is_drawing:
            return
        if self.current_line_backup is None:
            return

        self.overlay_image = self.current_line_backup.copy()
        self.overlay_draw = ImageDraw.Draw(self.overlay_image)
        self.current_line_backup = None
        self.render_canvas()

    def save_plot(self) -> None:
        if self.base_image is None:
            return

        composed = self.compose_current_image()
        filename = datetime.now().strftime("graph%H_%M_%S.png")
        save_path = Path(__file__).resolve().parent / filename
        composed.save(save_path)

    def on_close(self) -> None:
        try:
            self.exit_draw_mode()
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
    app = DataDrawApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
