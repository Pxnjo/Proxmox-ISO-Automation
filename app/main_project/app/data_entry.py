from ttkbootstrap.constants import *
import ttkbootstrap as ttk
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config, main_page

class DataEntryForm(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=(20, 10))
        self.pack(fill=BOTH, expand=YES)

        # form variables
        self.node = ttk.StringVar(value="")
        self.server = ttk.StringVar(value="")
        self.gateway = ttk.StringVar(value="")
        self.API_TOKEN = ttk.StringVar(value="")
        self.templateID = ttk.StringVar(value="")

        # form header
        hdr_txt = "Please enter your proxmox information" 
        hdr = ttk.Label(master=self, text=hdr_txt, width=50)
        hdr.pack(fill=X, pady=10)

        # form entries
        self.create_form_entry("Node", self.node)
        self.create_form_entry("Server", self.server)
        self.create_form_entry("Gateway", self.gateway)
        self.create_form_entry("API_TOKEN", self.API_TOKEN)
        self.create_form_entry("TemplateID", self.templateID)
        self.create_buttonbox()

    def create_form_entry(self, label, variable):
        """Create a single form entry"""
        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=5)

        lbl = ttk.Label(master=container, text=label.title(), width=10)
        lbl.pack(side=LEFT, padx=5)

        ent = ttk.Entry(master=container, textvariable=variable)
        ent.pack(side=LEFT, padx=5, fill=X, expand=YES)

    def create_buttonbox(self):
        """Create the application buttonbox"""
        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=(15, 10))

        sub_btn = ttk.Button(
            master=container,
            text="Submit",
            command=self.on_submit,
            bootstyle=SUCCESS,
            width=6,
        )
        sub_btn.pack(side=RIGHT, padx=5)
        sub_btn.focus_set()

        cnl_btn = ttk.Button(
            master=container,
            text="Cancel",
            command=self.on_cancel,
            bootstyle=DANGER,
            width=6,
        )
        cnl_btn.pack(side=RIGHT, padx=5)

    def on_submit(self):
        """Print the contents to console and return the values."""
        config.node = self.node.get()
        config.server = self.server.get()
        config.gateway = self.gateway.get()
        config.API_TOKEN = f"PVEAPIToken={self.API_TOKEN.get()}"
        config.templateID = self.templateID.get()
        # Chiude la finestra senza forzare subito la distruzione
        self.master.after(100, self.master.destroy)
        main_page.exe_app()

        return self.node.get(), self.server.get(), self.gateway.get(), self.API_TOKEN.get(),  self.templateID.get()

    def on_cancel(self):
        """Cancel and close the application."""
        self.quit()