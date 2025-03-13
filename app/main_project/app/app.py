from ttkbootstrap.constants import *
import ttkbootstrap as ttk
from PIL import Image
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import data_entry

script_dir = os.path.dirname(os.path.abspath(__file__))  # Ottiene la cartella dello script
icon_path = os.path.join(script_dir, 'x.ico')  # Crea il percorso corretto
im = Image.open(icon_path)

if __name__ == "__main__":
    app = ttk.Window("ISO Tester", "darkly", resizable=(False, False))
    app.iconbitmap(icon_path)
    data_entry.DataEntryForm(app)
    app.mainloop()
