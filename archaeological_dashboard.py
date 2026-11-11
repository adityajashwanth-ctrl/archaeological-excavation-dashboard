"""
RELATIONAL ARCHAEOLOGICAL EXCAVATION & TRENCH ANALYSIS DASHBOARD
Student assignment solution

Requirements:
- Python 3.9+
- SQLite is included with Python.
- Desktop: Tkinter (included with most Python installations).
- Jupyter: ipywidgets is used when available.
- Google Colab: install ipywidgets if it is not already available.

Run:
    python archaeological_dashboard.py

Database:
    archaeological_excavation.db (created automatically in this folder)

The application stores:
1. excavation_projects: one row per excavation project
2. trenches: one or more trenches belonging to a project
3. artifact_analyses: one or more analyses belonging to a trench

Foreign keys are enabled on every database connection. ON DELETE CASCADE
removes dependent trenches and analyses when a project is deleted, and
removes analyses when a trench is deleted.
"""

import os
import sqlite3
from datetime import date
from pathlib import Path

DB_FILE = Path(__file__).with_name("archaeological_excavation.db")


# ---------------------------------------------------------------------------
# DATABASE LAYER
# ---------------------------------------------------------------------------

def connect_db():
    """Open a database connection and explicitly enable foreign keys."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create normalized tables and seed sample records only when empty."""
    with connect_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS excavation_projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL UNIQUE,
                contact_email TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS trenches (
                trench_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                trench_identifier TEXT NOT NULL,
                opening_date TEXT NOT NULL,
                FOREIGN KEY (project_id)
                    REFERENCES excavation_projects(project_id)
                    ON DELETE CASCADE,
                UNIQUE(project_id, trench_identifier)
            );

            CREATE TABLE IF NOT EXISTS artifact_analyses (
                analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trench_id INTEGER NOT NULL,
                analysis_type TEXT NOT NULL,
                measured_value REAL NOT NULL CHECK (measured_value >= 0),
                FOREIGN KEY (trench_id)
                    REFERENCES trenches(trench_id)
                    ON DELETE CASCADE
            );
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM excavation_projects"
        ).fetchone()[0]

        if count == 0:
            sample_projects = [
                ("Hampi Heritage Excavation", "hampi.director@example.org"),
                ("Amaravati Archaeological Survey", "amaravati.team@example.org"),
            ]
            conn.executemany("""
                INSERT INTO excavation_projects (project_name, contact_email)
                VALUES (?, ?)
            """, sample_projects)

            project_ids = {
                name: project_id
                for project_id, name in conn.execute(
                    "SELECT project_id, project_name FROM excavation_projects"
                )
            }

            conn.executemany("""
                INSERT INTO trenches
                    (project_id, trench_identifier, opening_date)
                VALUES (?, ?, ?)
            """, [
                (project_ids["Hampi Heritage Excavation"],
                 "Trench T-04 - North Quadrant", "2026-10-01"),
                (project_ids["Hampi Heritage Excavation"],
                 "Trench T-07 - Temple Area", "2026-10-05"),
                (project_ids["Amaravati Archaeological Survey"],
                 "Trench T-11 - Burial Layer", "2026-10-08"),
            ])

            trench_ids = {
                identifier: trench_id
                for trench_id, identifier in conn.execute(
                    "SELECT trench_id, trench_identifier FROM trenches"
                )
            }

            conn.executemany("""
                INSERT INTO artifact_analyses
                    (trench_id, analysis_type, measured_value)
                VALUES (?, ?, ?)
            """, [
                (trench_ids["Trench T-04 - North Quadrant"],
                 "Pottery fragment analysis", 12.5),
                (trench_ids["Trench T-04 - North Quadrant"],
                 "Carbon dating", 1450.0),
                (trench_ids["Trench T-07 - Temple Area"],
                 "Metal artifact analysis", 8.2),
                (trench_ids["Trench T-11 - Burial Layer"],
                 "Soil composition analysis", 3.7),
            ])


