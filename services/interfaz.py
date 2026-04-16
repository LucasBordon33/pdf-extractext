import tkinter as tk
from tkinter import filedialog
from io import BytesIO
from typing import Optional
from fastapi import UploadFile
from services.pdf_service import PDFService


class Interfaz:

    def __init__(self):
        self.current_pdf_text = "" 
        self.pdf_manager = PDFService() 

    # Función búsqueda de archivos
    def browse_pdf(self):
        filename = filedialog.askopenfilename(
            initialdir="/",
            title="Elija un archivo",
            filetypes=[("Archivos PDF", "*.pdf")]
        )

        if not filename:
            return None

        with open(filename, "rb") as f:
            content = f.read()
        """
        upload_file = UploadFile(
            filename=filename.split("/")[-1], 
            file=BytesIO(content)
        ) 
        """ # Con la refactorización que hice no necesitamos ^, pero lo voy a dejar un par de commits por si lo necesitamos después
        self.current_pdf_text = self.pdf_manager.extract_text(content)
        

    def panel_runner(self):
        # Creación y definición de ventana
        window = tk.Tk()
        window.title("PDF ExtractText")
        window.geometry("600x600")
        window.configure(background="black")

        label = tk.Label(
            window,
            text="PDF ExtractText",
            width=100,
            height=4,
            fg="white",
            bg="black"
        )

        uploaded_file: Optional[UploadFile] = None

        def on_browse():
            nonlocal uploaded_file
            uploaded_file = self.browse_pdf()
            if uploaded_file:
                label.configure(text=f"Archivo: {uploaded_file.filename}")

        # Para las funciones que aún no han sido añadidas
        def placeholder():
            return 0        

        # Botones
        btn_browse = tk.Button(window, text="Buscar Archivo", command=on_browse)
        btn_export = tk.Button(window, text="Exportar texto", command=placeholder) 
        btn_sumUp = tk.Button(window, text="Resumen", command=placeholder)
        btn_exit = tk.Button(window, text="Cerrar", command=window.destroy)

        label.grid(column=1, row=1, pady=20)
        btn_browse.grid(column=1, row=2, pady=10)
        btn_export.grid(column=1, row=3, pady=10)
        btn_sumUp.grid(column=1, row=4, pady=10)
        btn_exit.grid(column=1, row=5, pady=10)

        window.mainloop()
        return uploaded_file

