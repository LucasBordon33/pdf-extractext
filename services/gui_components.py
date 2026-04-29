import tkinter as tk


class GUICreator:

    def __init__(self, gui_service):
        self.service = gui_service

    def create_main_window(self) -> tk.Tk:
        window = tk.Tk()
        window.title("PDF ExtractText")
        window.geometry("600x600")
        window.configure(background="black")
        return window

    def configure_layout(self, window: tk.Tk) -> None:
        file_label = self._create_title_label(window)
        browse_button = self._create_browse_button(window, file_label)
        self._create_action_button(window, "Exportar texto", self.service.export_text, 3)
        self._create_exit_button(window, 5)

        file_label.grid(column=1, row=1, pady=20)
        browse_button.grid(column=1, row=2, pady=10)

    def _create_title_label(self, window: tk.Tk) -> tk.Label:
        return tk.Label(
            window,
            text="PDFExtractext",
            width=100,
            height=4,
            fg="white",
            bg="black",
        )

    def _create_browse_button(self, window: tk.Tk, label: tk.Label) -> tk.Button:
        return tk.Button(
            window,
            text="Buscar Archivo",
            command=lambda: self.service.load_pdf_file_callback(label),
        )

    def _create_action_button(self, window: tk.Tk, text: str, command, row: int) -> tk.Button:
        def placeholder():
            self.service.show_info_message(f"Función '{text}' no implementada")

        button = tk.Button(
            window,
            text=text,
            command=command if self.service.current_file_path else placeholder,
        )
        button.grid(column=1, row=row, pady=10)
        return button

    def _create_exit_button(self, window: tk.Tk, row: int) -> tk.Button:
        button = tk.Button(window, text="Cerrar", command=window.destroy)
        button.grid(column=1, row=row, pady=10)
        return button
