from ttkbootstrap.constants import *
import ttkbootstrap as ttk
from PIL import Image
import threading
import tkinter
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import script, delete

script_dir = os.path.dirname(os.path.abspath(__file__))  # Ottiene la cartella dello script
icon_path = os.path.join(script_dir, 'x.ico')  # Crea il percorso corretto
im = Image.open(icon_path)

def create_log_box(master):
    # Crea un frame per contenere il Text e la Scrollbar
    frame = ttk.Frame(master)
    frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    # Configura il frame per espandersi
    master.columnconfigure(0, weight=1)
    master.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    
    # Crea un widget Text
    log_text = tkinter.Text(frame, wrap="word")
    log_text.grid(row=0, column=0, sticky="nsew")
    
    # Crea scrollbar
    scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, bootstyle="round", command=log_text.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    
    # Collega scrollbar al Text
    log_text.config(yscrollcommand=scrollbar.set)
    
    return log_text

class RedirectText(object):
    def __init__(self, widget):
        self.widget = widget

    def write(self, string):
        # Inserisce il testo nel widget Text
        self.widget.insert(tkinter.END, string)
        # Scorre automaticamente in fondo al testo
        self.widget.see(tkinter.END)

    def flush(self):
        # Metodo richiesto per compatibilità, non fa nulla
        pass

def delete_vm_and_disable_button(button):
    delete.main()  # Esegue la funzione di eliminazione
    if delete.state:  # Controlla se lo stato è stato aggiornato
        button.config(state="disabled")  # Disabilita il pulsante

def del_btn(master):
    container = ttk.Frame(master)
    container.pack(fill=X, expand=YES, pady=(15, 10))

    del_btn = ttk.Button(
        master=container,
        text="Delete VM",
        command=lambda: delete_vm_and_disable_button(del_btn),
        bootstyle=DANGER,
        width=6,
    )
    del_btn.pack(side=RIGHT, padx=5)
    if delete.state:
         del_btn.config(state="disabled")

def exe_app():
    app = ttk.Window("ISO Tester", "darkly")
    app.iconbitmap(icon_path)
    app.geometry("800x600")
    
    # Configura la griglia principale
    app.columnconfigure(0, weight=1)
    app.rowconfigure(0, weight=1)
    app.rowconfigure(1, weight=0)  # Riga per il pulsante, non deve espandersi
    
    # Area log
    log_box = create_log_box(app)
    sys.stdout = RedirectText(log_box)
    sys.stderr = RedirectText(log_box)
    
    # Avvia script
    thread = threading.Thread(target=script.main, daemon=True)
    thread.start()
    
    # Frame pulsante
    button_frame = ttk.Frame(app)
    button_frame.grid(row=1, column=0, sticky="e", padx=10, pady=10)
    
    # Pulsante
    del_btn_instance = ttk.Button(
        master=button_frame,
        text="Delete VM",
        command=lambda: delete_vm_and_disable_button(del_btn_instance),
        bootstyle=DANGER,
        width=6,
    )
    del_btn_instance.pack(side=RIGHT)
    if delete.state:
        del_btn_instance.config(state="disabled")
    
    app.mainloop()