def add_record(project_name, contact_email, trench_identifier,
               opening_date, analysis_type, measured_value):
    """Create/reuse a project, then insert one trench and one analysis."""
    project_name = project_name.strip()
    contact_email = contact_email.strip()
    trench_identifier = trench_identifier.strip()
    opening_date = opening_date.strip()
    analysis_type = analysis_type.strip()

    if not all([project_name, contact_email, trench_identifier,
                opening_date, analysis_type]):
        raise ValueError("All text fields are required.")

    try:
        value = float(measured_value)
    except (TypeError, ValueError):
        raise ValueError("Measured value must be a valid number.")
    if value < 0:
        raise ValueError("Measured value cannot be negative.")

    # Validate the date format.
    try:
        date.fromisoformat(opening_date)
    except ValueError:
        raise ValueError("Opening date must use YYYY-MM-DD format.")

    with connect_db() as conn:
        row = conn.execute(
            "SELECT project_id FROM excavation_projects WHERE project_name = ?",
            (project_name,)
        ).fetchone()

        if row:
            project_id = row[0]
            # Keep the existing project profile; do not silently overwrite email.
        else:
            cursor = conn.execute("""
                INSERT INTO excavation_projects (project_name, contact_email)
                VALUES (?, ?)
            """, (project_name, contact_email))
            project_id = cursor.lastrowid

        cursor = conn.execute("""
            INSERT INTO trenches (project_id, trench_identifier, opening_date)
            VALUES (?, ?, ?)
        """, (project_id, trench_identifier, opening_date))
        trench_id = cursor.lastrowid

        conn.execute("""
            INSERT INTO artifact_analyses
                (trench_id, analysis_type, measured_value)
            VALUES (?, ?, ?)
        """, (trench_id, analysis_type, value))

    return "Record added successfully."


def get_table_data(table_name):
    """Return column names and rows for one approved table."""
    allowed = {
        "excavation_projects", "trenches", "artifact_analyses"
    }
    if table_name not in allowed:
        raise ValueError("Unknown table.")
    with connect_db() as conn:
        cursor = conn.execute(f"SELECT * FROM {table_name} ORDER BY 1")
        return [item[0] for item in cursor.description], cursor.fetchall()


def get_joined_data():
    """Return the master view joining all three related tables."""
    query = """
        SELECT
            t.trench_id AS "Trench ID",
            p.project_name AS "Project Name",
            t.trench_identifier AS "Trench Identifier",
            t.opening_date AS "Opening Date",
            a.analysis_type AS "Analysis Type",
            a.measured_value AS "Measured Value",
            a.analysis_id AS "Analysis ID"
        FROM trenches AS t
        INNER JOIN excavation_projects AS p
            ON p.project_id = t.project_id
        INNER JOIN artifact_analyses AS a
            ON a.trench_id = t.trench_id
        ORDER BY t.trench_id, a.analysis_id
    """
    with connect_db() as conn:
        cursor = conn.execute(query)
        return [item[0] for item in cursor.description], cursor.fetchall()


def get_delete_options(target):
    """Build current dropdown options directly from the database."""
    queries = {
        "Excavation Project": (
            "SELECT project_id, project_name FROM excavation_projects "
            "ORDER BY project_name"
        ),
        "Trench": (
            "SELECT trench_id, trench_identifier FROM trenches "
            "ORDER BY trench_id"
        ),
        "Artifact Analysis": (
            "SELECT analysis_id, analysis_type || ' (Analysis #' || "
            "analysis_id || ')' FROM artifact_analyses ORDER BY analysis_id"
        ),
    }
    if target not in queries:
        return []
    with connect_db() as conn:
        return conn.execute(queries[target]).fetchall()


