import sys
import os
import logging
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QListWidget, QDialog, QListWidgetItem,
    QHBoxLayout, QLineEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from src.candidate_classification_project.nlp_script import process_nlp_responses

logging.basicConfig(
    level=logging.INFO,
    filename="nlp_app.log",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Dialog for selecting filter values after NLP ---
class FilterDialog(QDialog):
    def __init__(self, df, column_name):
        super().__init__()
        self.setWindowTitle(f"Filter: {column_name}")
        self.selected_values = []

        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        unique_vals = sorted(df[column_name].dropna().unique())
        for val in unique_vals:
            self.list_widget.addItem(QListWidgetItem(str(val)))
        layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def accept(self):
        self.selected_values = [item.text() for item in self.list_widget.selectedItems()]
        super().accept()


# --- Dialog for choosing default or custom NLP categories ---
class NLPConfigDialog(QDialog):
    DEFAULT_CATEGORIES = {
        "EA_KEYWORDS": ["80,000 hours", "80k", "gwwc", "giving what we can", "10% pledge"],
        "X_SENSITIVE": ["ai x-risk", "agi safety", "existential risk"],
        "SOCIAL_TERMS": ["justice", "equity", "inequality", "marginalized", "oppression", "social concern"],
        "MGMT_TERMS": ["manage", "supervise", "lead", "led", "managed", "oversaw", "directed", "organized", "coordinated"]
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configure NLP Categories")
        self.resize(500, 500)
        self.use_default = True
        self.custom_categories = {}

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Choose NLP configuration:"))

        # Option buttons
        self.radio_default = QRadioButton("Use default NLP categories")
        self.radio_custom = QRadioButton("Define new NLP categories")
        self.radio_default.setChecked(True)

        self.group = QButtonGroup()
        self.group.addButton(self.radio_default)
        self.group.addButton(self.radio_custom)
        layout.addWidget(self.radio_default)
        layout.addWidget(self.radio_custom)

        # Show default categories
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.refresh_output()
        layout.addWidget(QLabel("\nDefault NLP categories:"))
        layout.addWidget(self.output_box)

        # Add custom category button
        self.add_cat_btn = QPushButton("Add Custom NLP Categories")
        self.add_cat_btn.setEnabled(False)
        self.add_cat_btn.clicked.connect(self.open_category_editor)
        layout.addWidget(self.add_cat_btn)
        self.radio_custom.toggled.connect(
            lambda checked: self.add_cat_btn.setEnabled(checked)
        )

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def refresh_output(self):
        self.output_box.clear()
        for cat, words in self.DEFAULT_CATEGORIES.items():
            self.output_box.append(f"📂 {cat}: {', '.join(words)}")

    def open_category_editor(self):
        editor = CategoryEditorDialog(self.custom_categories)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self.custom_categories = editor.categories
            # Refresh output box to show new custom categories
            self.output_box.clear()
            for cat, words in self.custom_categories.items():
                self.output_box.append(f"📂 {cat}: {', '.join(words)}")

    def accept(self):
        self.use_default = self.radio_default.isChecked()
        if not self.use_default and self.custom_categories:
            # Replace default categories with custom ones
            self.DEFAULT_CATEGORIES = self.custom_categories
        super().accept()





# --- Dialog for defining custom NLP categories ---
class CategoryEditorDialog(QDialog):
    def __init__(self, existing_categories=None):
        super().__init__()
        self.setWindowTitle("Add Custom NLP Categories")
        self.resize(500, 500)
        self.categories = existing_categories if existing_categories else {}

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Add category title:"))
        self.cat_input = QLineEdit()
        self.layout.addWidget(self.cat_input)

        self.add_cat_btn = QPushButton("Add Category")
        self.add_cat_btn.clicked.connect(self.add_category)
        self.layout.addWidget(self.add_cat_btn)

        self.layout.addWidget(QLabel("Add keywords (comma separated):"))
        self.keyword_input = QLineEdit()
        self.layout.addWidget(self.keyword_input)

        self.add_kw_btn = QPushButton("Add Keywords")
        self.add_kw_btn.clicked.connect(self.add_keywords)
        self.layout.addWidget(self.add_kw_btn)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.layout.addWidget(self.output_box)

        # Navigation
        btn_layout = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.reject)
        done_btn = QPushButton("Done")
        done_btn.clicked.connect(self.accept)
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(done_btn)
        self.layout.addLayout(btn_layout)

        self.setLayout(self.layout)
        self.refresh_output()

    def add_category(self):
        cat = self.cat_input.text().strip()
        if cat:
            self.categories[cat] = []
            self.cat_input.clear()
            self.refresh_output()

    def add_keywords(self):
        text = self.keyword_input.text().strip()
        if not text:
            return
        if not self.categories:
            self.output_box.append("⚠️ Please add a category first.")
            return
        latest_cat = list(self.categories.keys())[-1]
        words = [w.strip() for w in text.split(",") if w.strip()]
        self.categories[latest_cat].extend(words)
        self.keyword_input.clear()
        self.refresh_output()

    def refresh_output(self):
        self.output_box.clear()
        for cat, words in self.categories.items():
            self.output_box.append(f"📂 {cat}: {', '.join(words)}")


# --- Main App ---
class NLPApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NLP Processor")
        self.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout()

        self.label = QLabel("Drop a CSV or Excel file here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        layout.addWidget(self.output_box)

        # Configure NLP
        self.config_btn = QPushButton("Configure NLP")
        self.config_btn.setEnabled(False)
        self.config_btn.clicked.connect(self.configure_nlp)
        layout.addWidget(self.config_btn)

        # Run NLP
        self.run_nlp_btn = QPushButton("Run NLP")
        self.run_nlp_btn.setEnabled(False)
        self.run_nlp_btn.clicked.connect(self.run_nlp)
        layout.addWidget(self.run_nlp_btn)

        # Post-NLP filters
        self.post_filter_btn = QPushButton("Filter Columns (Post-NLP)")
        self.post_filter_btn.setEnabled(False)
        self.post_filter_btn.clicked.connect(self.select_column_to_filter)
        layout.addWidget(self.post_filter_btn)

        # Export
        self.export_btn = QPushButton("Export Final Data")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_final)
        layout.addWidget(self.export_btn)

        self.setLayout(layout)
        self.setAcceptDrops(True)

        # Data
        self.df_original = None
        self.df_nlp = None
        self.selected_columns = []
        self.custom_categories = {}
        self.use_default = True

        # Data storage
        self.df_original = None
        self.df_nlp = None
        self.df_final = None

        # Filters storage
        self.post_filters = {}

    # --- Drag & Drop ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.label.setText(f"File selected: {file_path}")
            try:
                if file_path.endswith(".csv"):
                    df = pd.read_csv(file_path)
                elif file_path.endswith((".xls", ".xlsx")):
                    df = pd.read_excel(file_path)
                else:
                    self.output_box.setText("Unsupported file type.")
                    return
                self.df_original = df
                self.output_box.setText(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns.")
                self.config_btn.setEnabled(True)
            except Exception as e:
                self.output_box.setText(f"Error loading file:\n{e}")
                logging.error(e)

    # --- NLP Configuration ---
    def configure_nlp(self):
        dialog = NLPConfigDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.use_default:
                self.nlp_categories = dialog.DEFAULT_CATEGORIES
            else:
                self.nlp_categories = dialog.custom_categories

            self.output_box.append("✅ NLP categories configured.")

            # Enable Run NLP button now that categories are set
            if self.df_original is not None and len(self.df_original) > 0:
                self.run_nlp_btn.setEnabled(True)

    # --- Run NLP ---
    def run_nlp(self):
        if self.df_original is None or len(self.df_original) == 0:
            self.output_box.append("No data to process.")
            return

        self.output_box.append("Running NLP processing...")

        # Save the original DataFrame to a temp file (all rows, no pre-NLP filtering)
        temp_file = os.path.join(os.path.expanduser("~"), "Desktop", "temp_filtered.xlsx")
        self.df_original.to_excel(temp_file, index=False)

        # Run NLP on the full dataset
        self.df_nlp = process_nlp_responses(
            file_name=temp_file,
            categories=self.nlp_categories
        )

        self.output_box.append(f"NLP processing done: {len(self.df_nlp)} rows")
        self.post_filter_btn.setEnabled(True)
        self.export_btn.setEnabled(True)


    # --- Post-NLP Filters ---
    def select_column_to_filter(self):
        df = self.df_nlp
        if df is None:
            return
        col_dialog = QDialog(self)
        col_dialog.setWindowTitle("Select Column to Filter")
        layout = QVBoxLayout()
        list_widget = QListWidget()
        for col in df.columns:
            list_widget.addItem(col)
        layout.addWidget(list_widget)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(col_dialog.accept)
        layout.addWidget(ok_btn)
        col_dialog.setLayout(layout)
        if col_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = list_widget.selectedItems()
            if selected_items:
                column_name = selected_items[0].text()
                self.filter_column_values(column_name)

    def filter_column_values(self, column_name, pre_nlp=False):
        df = self.df_nlp  # pre-NLP is no longer used
        dialog = FilterDialog(df, column_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_vals = dialog.selected_values

            # Convert "True"/"False" strings to boolean if column is boolean
            if df[column_name].dtype == bool:
                selected_vals = [val == "True" for val in selected_vals]

            if selected_vals:
                mask = df[column_name].isin(selected_vals)
                self.df_nlp = df[mask]
                self.post_filters[column_name] = selected_vals
                self.output_box.append(f"Post-NLP filtered {column_name}: {len(self.df_nlp)} rows left")


    # --- Export ---
    def export_final(self):
        if self.df_nlp is None or len(self.df_nlp) == 0:
            self.output_box.append("⚠️ No data to export.")
            return
        output_file = os.path.join(os.path.expanduser("~"), "Desktop", "nlp_results.xlsx")
        self.df_nlp.to_excel(output_file, index=False)
        self.output_box.append(f"✅ Exported to {output_file}")
        if sys.platform == "darwin":
            os.system(f"open '{output_file}'")
        elif sys.platform == "win32":
            os.startfile(output_file)
        else:
            os.system(f"xdg-open '{output_file}'")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NLPApp()
    window.show()
    sys.exit(app.exec())
