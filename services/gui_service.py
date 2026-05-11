import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Optional
from services.pdf_service import PDFService
from services.gui_components import GUICreator


class GUIService:

    def __init__(self):
        self.pdf_service = PDFService()
        self.current_pdf_text = ""
        self.current_file_path: Optional[Path] = None
        self.ui = GUICreator(self)

    def select_pdf_file(self) -> Optional[Path]:
        file_path_str = filedialog.askopenfilename(
            initialdir="/",
            title="Elija un archivo",
            filetypes=[("Archivos PDF", "*.pdf")],
        )
        if not file_path_str:
            return None
        return Path(file_path_str)

    def extract_pdf_content(self, file_path: Path) -> str:
        try:
            with open(file_path, "rb") as pdf_file:
                file_content = pdf_file.read()
                return self.pdf_service._extract_text_from_pdf_stream(file_content)
        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo no fue encontrado: {file_path}")
        except PermissionError:
            raise PermissionError(f"No se tiene permiso para leer el archivo: {file_path}")
        except Exception as e:
            raise ValueError(f"Error al procesar el PDF: {str(e)}")

    def load_pdf_file(self, file_path: Path, file_label: tk.Label) -> None:
        self.current_file_path = file_path
        try:
            self.current_pdf_text = self.extract_pdf_content(file_path)
            file_label.configure(text=f"Archivo: {file_path.name}")
        except Exception as e:
            self.show_error_message(str(e))

    def export_text(self):
        if not self.current_file_path:
            self.show_info_message("No hay archivo seleccionado")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt")],
            initialfile=self.current_file_path.stem,
        )

        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.current_pdf_text)
                self.show_info_message(f"Texto exportado exitosamente a: {filename}")
            except Exception as e:
                self.show_error_message(f"Error al exportar: {str(e)}")

    def show_error_message(self, message: str) -> None:
        error_window = tk.Toplevel()
        error_window.title("Error")
        error_window.geometry("400x100")
        tk.Label(error_window, text=message, wraplength=350, fg="red", padx=10, pady=10).pack()
        tk.Button(error_window, text="OK", command=error_window.destroy).pack(pady=10)

    def show_info_message(self, message: str) -> None:
        info_window = tk.Toplevel()
        info_window.title("Información")
        info_window.geometry("400x100")
        tk.Label(info_window, text=message, wraplength=350, padx=10, pady=10).pack()
        tk.Button(info_window, text="OK", command=info_window.destroy).pack(pady=10)

    def launch_main_window(self) -> None:
        main_window = self.ui.create_main_window()
        self.ui.configure_layout(main_window)
        main_window.mainloop()

    def load_pdf_file_callback(self, label: tk.Label) -> None:
        file_path = self.select_pdf_file() 
        if file_path:
            self.load_pdf_file(file_path, label)
    
