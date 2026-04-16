import tkinter as tk
from tkinter import filedialog
from io import BytesIO
from typing import Optional
from fastapi import UploadFile
from pdf_service import PDFService


johnny = PDFService()

# Función busqueda de archivos
def browse_pdf() -> Optional[UploadFile]:
    filename = filedialog.askopenfilename(
        initialdir="/",
        title="Elija un archivo",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

    if not filename:
        return None

    with open(filename, "rb") as f:
        content = f.read()

    upload_file = UploadFile(
        filename=filename.split("/")[-1],
        file=BytesIO(content)
    )

    return upload_file

def main():
    #Creación y definicion de ventana
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
        uploaded_file = browse_pdf()
        if uploaded_file:
            label.configure(text=f"Archivo: {uploaded_file.filename}")

    #Para las funciones que aun no han sido añadidas
    def placeholder():
        return 0        
    
    #Botones
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