def delete_record(target, record_id):
    """Delete the selected row. Foreign-key cascades handle child records."""
    table_and_key = {
        "Excavation Project": ("excavation_projects", "project_id"),
        "Trench": ("trenches", "trench_id"),
        "Artifact Analysis": ("artifact_analyses", "analysis_id"),
    }
    if target not in table_and_key:
        raise ValueError("Select a valid record type.")
    table, key = table_and_key[target]
    with connect_db() as conn:
        cursor = conn.execute(
            f"DELETE FROM {table} WHERE {key} = ?", (int(record_id),)
        )
        if cursor.rowcount == 0:
            raise ValueError("That record no longer exists. Refresh and try again.")
    return f"{target} deleted successfully."


# ---------------------------------------------------------------------------
# NOTEBOOK INTERFACE (JUPYTER / COLAB)
# ---------------------------------------------------------------------------

def run_notebook_app():
    try:
        import ipywidgets as widgets
        from IPython.display import display, HTML, clear_output
    except ImportError:
        return False

    title = widgets.HTML(
        "<h2>Archaeological Excavation Dashboard</h2>"
        "<p>Manage projects, trenches and artifact analyses in one place.</p>"
    )

    project = widgets.Text(description="Project:", placeholder="Project name")
    email = widgets.Text(description="Email:", placeholder="Site director email")
    trench = widgets.Text(description="Trench:", placeholder="Trench identifier")
    opening = widgets.Text(
        description="Date:", value=date.today().isoformat(),
        placeholder="YYYY-MM-DD"
    )
    analysis = widgets.Text(description="Analysis:", placeholder="Analysis type")
    measured = widgets.Text(description="Value:", placeholder="e.g. 12.5")
    add_button = widgets.Button(description="Add Record", button_style="success")
    add_message = widgets.Output()

    delete_type = widgets.Dropdown(
        options=["Excavation Project", "Trench", "Artifact Analysis"],
        description="Delete:"
    )
    delete_item = widgets.Dropdown(description="Record:")
    delete_button = widgets.Button(description="Delete Selected", button_style="danger")
    delete_message = widgets.Output()

    def refresh_delete_options(*_):
        options = get_delete_options(delete_type.value)
        delete_item.options = [(label, record_id) for record_id, label in options]
        if options:
            delete_item.value = options[0][0]
        else:
            delete_item.value = None

    delete_type.observe(refresh_delete_options, names="value")

    def add_clicked(_):
        with add_message:
            clear_output()
            try:
                message = add_record(
                    project.value, email.value, trench.value, opening.value,
                    analysis.value, measured.value
                )
                project.value = ""
                email.value = ""
                trench.value = ""
                opening.value = date.today().isoformat()
                analysis.value = ""
                measured.value = ""
                print(message)
                refresh_all()
            except Exception as exc:
                print(f"Error: {exc}")

    def delete_clicked(_):
        with delete_message:
            clear_output()
            try:
                if delete_item.value is None:
                    raise ValueError("There are no records of this type to delete.")
                print(delete_record(delete_type.value, delete_item.value))
                refresh_delete_options()
                refresh_all()
            except Exception as exc:
                print(f"Error: {exc}")

    add_button.on_click(add_clicked)
    delete_button.on_click(delete_clicked)

    outputs = [widgets.Output() for _ in range(4)]

    def show_table(output, data_function):
        with output:
            clear_output()
            headers, rows = data_function()
            if not rows:
                display(HTML("<i>No records found.</i>"))
                return
            # Escape data before rendering HTML.
            import html
            header_html = "".join(
                f"<th>{html.escape(str(h))}</th>" for h in headers
            )
            row_html = "".join(
                "<tr>" + "".join(
                    f"<td>{html.escape(str(v))}</td>" for v in row
                ) + "</tr>" for row in rows
            )
            display(HTML(
                "<div style='overflow-x:auto'><table border='1' "
                "cellpadding='6' style='border-collapse:collapse'>"
                f"<thead><tr>{header_html}</tr></thead>"
                f"<tbody>{row_html}</tbody></table></div>"
            ))

    def refresh_all():
        show_table(outputs[0], get_joined_data)
        show_table(outputs[1], lambda: get_table_data("excavation_projects"))
        show_table(outputs[2], lambda: get_table_data("trenches"))
        show_table(outputs[3], lambda: get_table_data("artifact_analyses"))
        refresh_delete_options()

    tabs = widgets.Tab(children=outputs)
    for index, name in enumerate([
        "Master Excavation JOIN", "Projects", "Trenches", "Artifact Analyses"
    ]):
        tabs.set_title(index, name)

    add_panel = widgets.VBox([
        widgets.HTML("<h3>Insert Panel</h3>"),
        project, email, trench, opening, analysis, measured, add_button, add_message
    ])
    delete_panel = widgets.VBox([
        widgets.HTML("<h3>Delete Panel</h3>"),
        delete_type, delete_item, delete_button, delete_message
    ])

    refresh_delete_options()
    refresh_all()
    display(title, widgets.HBox([add_panel, delete_panel]), tabs)
    return True


