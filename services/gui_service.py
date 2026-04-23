

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Optional
from services.pdf_service import PDFService


class GUIService:

    def __init__(self):
        self.pdf_service = PDFService()
        self.current_pdf_text = ""
        self.current_file_path: Optional[Path] = None

    def select_pdf_file(self) -> Optional[Path]:
        #Sistema de seleccion de archivos PDF
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
            raise PermissionError(
                f"No se tiene permiso para leer el archivo: {file_path}"
            )
        except Exception as e:
            raise ValueError(f"Error al procesar el PDF: {str(e)}")

    def launch_main_window(self) -> None:
       
        
        main_window = self._create_main_window()
        self._configure_window_layout(main_window)
        main_window.mainloop()

    def _create_main_window(self) -> tk.Tk:
        #Configuración de la ventana principal
        window = tk.Tk()
        window.title("PDF ExtractText")
        window.geometry("600x600")
        window.configure(background="black")
        return window

    def _configure_window_layout(self, window: tk.Tk) -> None:
        #Config del GUI y creacion de los widgets
        file_label = self._create_title_label(window)
        browse_button = self._create_browse_button(window, file_label)

        self._create_action_button(window, "Exportar texto", self._export_text, 3)
        self._create_exit_button(window, 5)

        file_label.grid(column=1, row=1, pady=20)
        browse_button.grid(column=1, row=2, pady=10)

    def _create_title_label(self, window: tk.Tk) -> tk.Label:
        #Titulo principal
        return tk.Label(
            window,
            text="PDFExtractext",
            width=100,
            height=4,
            fg="white",
            bg="black"
        )

    def _create_browse_button(self, window: tk.Tk, label: tk.Label) -> tk.Button:
        #Crea el boton de búsqueda

        def handle_file_browse():
            file_path = self.select_pdf_file()
            if file_path:
                self.current_file_path = file_path
                try:
                    self.current_pdf_text = self.extract_pdf_content(file_path)
                    print(self.current_pdf_text)
                    label.configure(text=f"Archivo: {file_path.name}")
                except Exception as e:
                    self._show_error_message(str(e))

        return tk.Button(window, text="Buscar Archivo", command=handle_file_browse)

    def _create_action_button(
        self, window: tk.Tk, text: str, command, row: int
    ) -> tk.Button:
        #Crea botones que todavía no hacen nada

        def placeholder_function():
            self._show_info_message(f"Función '{text}' no implementada")

        button = tk.Button(
            window,
            text=text,
            command=command if self.current_file_path else placeholder_function,
        )
        button.grid(column=1, row=row, pady=10)
        return button

    def _create_exit_button(self, window: tk.Tk, row: int) -> tk.Button:
        #Botón para salir
        button = tk.Button(window, text="Cerrar", command=window.destroy)
        button.grid(column=1, row=row, pady=10)
        return button

    def _show_error_message(self, message: str) -> None:
        #Mensaje de error cuando sucede algo inesperado
        error_window = tk.Toplevel()
        error_window.title("Error")
        error_window.geometry("400x100")
        tk.Label(
            error_window, text=message, wraplength=350, fg="red", padx=10, pady=10
        ).pack()
        tk.Button(error_window, text="OK", command=error_window.destroy).pack(pady=10)

    def _show_info_message(self, message: str) -> None:
        #Muestra un mensaje con información al usuario
        info_window = tk.Toplevel()
        info_window.title("Información")
        info_window.geometry("400x100")
        tk.Label(info_window, text=message, wraplength=350, padx=10, pady=10).pack()
        tk.Button(info_window, text="OK", command=info_window.destroy).pack(pady=10)

    def _export_text(self) -> None:
        #Exportar el texto
        if not self.current_file_path:
            self._show_info_message("No hay archivo seleccionado")
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
                self._show_info_message(f"Texto exportado exitosamente a: {filename}")
            except Exception as e:
                self._show_error_message(f"Error al exportar: {str(e)}")
