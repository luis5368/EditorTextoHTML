import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from bs4 import BeautifulSoup
import re

class HTMLEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("HTML Editor")

        # Frame para el área de texto y los números de línea
        self.text_frame = tk.Frame(root)
        self.text_frame.pack(fill=tk.BOTH, expand=1)

        # Crear el área de texto para los números de línea
        self.line_numbers = tk.Text(self.text_frame, width=4, padx=3, takefocus=0, border=0, background='lightgrey', state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Crear el área de texto con scroll
        self.text_area = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD, undo=True)
        self.text_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        # Sincronizar scrolls
        self.text_area.bind("<KeyRelease>", self.on_text_change)
        self.text_area.bind("<MouseWheel>", self.on_text_change)
        self.text_area.bind("<Button-1>", self.on_text_change)
        self.text_area.bind("<Return>", self.on_text_change)
        self.text_area.bind("<BackSpace>", self.on_text_change)

        # Crear el menú
        self.create_menu()

        # Inicializar la variable del archivo actual
        self.file_path = None

        # Configurar resaltado de sintaxis
        self.setup_tags()
        self.text_area.bind("<KeyRelease>", self.highlight_syntax)

        # Crear la ventana del DOM Viewer
        self.dom_view = tk.Toplevel(root)
        self.dom_view.title("DOM Viewer")
        self.dom_text = tk.Text(self.dom_view, wrap=tk.WORD)
        self.dom_text.pack(fill=tk.BOTH, expand=1)
        self.text_area.bind("<KeyRelease>", self.update_dom_view)

    def create_menu(self):
        menu_bar = tk.Menu(self.root)

        # Menú de archivo
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Nuevo", command=self.new_file)
        file_menu.add_command(label="Abrir", command=self.open_file)
        file_menu.add_command(label="Guardar", command=self.save_file)
        file_menu.add_command(label="Guardar como", command=self.save_file_as)
        file_menu.add_command(label="Imprimir", command=self.print_file)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)

        # Menú de edición
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Deshacer", command=self.text_area.edit_undo)
        edit_menu.add_command(label="Rehacer", command=self.text_area.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Buscar", command=self.find_text)
        edit_menu.add_command(label="Reemplazar", command=self.replace_text)
        edit_menu.add_command(label="Ir a", command=self.goto_line)
        menu_bar.add_cascade(label="Edición", menu=edit_menu)

        self.root.config(menu=menu_bar)

    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.file_path = None

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r") as file:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, file.read())
            self.file_path = file_path
        self.on_text_change()

    def save_file(self):
        if self.file_path:
            with open(self.file_path, "w") as file:
                file.write(self.text_area.get(1.0, tk.END))
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")])
        if file_path:
            self.file_path = file_path
            self.save_file()

    def print_file(self):
        messagebox.showinfo("Imprimir", "Función de impresión no implementada")

    def find_text(self):
        self.search_toplevel = tk.Toplevel(self.root)
        self.search_toplevel.title("Buscar")
        self.search_toplevel.geometry("300x50")

        tk.Label(self.search_toplevel, text="Buscar:").pack(side=tk.LEFT, padx=10)
        self.search_entry = tk.Entry(self.search_toplevel, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=10)
        tk.Button(self.search_toplevel, text="Buscar", command=self.search).pack(side=tk.LEFT, padx=10)

    def search(self):
        self.text_area.tag_remove("search", "1.0", tk.END)
        search_text = self.search_entry.get()
        if search_text:
            start_pos = "1.0"
            while True:
                start_pos = self.text_area.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.text_area.tag_add("search", start_pos, end_pos)
                self.text_area.tag_config("search", background="yellow")
                start_pos = end_pos

    def replace_text(self):
        self.replace_toplevel = tk.Toplevel(self.root)
        self.replace_toplevel.title("Reemplazar")
        self.replace_toplevel.geometry("400x100")

        tk.Label(self.replace_toplevel, text="Buscar:").grid(row=0, column=0, padx=10, pady=10)
        self.replace_search_entry = tk.Entry(self.replace_toplevel, width=20)
        self.replace_search_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.replace_toplevel, text="Reemplazar con:").grid(row=1, column=0, padx=10, pady=10)
        self.replace_entry = tk.Entry(self.replace_toplevel, width=20)
        self.replace_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Button(self.replace_toplevel, text="Reemplazar", command=self.replace).grid(row=2, column=0, columnspan=2, pady=10)

    def replace(self):
        search_text = self.replace_search_entry.get()
        replace_text = self.replace_entry.get()
        content = self.text_area.get(1.0, tk.END)
        new_content = content.replace(search_text, replace_text)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, new_content)
        self.on_text_change()

    def goto_line(self):
        self.goto_toplevel = tk.Toplevel(self.root)
        self.goto_toplevel.title("Ir a línea")
        self.goto_toplevel.geometry("200x50")

        tk.Label(self.goto_toplevel, text="Línea:").pack(side=tk.LEFT, padx=10)
        self.goto_entry = tk.Entry(self.goto_toplevel, width=10)
        self.goto_entry.pack(side=tk.LEFT, padx=10)
        tk.Button(self.goto_toplevel, text="Ir", command=self.goto).pack(side=tk.LEFT, padx=10)

    def goto(self):
        line_number = self.goto_entry.get()
        self.text_area.mark_set("insert", f"{line_number}.0")
        self.text_area.see("insert")

    def setup_tags(self):
        self.keywords = [
            "<!DOCTYPE>", "<a>", "<abbr>", "<acronym>", "<address>", "<applet>", "<area>", "<article>", "<aside>", "<audio>", 
            "<b>", "<base>", "<basefont>", "<bdi>", "<bdo>", "<big>", "<blockquote>", "<body>", "<br>", "<button>", "<canvas>", 
            "<caption>", "<center>", "<cite>", "<code>", "<col>", "<colgroup>", "<data>", "<datalist>", "<dd>", "<del>", 
            "<details>", "<dfn>", "<dialog>", "<dir>", "<div>", "<dl>", "<dt>", "<em>", "<embed>", "<fieldset>", "<figcaption>", 
            "<figure>", "<font>", "<footer>", "<form>", "<frame>", "<frameset>", "<h1>", "<h2>", "<h3>", "<h4>", "<h5>", "<h6>", 
            "<head>", "<header>", "<hr>", "<html>", "<i>", "<iframe>", "<img>", "<input>", "<ins>", "<kbd>", "<label>", 
            "<legend>", "<li>", "<link>", "<main>", "<map>", "<mark>", "<meta>", "<meter>", "<nav>", "<noframes>", "<noscript>", 
            "<object>", "<ol>", "<optgroup>", "<option>", "<output>", "<p>", "<param>", "<picture>", "<pre>", "<progress>", "<q>", 
            "<rp>", "<rt>", "<ruby>", "<s>", "<samp>", "<script>", "<section>", "<select>", "<small>", "<source>", "<span>", 
            "<strike>", "<strong>", "<style>", "<sub>", "<summary>", "<sup>", "<svg>", "<table>", "<tbody>", "<td>", "<template>", 
            "<textarea>", "<tfoot>", "<th>", "<thead>", "<time>", "<title>", "<tr>", "<track>", "<tt>", "<u>", "<ul>", "<var>", 
            "<video>", "<wbr>"
        ]

        for keyword in self.keywords:
            self.text_area.tag_configure(keyword, foreground="red")

    def highlight_syntax(self, event=None):
        for tag in self.text_area.tag_names():
            self.text_area.tag_remove(tag, "1.0", tk.END)

        pattern = "|".join(re.escape(word) for word in self.keywords)
        regex = re.compile(pattern)

        pos = "1.0"
        while True:
            match = regex.search(self.text_area.get(pos, tk.END))
            if not match:
                break
            start, end = match.span()
            start_pos = f"{pos}+{start}c"
            end_pos = f"{pos}+{end}c"
            self.text_area.tag_add(match.group(), start_pos, end_pos)
            pos = end_pos

    def update_dom_view(self, event=None):
        html_content = self.text_area.get(1.0, tk.END)
        soup = BeautifulSoup(html_content, "html.parser")
        formatted_dom = soup.prettify()
        self.dom_text.delete(1.0, tk.END)
        self.dom_text.insert(tk.END, formatted_dom)

    def check_html_validity(self, event=None):
        html_content = self.text_area.get(1.0, tk.END)
        soup = BeautifulSoup(html_content, "html.parser")
        error_message = ""

        for tag in soup.find_all():
            if tag.find_next(string=re.compile(r"</" + tag.name + r">")) is None:
                error_message += f"Etiqueta <{tag.name}> no cerrada correctamente.\n"

        if error_message:
            messagebox.showwarning("Errores de HTML", error_message)
        else:
            messagebox.showinfo("HTML Válido", "Todas las etiquetas están correctamente cerradas.")

    def on_text_change(self, event=None):
        self.update_line_numbers()
        self.highlight_syntax()

    def update_line_numbers(self):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)

        current_lines = int(self.text_area.index('end-1c').split('.')[0])
        line_number_string = "\n".join(str(i) for i in range(1, current_lines))

        self.line_numbers.insert(1.0, line_number_string)
        self.line_numbers.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    editor = HTMLEditor(root)
    root.mainloop()
