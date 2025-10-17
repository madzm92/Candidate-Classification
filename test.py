import sys
import os
import logging
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QListWidget, QDialog, QListWidgetItem, QHBoxLayout
)
from PyQt6.QtCore import Qt
from src.candidate_classification_project.nlp_script import process_nlp_responses

logging.basicConfig(
    level=logging.INFO,
    filename="nlp_app.log",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class FilterDialog(QDialog):
    """Dialog to select filter values for a column using multi-highlight selection"""
    def __init__(self, df, column_name):
        super().__init__()
        self.setWindowTitle(f"Filter: {column_name}")
        self.selected_values = []
        self.df = df
        self.column = column_name

        layout = QVBoxLayout()

        # List of unique values in column
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # allow multi-highlight
        unique_vals = sorted(df[column_name].dropna().unique())
        for val in unique_vals:
            item = QListWidgetItem(str(val))
            self.list_widget.addItem(item)
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
        # Collect all highlighted/selected values
        self.selected_values = [item.text() for item in self.list_widget.selectedItems()]
        super().accept()



class NLPApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NLP Processor with Filters")
        self.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout()

        self.label = QLabel("Drop a CSV or Excel file here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        layout.addWidget(self.output_box)

        # Pre-NLP filter
        self.pre_filter_btn = QPushButton("Select Column to Filter (Pre-NLP)")
        self.pre_filter_btn.setEnabled(False)
        self.pre_filter_btn.clicked.connect(lambda: self.select_column_to_filter(pre_nlp=True))
        layout.addWidget(self.pre_filter_btn)

        # Run NLP button
        self.run_nlp_btn = QPushButton("Run NLP")
        self.run_nlp_btn.setEnabled(False)
        self.run_nlp_btn.clicked.connect(self.run_nlp)
        layout.addWidget(self.run_nlp_btn)

        # Post-NLP filter
        self.post_filter_btn = QPushButton("Select Column to Filter (Post-NLP)")
        self.post_filter_btn.setEnabled(False)
        self.post_filter_btn.clicked.connect(lambda: self.select_column_to_filter(pre_nlp=False))
        layout.addWidget(self.post_filter_btn)

        # Export button
        self.export_btn = QPushButton("Export Final Data")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_final)
        layout.addWidget(self.export_btn)

        self.setLayout(layout)
        self.setAcceptDrops(True)

        # Data storage
        self.df_original = None
        self.df_filtered_pre = None
        self.df_nlp = None
        self.df_final = None
        self.pre_filters = {}
        self.post_filters = {}

    # Drag & drop
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
                    self.output_box.setText("Unsupported file type. Use CSV or Excel.")
                    return
                self.df_original = df
                self.df_filtered_pre = df.copy()
                self.output_box.setText(f"Loaded {len(df)} rows with {len(df.columns)} columns.")
                self.pre_filter_btn.setEnabled(True)
                self.run_nlp_btn.setEnabled(True)
            except Exception as e:
                self.output_box.setText(f"Error reading file:\n{e}")
                logging.error(f"Error reading file {file_path}: {e}")

    # Column selection for filtering
    def select_column_to_filter(self, pre_nlp=True):
        df = self.df_filtered_pre if pre_nlp else self.df_nlp
        if df is None:
            return
        col_dialog = QDialog(self)
        col_dialog.setWindowTitle("Select Column to Filter")
        layout = QVBoxLayout()
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
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
                self.filter_column_values(column_name, pre_nlp=pre_nlp)

    # Filtering by selected values
    def filter_column_values(self, column_name, pre_nlp=True):
        df = self.df_filtered_pre if pre_nlp else self.df_nlp
        dialog = FilterDialog(df, column_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_vals = dialog.selected_values
            if selected_vals:
                mask = df[column_name].isin(selected_vals)
                if pre_nlp:
                    self.df_filtered_pre = df[mask]
                    self.pre_filters[column_name] = selected_vals
                    self.output_box.append(f"Pre-NLP filtered {column_name}: {len(self.df_filtered_pre)} rows left")
                else:
                    self.df_nlp = df[mask]
                    self.post_filters[column_name] = selected_vals
                    self.output_box.append(f"Post-NLP filtered {column_name}: {len(self.df_nlp)} rows left")

    # Run NLP processing
    def run_nlp(self):
        if self.df_filtered_pre is None or len(self.df_filtered_pre) == 0:
            self.output_box.append("No data to process.")
            return
        temp_file = os.path.join(os.path.expanduser("~"), "Desktop", "temp_filtered.xlsx")
        self.df_filtered_pre.to_excel(temp_file, index=False)
        self.output_box.append("Running NLP processing...")
        self.df_nlp = process_nlp_responses(temp_file)
        self.output_box.append(f"NLP processing done: {len(self.df_nlp)} rows")
        self.post_filter_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

    # Export final filtered & NLP data
    def export_final(self):
        if self.df_nlp is None or len(self.df_nlp) == 0:
            self.output_box.append("No data to export.")
            return
        self.df_final = self.df_nlp
        output_file = os.path.join(os.path.expanduser("~"), "Desktop", "nlp_results.xlsx")
        self.df_final.to_excel(output_file, index=False)
        self.output_box.append(f"✅ Exported final data to {output_file}")

        # Open automatically
        import sys
        if sys.platform == "darwin":
            os.system(f"open '{output_file}'")
        elif sys.platform == "win32":
            os.startfile(output_file)
        else:
            os.system(f"xdg-open '{output_file}'")


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = NLPApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
