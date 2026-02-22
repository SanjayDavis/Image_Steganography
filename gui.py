"""Image Steganography GUI  dark-themed, customtkinter."""

import os
import sys
import threading
from tkinter import filedialog, messagebox
from pathlib import Path

import customtkinter as ctk

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encryption.lsb_encrypt import lsb_embed
from encryption.dct_encrypt import dct_embed
from decryption.lsb_decrypt import lsb_extract
from decryption.dct_decrypt import dct_extract
from utils.compression import COMPRESSION_BACKEND

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# palette
_A    = "#1f6aa5"
_AH   = "#144870"
_CARD = "#1e1e2e"
_SIDE = "#181825"
_T    = "#cdd6f4"
_M    = "#6c7086"
_OK   = "#a6e3a1"


# widget helpers

def _lbl(parent, text, size=12, weight="normal", color=_T, **kw):
    return ctk.CTkLabel(parent, text=text, text_color=color,
                        font=ctk.CTkFont(size=size, weight=weight), **kw)


def _entry(parent, placeholder="", default="", **kw):
    e = ctk.CTkEntry(parent, fg_color="#313244", border_color="#45475a",
                     text_color=_T, height=36,
                     placeholder_text=placeholder, **kw)
    if default:
        e.insert(0, default)
    return e


def _btn(parent, text, cmd, accent=True, **kw):
    return ctk.CTkButton(parent, text=text, command=cmd,
                         fg_color=_A if accent else "#313244",
                         hover_color=_AH if accent else "#45475a", **kw)


def _card(parent, title):
    f = ctk.CTkFrame(parent, corner_radius=12, fg_color=_CARD,
                     border_width=1, border_color="#313244")
    _lbl(f, title.upper(), size=10, weight="bold", color=_M
         ).pack(anchor="w", padx=16, pady=(12, 0))
    return f


# FilePicker

