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
    frame.pack(fill=BOTH, expand=YES, pady=10, padx=10)

    # Crea un widget Text per visualizzare i log
    log_text = tkinter.Text(frame, height=10, wrap="word")
    log_text.pack(side=LEFT, fill=BOTH, expand=YES)

    # Crea una scrollbar verticale
    scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, bootstyle="round", command=log_text.yview)
    scrollbar.pack(side=RIGHT, fill=Y)

    # Collega lo scrollbar al widget Text
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

    # Crea il log box e reindirizza l'output
    log_box = create_log_box(app)
    sys.stdout = RedirectText(log_box)
    sys.stderr = RedirectText(log_box)

    # Avvia script.main() in un thread separato per non bloccare l'UI
    thread = threading.Thread(target=script.main, daemon=True)
    thread.start()

    del_btn(app)
    app.mainloop()