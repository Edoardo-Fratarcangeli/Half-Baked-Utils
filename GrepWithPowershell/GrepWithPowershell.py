import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import PyPDF2
import ctypes
from SearchHelper import searcher  # <-- Il tuo helper con PDF, Word, Excel, TXT ecc.

class GrepWithPowershell:

    def __init__(self, root):
        """Initialize the application"""

        # ------------------------------
        # Hidden root keeps taskbar icon
        # ------------------------------
        self.root = root
        self.root.withdraw()

        # ------------------------------
        # Main window as Toplevel
        # ------------------------------
        self.window = tk.Toplevel(self.root)
        self.window.title("Grep With Powershell")
        self.center_window(width=1000, height=700)
        self.window.resizable(True, True)

        # ------------------------------
        # Modern color scheme - grayscale palette
        # ------------------------------
        self.colors = {
            'bg_dark': '#1e1e1e',
            'bg_medium': '#2d2d2d',
            'bg_light': '#3c3c3c',
            'bg_card': '#252525',
            'text_primary': '#e0e0e0',
            'text_secondary': '#a0a0a0',
            'accent': '#007acc',
            'accent_hover': '#1a8cd8',
            'success': '#4ec9b0',
            'success_hover': '#3da590',
            'warning': '#ce9178',
            'error': '#f44336',
            'error_hover': '#d32f2f',
            'border': '#404040',
            'neutral_hover': '#4a4a4a'
        }

        # ------------------------------
        # Configure main window
        # ------------------------------
        self.window.configure(bg='#000000')

        # Variables
        self.stop_search = False
        self.case_sensitive = tk.BooleanVar(value=False)
        self.recursive = tk.BooleanVar(value=True)

        # Context variables for lines before/after
        self.lines_before = tk.IntVar(value=2)
        self.lines_after = tk.IntVar(value=2)

        # Configure modern styles
        self.setup_styles()

        # Main container
        main_container = tk.Frame(self.window, bg=self.colors['bg_dark'])
        main_container.pack(fill="both", expand=True, padx=(20, 20), pady=(0, 20))

        # Title label
        title_frame = tk.Frame(main_container, bg='#000000', height=60)
        title_frame.pack(fill="x", pady=(0, 0))
        title_frame.pack_propagate(False)
        tk.Label(
            title_frame,
            text="🔍 FILE TEXT SEARCH",
            font=("Segoe UI", 20, "bold"),
            bg='#000000',
            fg=self.colors['text_primary']
        ).pack(expand=True)

        # Input, buttons, results+status
        self.create_input_section(main_container)
        self.create_action_buttons(main_container)
        self.create_results_and_status(main_container)

        # ------------------------------
        # Safe close protocol
        # ------------------------------
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------
    # Modern ttk styles
    # ------------------------------
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Card.TFrame", background=self.colors['bg_card'], borderwidth=1, relief="flat")
        style.configure("Modern.TLabel", background=self.colors['bg_card'], foreground=self.colors['text_primary'], font=("Segoe UI", 10))
        style.configure("Modern.TEntry", fieldbackground=self.colors['bg_light'], foreground=self.colors['text_primary'], borderwidth=0, relief="flat")
        style.configure("Modern.TCheckbutton", background=self.colors['bg_card'], foreground=self.colors['text_secondary'], font=("Segoe UI", 9))
        style.map("Modern.TCheckbutton", background=[('active', self.colors['bg_card'])], foreground=[('active', self.colors['text_primary'])])
        style.configure("Dark.Vertical.TScrollbar", background='#1e1e1e', troughcolor='#0a0a0a', bordercolor='#1e1e1e', arrowcolor='#a0a0a0', relief="flat")
        style.map("Dark.Vertical.TScrollbar", background=[('active', '#2d2d2d'), ('pressed', '#3c3c3c')])

    # ------------------------------
    # Rounded button with custom hover color
    # ------------------------------
    def create_rounded_button(self, parent, text, command, bg_color, fg_color='#ffffff', hover_color=None, state='normal'):
        """Creates a modern rounded button with individual hover color"""
        btn = tk.Button(parent, text=text, command=command, bg=bg_color, fg=fg_color, font=("Segoe UI", 10, "bold"),
                        borderwidth=0, padx=20, pady=10, cursor="hand2",
                        activebackground=hover_color or self.colors['accent_hover'], activeforeground='#ffffff',
                        state=state, relief="flat")

        def on_enter(e):
            if btn['state'] != 'disabled':
                btn['background'] = hover_color or self.colors['accent_hover']

        def on_leave(e):
            if btn['state'] != 'disabled':
                btn['background'] = bg_color

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # ------------------------------
    # Center window on screen
    # ------------------------------
    def center_window(self, width=None, height=None):
        self.window.update_idletasks()
        if width is None:
            width = self.window.winfo_width()
        if height is None:
            height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    # ------------------------------
    # Input section
    # ------------------------------
    def create_input_section(self, parent):
        input_card = tk.Frame(parent, bg=self.colors['bg_card'], highlightthickness=1, highlightbackground=self.colors['border'])
        input_card.pack(fill="x", pady=(0, 15))
        input_inner = tk.Frame(input_card, bg=self.colors['bg_card'])
        input_inner.pack(fill="both", padx=20, pady=20)

        # Folder
        self.create_input_row(input_inner, "Folder", 0)
        self.folder_var = tk.StringVar(value=os.getcwd())
        folder_frame = tk.Frame(input_inner, bg=self.colors['bg_card'])
        folder_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=8)
        folder_frame.columnconfigure(0, weight=1)
        tk.Entry(folder_frame, textvariable=self.folder_var, bg=self.colors['bg_light'], fg=self.colors['text_primary'],
                 font=("Segoe UI", 10), borderwidth=0, insertbackground=self.colors['text_primary'],
                 relief="flat").grid(row=0, column=0, sticky="ew", ipady=8, ipadx=10)
        self.create_rounded_button(folder_frame, "Browse", self.select_folder,
                                   self.colors['bg_medium'], self.colors['text_primary'],
                                   hover_color=self.colors['neutral_hover']).grid(row=0, column=1, padx=(10, 0))

        # Search text
        self.create_input_row(input_inner, "Search text", 1)
        self.search_var = tk.StringVar()
        tk.Entry(input_inner, textvariable=self.search_var, bg=self.colors['bg_light'], fg=self.colors['text_primary'],
                 font=("Segoe UI", 10), borderwidth=0, insertbackground=self.colors['text_primary'],
                 relief="flat").grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=8, ipady=8, ipadx=10)

        # Extensions
        self.create_input_row(input_inner, "Extensions (e.g. .txt,.py,.pdf,.btl,.docx,.xlsx)", 2)
        self.extensions_var = tk.StringVar(value="*")
        tk.Entry(input_inner, textvariable=self.extensions_var, bg=self.colors['bg_light'], fg=self.colors['text_primary'],
                 font=("Segoe UI", 10), borderwidth=0, insertbackground=self.colors['text_primary'],
                 relief="flat").grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=8, ipady=8, ipadx=10)

        # Options
        options_frame = tk.Frame(input_inner, bg=self.colors['bg_card'])
        options_frame.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=(15, 0))
        tk.Checkbutton(options_frame, text="Case sensitive", variable=self.case_sensitive, bg=self.colors['bg_card'],
                       fg=self.colors['text_secondary'], selectcolor=self.colors['bg_light'],
                       activebackground=self.colors['bg_card'], activeforeground=self.colors['text_primary'],
                       font=("Segoe UI", 9), borderwidth=0, highlightthickness=0).pack(side="left", padx=(0, 20))
        tk.Checkbutton(options_frame, text="Recursive search", variable=self.recursive, bg=self.colors['bg_card'],
                       fg=self.colors['text_secondary'], selectcolor=self.colors['bg_light'],
                       activebackground=self.colors['bg_card'], activeforeground=self.colors['text_primary'],
                       font=("Segoe UI", 9), borderwidth=0, highlightthickness=0).pack(side="left")

        # Context settings for lines before/after
        context_frame = tk.Frame(input_inner, bg=self.colors['bg_card'])
        context_frame.grid(row=4, column=1, sticky="w", padx=(10, 0), pady=(15, 0))
        tk.Label(context_frame, text="Context:", bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary'], font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))
        tk.Label(context_frame, text="Lines before", bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary'], font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))
        tk.Entry(context_frame, textvariable=self.lines_before, width=4, bg=self.colors['bg_light'],
                 fg=self.colors['text_primary'], font=("Segoe UI", 9), borderwidth=0, relief="flat",
                 justify="center", insertbackground=self.colors['text_primary']).pack(side="left", padx=(0, 15))
        tk.Label(context_frame, text="Lines after", bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary'], font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))
        tk.Entry(context_frame, textvariable=self.lines_after, width=4, bg=self.colors['bg_light'],
                 fg=self.colors['text_primary'], font=("Segoe UI", 9), borderwidth=0, relief="flat",
                 justify="center", insertbackground=self.colors['text_primary']).pack(side="left")

        input_inner.columnconfigure(1, weight=1)

    # ------------------------------
    # Create input row label
    # ------------------------------
    def create_input_row(self, parent, label_text, row):
        label = tk.Label(parent, text=label_text, bg=self.colors['bg_card'], fg=self.colors['text_secondary'],
                         font=("Segoe UI", 10), anchor="w")
        label.grid(row=row, column=0, sticky="w", pady=8)

    # ------------------------------
    # Action buttons
    # ------------------------------
    def create_action_buttons(self, parent):
        button_frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        button_frame.pack(fill="x", pady=(0, 15))
        self.search_button = self.create_rounded_button(button_frame, "🔍 SEARCH", self.start_search,
                                                        self.colors['accent'], '#ffffff',
                                                        hover_color=self.colors['accent_hover'])
        self.search_button.pack(side="left", padx=(0, 10))
        self.stop_button = self.create_rounded_button(button_frame, "⏹ STOP", self.stop_search_action,
                                                      self.colors['error'], '#ffffff',
                                                      hover_color=self.colors['error_hover'], state='disabled')
        self.stop_button.pack(side="left", padx=(0, 10))
        clear_button = self.create_rounded_button(button_frame, "🗑 CLEAR", self.clear_results,
                                                  self.colors['bg_medium'], self.colors['text_primary'],
                                                  hover_color=self.colors['neutral_hover'])
        clear_button.pack(side="left", padx=(0, 10))
        save_button = self.create_rounded_button(button_frame, "💾 SAVE", self.save_results,
                                                 self.colors['success'], '#ffffff',
                                                 hover_color=self.colors['success_hover'])
        save_button.pack(side="left")

    # ------------------------------
    # Results + Status section
    # ------------------------------
    def create_results_and_status(self, parent):
        """Creates the results text area and status bar with correct layout"""

        container = tk.Frame(parent, bg=self.colors['bg_dark'])
        container.pack(fill="both", expand=True)

        # Status bar
        self.status_bar = tk.Frame(container, bg=self.colors['bg_light'], height=30)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.status_bar, textvariable=self.status_var, bg=self.colors['bg_light'],
                 fg=self.colors['text_primary'], font=("Segoe UI", 9), anchor="w").pack(side="left", padx=15, pady=5)

        # Results frame
        self.results_card = tk.Frame(container, bg=self.colors['bg_card'], highlightthickness=1,
                                     highlightbackground=self.colors['border'])
        self.results_card.pack(fill="both", expand=True, pady=(0, 0))

        results_header = tk.Frame(self.results_card, bg='#000000', height=50)
        results_header.pack(fill="x")
        results_header.pack_propagate(False)
        tk.Label(results_header, text="🔍 RESULTS", bg='#000000', fg=self.colors['text_primary'],
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=20, pady=15)

        results_inner = tk.Frame(self.results_card, bg=self.colors['bg_card'])
        results_inner.pack(fill="both", expand=True, padx=20, pady=(10, 10))

        self.results_text = tk.Text(results_inner, wrap=tk.NONE, bg=self.colors['bg_dark'], fg=self.colors['text_primary'],
                                    font=("Consolas", 10), insertbackground=self.colors['text_primary'], borderwidth=0,
                                    relief="flat", padx=10, pady=10)
        v_scrollbar = ttk.Scrollbar(results_inner, orient="vertical", command=self.results_text.yview,
                                    style="Dark.Vertical.TScrollbar")
        v_scrollbar.pack(side="right", fill="y")
        self.results_text.pack(side="left", fill="both", expand=True)
        self.results_text.configure(yscrollcommand=v_scrollbar.set)

        # Text tags
        self.results_text.tag_config("path", foreground=self.colors['accent'], font=("Consolas", 10, "bold"))
        self.results_text.tag_config("line", foreground=self.colors['success'])
        self.results_text.tag_config("content", foreground=self.colors['text_primary'])
        self.results_text.tag_config("summary", foreground=self.colors['text_secondary'], font=("Consolas", 10, "italic"))
        self.results_text.tag_config("highlight", foreground="#f44336", font=("Consolas", 10, "bold"))

    # ------------------------------
    # Highlight search word
    # ------------------------------
    def highlight_search_word(self, text_widget, word):
        if not word:
            return
        start_pos = "1.0"
        while True:
            start_pos = text_widget.search(word, start_pos, stopindex=tk.END, nocase=not self.case_sensitive.get())
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(word)}c"
            text_widget.tag_add("highlight", start_pos, end_pos)
            start_pos = end_pos

    # ------------------------------
    # Folder selection
    # ------------------------------
    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)

    # ------------------------------
    # Clear results
    # ------------------------------
    def clear_results(self):
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Results cleared")

    # ------------------------------
    # Stop search
    # ------------------------------
    def stop_search_action(self):
        self.stop_search = True
        self.status_var.set("Stopping...")

    # ------------------------------
    # Start search (threaded)
    # ------------------------------
    def start_search(self):
        self.search_thread = threading.Thread(target=self.search_files, daemon=True)
        self.search_thread.start()

        search_text = self.search_var.get()
        folder = self.folder_var.get()
        if not search_text:
            messagebox.showwarning("Warning", "Please enter a search text!")
            return
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "The specified folder does not exist!")
            return
        self.stop_search = False
        self.search_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.clear_results()
        threading.Thread(target=self.search_files, daemon=True).start()

    # ------------------------------
    # Search files via searcher()
    # ------------------------------
    def search_files(self):
        folder = self.folder_var.get()
        search_text = self.search_var.get()
        extensions = self.extensions_var.get().strip()
        case_sensitive = self.case_sensitive.get()
        recursive = self.recursive.get()
        lines_before = self.lines_before.get()
        lines_after = self.lines_after.get()

        self.window.after(0, lambda: self.status_var.set("⏳ Searching..."))

        stop_flag = {'stop': False}

        try:
            # Call searcher helper
            results, total_files, total_matches = searcher(
                folder=folder,
                search_text=search_text,
                extensions=extensions,
                case_sensitive=case_sensitive,
                recursive=recursive,
                lines_before=lines_before,
                lines_after=lines_after,
                stop_flag=stop_flag
            )

            files_with_matches = len(results)

            for file_path, matches in results:
                if self.stop_search:
                    stop_flag['stop'] = True
                    break
                self.window.after(0, lambda fp=file_path: self.results_text.insert(tk.END, f"\n📄 {fp}\n", "path"))
                for match in matches:
                    line_text = f"   Line {match[0]}:\n{match[1]}\n" if isinstance(match[0], int) else f"   Page {match[0]}:\n{match[1]}\n"
                    self.window.after(0, lambda lt=line_text: self.results_text.insert(tk.END, lt, "content"))
                    self.window.after(0, lambda: self.highlight_search_word(self.results_text, search_text))
                self.window.after(0, lambda: self.results_text.insert(tk.END, "\n", "content"))
                self.window.after(0, lambda: self.results_text.see(tk.END))

            if total_matches == 0:
                self.window.after(0, lambda: self.results_text.insert(tk.END, "\n⚠️ No results found.\n", "summary"))

        finally:
            self.window.after(0, lambda: self.status_var.set(
                f"✅ Done - {total_matches} matches in {files_with_matches}/{total_files} files"
            ))
            self.window.after(0, lambda: self.search_button.config(state="normal"))
            self.window.after(0, lambda: self.stop_button.config(state="disabled"))

    # ------------------------------
    # Save results to file
    # ------------------------------
    def save_results(self):
        content = self.results_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showinfo("Info", "No results to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Results saved to:\n{file_path}")

    # ------------------------------
    # Safe close
    # ------------------------------
    def on_close(self):
        self.stop_search = True
        if hasattr(self, 'search_thread') and self.search_thread.is_alive():
            self.search_thread.join()
        self.window.destroy()
        self.root.quit()


# ------------------------------
# Run the app
# ------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = GrepWithPowershell(root)
    root.mainloop()