# ---------------------------------------------------------------------------
# DESKTOP INTERFACE (TKINTER)
# ---------------------------------------------------------------------------

def run_desktop_app():
    import tkinter as tk
    from tkinter import ttk, messagebox

    root = tk.Tk()
    root.title("Archaeological Excavation & Trench Analysis Dashboard")
    root.geometry("1180x760")
    root.minsize(900, 620)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    outer = ttk.Frame(root, padding=14)
    outer.pack(fill="both", expand=True)

    ttk.Label(
        outer, text="ARCHAEOLOGICAL EXCAVATION DASHBOARD",
        font=("Arial", 18, "bold")
    ).pack(anchor="w")
    ttk.Label(
        outer, text="Manage excavation projects, trenches and artifact analyses",
        font=("Arial", 10)
    ).pack(anchor="w", pady=(2, 12))

    panels = ttk.Frame(outer)
    panels.pack(fill="x", pady=(0, 12))
    insert_frame = ttk.LabelFrame(panels, text="Insert Panel", padding=10)
    insert_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
    delete_frame = ttk.LabelFrame(panels, text="Delete Panel", padding=10)
    delete_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))

    fields = [
        ("Project Name", "project"),
        ("Contact Email", "email"),
        ("Trench Identifier", "trench"),
        ("Opening Date (YYYY-MM-DD)", "opening"),
        ("Analysis Type", "analysis"),
        ("Measured Value", "measured"),
    ]
    entries = {}
    for row, (label, key) in enumerate(fields):
        ttk.Label(insert_frame, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=3
        )
        entry = ttk.Entry(insert_frame, width=34)
        entry.grid(row=row, column=1, sticky="ew", pady=3)
        entries[key] = entry
    entries["opening"].insert(0, date.today().isoformat())
    insert_frame.columnconfigure(1, weight=1)

    delete_kind = tk.StringVar(value="Excavation Project")
    delete_choice = tk.StringVar()
    ttk.Label(delete_frame, text="Record type").grid(
        row=0, column=0, sticky="w", pady=4
    )
    kind_box = ttk.Combobox(
        delete_frame, textvariable=delete_kind, state="readonly",
        values=["Excavation Project", "Trench", "Artifact Analysis"], width=28
    )
    kind_box.grid(row=0, column=1, sticky="ew", pady=4)
    ttk.Label(delete_frame, text="Select record").grid(
        row=1, column=0, sticky="w", pady=4
    )
    choice_box = ttk.Combobox(
        delete_frame, textvariable=delete_choice, state="readonly", width=38
    )
    choice_box.grid(row=1, column=1, sticky="ew", pady=4)
    delete_frame.columnconfigure(1, weight=1)

    status = tk.StringVar(value="Ready.")
    ttk.Label(outer, textvariable=status, foreground="#245b36").pack(
        anchor="w", pady=(0, 8)
    )

    notebook = ttk.Notebook(outer)
    notebook.pack(fill="both", expand=True)

    table_specs = [
        ("Master Excavation JOIN", get_joined_data),
        ("Projects", lambda: get_table_data("excavation_projects")),
        ("Trenches", lambda: get_table_data("trenches")),
        ("Artifact Analyses", lambda: get_table_data("artifact_analyses")),
    ]
    tree_views = []

    def make_tree_tab(tab_name):
        frame = ttk.Frame(notebook, padding=6)
        notebook.add(frame, text=tab_name)
        tree = ttk.Treeview(frame, show="headings")
        ybar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree_views.append(tree)

    for tab_name, _ in table_specs:
        make_tree_tab(tab_name)

    def refresh_tables():
        for tree, (_, data_function) in zip(tree_views, table_specs):
            headers, rows = data_function()
            tree.delete(*tree.get_children())
            tree["columns"] = headers
            for header in headers:
                tree.heading(header, text=header)
                tree.column(header, width=145, minwidth=90, stretch=True)
            for row in rows:
                tree.insert("", "end", values=row)
        refresh_delete_dropdown()

    current_options = []

    def refresh_delete_dropdown(*_):
        nonlocal current_options
        current_options = get_delete_options(delete_kind.get())
        choice_box["values"] = [
            f"{label} [ID: {record_id}]" for record_id, label in current_options
        ]
        delete_choice.set(choice_box["values"][0] if current_options else "")

    def add_clicked():
        try:
            add_record(
                entries["project"].get(), entries["email"].get(),
                entries["trench"].get(), entries["opening"].get(),
                entries["analysis"].get(), entries["measured"].get()
            )
            for key, entry in entries.items():
                entry.delete(0, tk.END)
            entries["opening"].insert(0, date.today().isoformat())
            status.set("Record added successfully.")
            refresh_tables()
            messagebox.showinfo("Success", "The trench and artifact analysis were added.")
        except sqlite3.IntegrityError as exc:
            messagebox.showerror(
                "Database rule", 
                "This trench identifier may already exist in the selected project, "
                "or a database integrity rule was violated.\n\n" + str(exc)
            )
        except Exception as exc:
            messagebox.showerror("Input error", str(exc))

    def delete_clicked():
        try:
            if not current_options or not delete_choice.get():
                raise ValueError("No record is available to delete.")
            index = choice_box.current()
            if index < 0 or index >= len(current_options):
                raise ValueError("Please select a valid record.")
            record_id = current_options[index][0]
            target = delete_kind.get()
            confirmed = messagebox.askyesno(
                "Confirm deletion",
                f"Delete this {target.lower()}?\n\n"
                "Dependent records may also be deleted by cascade rules."
            )
            if not confirmed:
                return
            delete_record(target, record_id)
            status.set(f"{target} deleted. Tables and dropdown refreshed.")
            refresh_tables()
            messagebox.showinfo("Success", f"{target} deleted successfully.")
        except Exception as exc:
            messagebox.showerror("Deletion error", str(exc))
            refresh_tables()

    ttk.Button(
        insert_frame, text="Add Record", command=add_clicked
    ).grid(row=len(fields), column=0, columnspan=2, sticky="ew", pady=(8, 0))
    ttk.Button(
        delete_frame, text="Delete Selected", command=delete_clicked
    ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    kind_box.bind("<<ComboboxSelected>>", refresh_delete_dropdown)
    refresh_tables()
    root.mainloop()


# ---------------------------------------------------------------------------
# STARTUP: choose an interface appropriate to the current environment
# ---------------------------------------------------------------------------

def main():
    initialize_database()

    # In notebooks, use the notebook-native interface when ipywidgets exists.
    try:
        from IPython import get_ipython
        shell = get_ipython()
        if shell is not None and shell.__class__.__name__ in (
            "ZMQInteractiveShell", "Shell"
        ):
            if run_notebook_app():
                return
    except Exception:
        # If notebook detection fails, continue to desktop mode.
        pass

    try:
        run_desktop_app()
    except Exception as exc:
        print("The database was initialized successfully.")
        print("A desktop window could not be opened in this environment.")
        print("If you are using Google Colab, run this file in a Jupyter "
              "environment with ipywidgets installed, or use a local Python IDE.")
        print("Technical details:", exc)


if __name__ == "__main__":
    main()