class FilePicker(ctk.CTkFrame):
    def __init__(self, master, label, mode="file", filetypes=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._mode = mode
        self._filetypes = filetypes or [("All files", "*.*")]
        self._var = ctk.StringVar()

        _lbl(self, label, size=13, weight="bold").pack(anchor="w", pady=(8, 2))
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkEntry(row, textvariable=self._var, fg_color="#313244",
                     border_color="#45475a", text_color=_T, height=36,
                     placeholder_text="Click Browse or type a path"
                     ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        _btn(row, "Browse", self._browse, width=90).pack(side="left")

    def _browse(self):
        path = (filedialog.askdirectory(title="Select Folder")
                if self._mode == "folder"
                else filedialog.askopenfilename(title="Select File",
                                                filetypes=self._filetypes))
        if path:
            self._var.set(path)

    @property
    def value(self):
        return self._var.get().strip()

    def set(self, v):
        self._var.set(v)


# KeyDialog

class KeyDialog(ctk.CTkToplevel):
    def __init__(self, parent, key, output_path=""):
        super().__init__(parent)
        self.title("Encryption Key")
        self.geometry("640x260")
        self.resizable(False, False)
        self.grab_set()

        _lbl(self, "Encryption Key", size=16, weight="bold").pack(pady=(20, 4))
        _lbl(self, "Store this key securely  it is required to recover your file.",
             color=_M).pack()
        if output_path:
            _lbl(self, f"Saved to: {output_path}", color=_OK, size=11).pack(pady=(4, 0))

        box = ctk.CTkTextbox(self, height=80, wrap="word", fg_color="#313244",
                             text_color=_T, font=ctk.CTkFont(family="Consolas", size=11))
        box.pack(fill="x", padx=20, pady=12)
        box.insert("1.0", key)
        box.configure(state="disabled")

        def copy():
            self.clipboard_clear()
            self.clipboard_append(key)
            cb.configure(text="Copied!", fg_color=_OK, text_color="#1e1e2e")
            self.after(2000, lambda: cb.configure(text="Copy Key",
                                                  fg_color=_A, text_color="white"))

        cb = _btn(self, "Copy Key", copy)
        cb.pack(pady=4)
        _btn(self, "Close", self.destroy, accent=False).pack(pady=(4, 16))


# Base panel

class _BasePanel(ctk.CTkScrollableFrame):
    def __init__(self, master, status_cb, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._set_status = status_cb

    def _run_task(self, fn, *args, on_success=None):
        self._set_status("busy")
        def worker():
            try:
                result = fn(*args)
                self.after(0, lambda r=result: (self._set_status("ready"),
                                                on_success and on_success(r)))
            except Exception as exc:
                self.after(0, lambda e=exc: (self._set_status("ready"),
                                             messagebox.showerror("Error", str(e), parent=self)))
        threading.Thread(target=worker, daemon=True).start()

    def _require(self, value, msg):
        if not value:
            messagebox.showwarning("Missing Field", msg, parent=self)
        return bool(value)

    def _header(self, title, subtitle):
        _lbl(self, title, size=22, weight="bold").pack(anchor="w", pady=(0, 4))
        _lbl(self, subtitle, size=12, color=_M).pack(anchor="w", pady=(0, 16))


# Encrypt panel  (LSB and DCT share this)

class EncryptPanel(_BasePanel):
    def __init__(self, master, status_cb, *, technique, embed_fn,
                 default_fname, subtitle, **kw):
        super().__init__(master, status_cb, **kw)
        self._embed_fn = embed_fn
        self._default  = default_fname
        self._header(f"Encrypt ({technique})", subtitle)

        in_c = _card(self, "Input")
        in_c.pack(fill="x", pady=(0, 12))
        self._cover = FilePicker(in_c, "Cover Image",
                                 filetypes=[("Images", "*.png *.bmp *.jpg *.jpeg"),
                                            ("All", "*.*")])
        self._cover.pack(fill="x", padx=16)
        self._secret = FilePicker(in_c, "Secret File")
        self._secret.pack(fill="x", padx=16, pady=(0, 12))

        out_c = _card(self, "Output")
        out_c.pack(fill="x", pady=(0, 12))
        self._out_dir = FilePicker(out_c, "Save Directory", mode="folder")
        self._out_dir.set("images")
        self._out_dir.pack(fill="x", padx=16)
        _lbl(out_c, "Output Filename", size=13, weight="bold"
             ).pack(anchor="w", padx=16, pady=(8, 2))
        self._fname = _entry(out_c, default=default_fname)
        self._fname.pack(fill="x", padx=16, pady=(0, 12))

        _btn(self, "Embed File into Image", self._embed, height=44,
             font=ctk.CTkFont(size=14, weight="bold")).pack(fill="x", pady=(8, 0))

    def _embed(self):
        if not self._require(self._cover.value, "Please select a Cover Image."): return
        if not self._require(self._secret.value, "Please select a Secret File."): return
        self._run_task(self._embed_fn,
                       self._cover.value, self._secret.value,
                       self._out_dir.value or "images",
                       self._fname.get().strip() or self._default,
                       on_success=self._show_key)

    def _show_key(self, key):
        stem = os.path.splitext(self._fname.get().strip() or self._default)[0]
        out  = os.path.join(self._out_dir.value or "images", stem + ".png")
        KeyDialog(self, key, output_path=out)


# Decrypt panel  (LSB and DCT share this)

class DecryptPanel(_BasePanel):
    def __init__(self, master, status_cb, *, technique, extract_fn,
                 img_filetypes, subtitle, **kw):
        super().__init__(master, status_cb, **kw)
        self._extract_fn = extract_fn
        self._header(f"Decrypt ({technique})", subtitle)

        in_c = _card(self, "Input")
        in_c.pack(fill="x", pady=(0, 12))
        self._stego = FilePicker(in_c, "Stego Image", filetypes=img_filetypes)
        self._stego.pack(fill="x", padx=16)

        _lbl(in_c, "Decryption Key", size=13, weight="bold"
             ).pack(anchor="w", padx=16, pady=(8, 2))
        row = ctk.CTkFrame(in_c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 12))
        self._key_var = ctk.StringVar()
        self._key_entry = _entry(row, placeholder="Paste your Fernet key here",
                                 show="*", textvariable=self._key_var)
        self._key_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._visible = False
        self._eye = _btn(row, "Show", self._toggle_vis, accent=False, width=70)
        self._eye.pack(side="left")

        out_c = _card(self, "Output")
        out_c.pack(fill="x", pady=(0, 12))
        self._out_dir = FilePicker(out_c, "Save Directory", mode="folder")
        self._out_dir.set("extracted")
        self._out_dir.pack(fill="x", padx=16, pady=(0, 12))

        _btn(self, "Extract Hidden File", self._extract, height=44,
             font=ctk.CTkFont(size=14, weight="bold")).pack(fill="x", pady=(8, 0))

    def _toggle_vis(self):
        self._visible = not self._visible
        self._key_entry.configure(show="" if self._visible else "*")
        self._eye.configure(text="Hide" if self._visible else "Show")

    def _extract(self):
        key = self._key_var.get().strip()
        if not self._require(self._stego.value, "Please select a Stego Image."): return
        if not self._require(key, "Please enter the Decryption Key."): return
        self._run_task(self._extract_fn,
                       self._stego.value, key, self._out_dir.value or "extracted",
                       on_success=self._show_result)

    def _show_result(self, result):
        meta = result.get("metadata", {})
        messagebox.showinfo("Extraction Successful",
                            f"File recovered!\n\n"
                            f"Name:          {meta.get('name', '')}\n"
                            f"Original size: {meta.get('original_size', '')} bytes\n"
                            f"Saved to:      {result['output_path']}", parent=self)


# About panel

class AboutPanel(ctk.CTkScrollableFrame):
    _SECTIONS = [
        ("What is Steganography?",
         "Steganography hides secret data inside ordinary files so that only the "
         "intended recipient knows a message exists. Unlike encryption alone, it "
         "conceals the very existence of the message."),
        ("LSB Technique",
         "Least Significant Bit steganography replaces the lowest-order bit of each "
         "pixel channel with a payload bit. The change is imperceptible. Works best "
         "with lossless PNG/BMP images."),
        ("DCT Technique",
         "DCT steganography embeds data into mid-frequency coefficients of 8x8 image "
         "blocks (similar to JPEG compression). More robust than LSB but lower capacity."),
        ("Compression", None),
        ("Encryption",
         "Compressed data is encrypted with Fernet (AES-128 CBC + HMAC-SHA256). "
         "A unique key is generated per embedding - keep it safe."),
    ]

    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        _lbl(self, "About", size=22, weight="bold").pack(anchor="w", pady=(0, 4))
        _lbl(self, "How this tool works.", size=12, color=_M
             ).pack(anchor="w", pady=(0, 20))
        for title, body in self._SECTIONS:
            if body is None:
                body = (f"Payload files are compressed with {COMPRESSION_BACKEND.upper()} "
                        "before encryption, reducing bits that must be hidden and "
                        "increasing effective capacity of the cover image.")
            c = ctk.CTkFrame(self, corner_radius=12, fg_color=_CARD,
                             border_width=1, border_color="#313244")
            c.pack(fill="x", pady=6)
            _lbl(c, title, size=13, weight="bold", color=_A, anchor="w"
                 ).pack(anchor="w", padx=16, pady=(12, 4))
            _lbl(c, body, size=12, anchor="w", wraplength=480, justify="left"
                 ).pack(anchor="w", padx=16, pady=(0, 12))


# Application

_IMG_LSB = [("Images", "*.png *.bmp"), ("All", "*.*")]
_IMG_DCT = [("Images", "*.png *.jpg *.jpeg"), ("All", "*.*")]

class App(ctk.CTk):
    _NAV = [
        ("Encrypt LSB", "encrypt_lsb"),
        ("Encrypt DCT", "encrypt_dct"),
        ("Decrypt LSB", "decrypt_lsb"),
        ("Decrypt DCT", "decrypt_dct"),
        ("About",       "about"),
    ]

    def __init__(self):
        super().__init__()
        self.title("Image Steganography")
        self.geometry("960x680")
        self.minsize(800, 560)
        self.configure(fg_color="#11111b")
        self._panels, self._nav_btns = {}, {}
        self._build()
        self._switch("encrypt_lsb")

    def _build(self):
        sb = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=_SIDE)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        lf = ctk.CTkFrame(sb, fg_color="transparent")
        lf.pack(fill="x", pady=(28, 8))
        _lbl(lf, "STEG", size=26, weight="bold", color=_A).pack()
        _lbl(lf, "steganography", size=9, color=_M).pack(pady=(2, 0))
        ctk.CTkFrame(sb, height=1, fg_color="#313244").pack(fill="x", padx=12, pady=12)

        for label, key in self._NAV:
            b = ctk.CTkButton(sb, text=label, anchor="w", height=40,
                              corner_radius=8, font=ctk.CTkFont(size=13),
                              fg_color="transparent", text_color=_T,
                              hover_color="#313244",
                              command=lambda k=key: self._switch(k))
            b.pack(fill="x", padx=10, pady=2)
            self._nav_btns[key] = b

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)
        self._content = ctk.CTkFrame(right, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=28, pady=24)

    def _switch(self, key):
        for k, b in self._nav_btns.items():
            b.configure(fg_color=_A if k == key else "transparent",
                        text_color="white" if k == key else _T)
        if key not in self._panels:
            self._panels[key] = self._make(key)
        for p in self._panels.values():
            p.pack_forget()
        self._panels[key].pack(fill="both", expand=True)

    def _make(self, key):
        c, cb = self._content, self._status
        if key == "encrypt_lsb":
            return EncryptPanel(c, cb, technique="LSB", embed_fn=lsb_embed,
                default_fname="output.png",
                subtitle="Hide a file inside a PNG image using Least Significant Bit steganography.")
        if key == "encrypt_dct":
            return EncryptPanel(c, cb, technique="DCT", embed_fn=dct_embed,
                default_fname="output_dct.png",
                subtitle="Hide a file inside an image using mid-band DCT coefficient steganography.")
        if key == "decrypt_lsb":
            return DecryptPanel(c, cb, technique="LSB", extract_fn=lsb_extract,
                img_filetypes=_IMG_LSB,
                subtitle="Extract and recover a hidden file from an LSB stego image.")
        if key == "decrypt_dct":
            return DecryptPanel(c, cb, technique="DCT", extract_fn=dct_extract,
                img_filetypes=_IMG_DCT,
                subtitle="Extract and recover a hidden file from a DCT stego image.")
        return AboutPanel(c)

    def _status(self, state):
        self.title("Image Steganography  Processing..."
                   if state == "busy" else "Image Steganography")


if __name__ == "__main__":
    App().mainloop()