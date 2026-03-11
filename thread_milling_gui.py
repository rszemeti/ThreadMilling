import sys
import importlib
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

ThreadMilling = importlib.import_module("thread_milling").ThreadMilling


class ThreadMillingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.milling = ThreadMilling()
        self.generated_gcode = ""
        self.generated_operation_count = 0
        self.config_path = Path(__file__).with_name("thread_milling_gui_config.json")
        self._build_ui()
        self.load_settings()

    def _build_ui(self):
        self.setWindowTitle("Thread Milling GUI")
        self.resize(900, 680)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.hole_file_input = QLineEdit()
        browse_hole_button = QPushButton("Browse...")
        browse_hole_button.clicked.connect(self.browse_hole_file)
        hole_row = QHBoxLayout()
        hole_row.addWidget(self.hole_file_input)
        hole_row.addWidget(browse_hole_button)
        form.addRow("Hole file (optional)", hole_row)

        self.output_file_input = QLineEdit(str(Path.cwd() / "thread_output.ngc"))
        browse_out_button = QPushButton("Browse...")
        browse_out_button.clicked.connect(self.browse_output_file)
        out_row = QHBoxLayout()
        out_row.addWidget(self.output_file_input)
        out_row.addWidget(browse_out_button)
        form.addRow("Output file", out_row)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Internal", "External"])
        form.addRow("Thread type", self.type_combo)

        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["top_down", "bottom_up"])
        self.direction_combo.setCurrentText("top_down")
        form.addRow("Direction", self.direction_combo)

        self.hand_combo = QComboBox()
        self.hand_combo.addItems(["right", "left"])
        self.hand_combo.setCurrentText("right")
        form.addRow("Thread hand", self.hand_combo)

        self.depth_input = QLineEdit("10.0")
        form.addRow("Depth (mm, no-file mode)", self.depth_input)

        self.major_input = QLineEdit("37.5")
        form.addRow("Major diameter (mm)", self.major_input)

        self.pitch_input = QLineEdit("1.75")
        form.addRow("Pitch (mm)", self.pitch_input)

        self.cutter_input = QLineEdit("10.0")
        form.addRow("Cutter diameter (mm)", self.cutter_input)

        self.passes_input = QLineEdit("2")
        form.addRow("Passes", self.passes_input)

        generate_button = QPushButton("Generate Preview")
        generate_button.clicked.connect(self.generate_preview)

        save_button = QPushButton("Save G-code")
        save_button.clicked.connect(self.save_gcode)

        button_row = QHBoxLayout()
        button_row.addWidget(generate_button)
        button_row.addWidget(save_button)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addWidget(QLabel("G-code Preview"))
        layout.addWidget(self.preview)
        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log)

    def _collect_settings(self):
        return {
            "hole_file": self.hole_file_input.text(),
            "output_file": self.output_file_input.text(),
            "thread_type": self.type_combo.currentText(),
            "direction": self.direction_combo.currentText(),
            "thread_hand": self.hand_combo.currentText(),
            "depth": self.depth_input.text(),
            "major_diameter": self.major_input.text(),
            "pitch": self.pitch_input.text(),
            "cutter_diameter": self.cutter_input.text(),
            "passes": self.passes_input.text(),
            "window_width": self.width(),
            "window_height": self.height(),
        }

    def save_settings(self):
        try:
            self.config_path.write_text(
                json.dumps(self._collect_settings(), indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            self.log.append(f"⚠️ Could not save settings: {exc}")

    def load_settings(self):
        if not self.config_path.exists():
            return

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.log.append(f"⚠️ Could not load settings: {exc}")
            return

        self.hole_file_input.setText(data.get("hole_file", self.hole_file_input.text()))
        self.output_file_input.setText(data.get("output_file", self.output_file_input.text()))

        thread_type = data.get("thread_type", self.type_combo.currentText())
        if self.type_combo.findText(thread_type) >= 0:
            self.type_combo.setCurrentText(thread_type)

        direction = data.get("direction", self.direction_combo.currentText())
        if self.direction_combo.findText(direction) >= 0:
            self.direction_combo.setCurrentText(direction)

        thread_hand = data.get("thread_hand", self.hand_combo.currentText())
        if self.hand_combo.findText(thread_hand) >= 0:
            self.hand_combo.setCurrentText(thread_hand)

        self.depth_input.setText(data.get("depth", self.depth_input.text()))
        self.major_input.setText(data.get("major_diameter", self.major_input.text()))
        self.pitch_input.setText(data.get("pitch", self.pitch_input.text()))
        self.cutter_input.setText(data.get("cutter_diameter", self.cutter_input.text()))
        self.passes_input.setText(data.get("passes", self.passes_input.text()))

        width = data.get("window_width")
        height = data.get("window_height")
        if isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
            self.resize(width, height)

    def browse_hole_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select hole file")
        if file_path:
            self.hole_file_input.setText(file_path)

    def browse_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save G-code",
            self.output_file_input.text(),
            "G-code Files (*.ngc);;All Files (*.*)",
        )
        if file_path:
            if "." not in Path(file_path).name:
                file_path = f"{file_path}.ngc"
            self.output_file_input.setText(file_path)

    def _float(self, widget, name):
        try:
            return float(widget.text().strip())
        except ValueError as exc:
            raise ValueError(f"Invalid {name}") from exc

    def _int(self, widget, name):
        try:
            return int(widget.text().strip())
        except ValueError as exc:
            raise ValueError(f"Invalid {name}") from exc

    def _build_gcode(self):
        hole_file = self.hole_file_input.text().strip()
        operation_type = self.type_combo.currentText()
        direction = self.direction_combo.currentText()
        thread_hand = self.hand_combo.currentText()

        if hole_file:
            holes, params = self.milling.parse_hole_file(hole_file)
        else:
            holes = [{"x": 0.0, "y": 0.0, "z": 0.0, "depth": self._float(self.depth_input, "depth")}]
            params = {
                "major_diameter": self._float(self.major_input, "major diameter"),
                "pitch": self._float(self.pitch_input, "pitch"),
                "cutter_diameter": self._float(self.cutter_input, "cutter diameter"),
                "passes": self._int(self.passes_input, "passes"),
            }

        thread_data = self.milling.generate_metric_thread_data(params["pitch"], params["major_diameter"])
        operations = self.milling.build_operations(
            holes=holes,
            thread_data=thread_data,
            pitch=params["pitch"],
            cutter_diameter=params["cutter_diameter"],
            num_passes=params["passes"],
            operation_type=operation_type,
            direction=direction,
            thread_hand=thread_hand,
        )
        gcode = self.milling.generate_complete_gcode(operations)
        return gcode, len(operations)

    def generate_preview(self):
        try:
            self.generated_gcode, self.generated_operation_count = self._build_gcode()
            self.preview.setPlainText(self.generated_gcode)
            self.log.append(f"✅ Preview generated for {self.generated_operation_count} operation(s)")
            self.save_settings()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            self.log.append(f"❌ {exc}")

    def save_gcode(self):
        try:
            if not self.generated_gcode:
                self.generated_gcode, self.generated_operation_count = self._build_gcode()
                self.preview.setPlainText(self.generated_gcode)

            output_file = self.output_file_input.text().strip()
            if not output_file:
                raise ValueError("Output file is required")

            with open(output_file, "w", encoding="utf-8") as handle:
                handle.write(self.generated_gcode)

            self.log.append(f"✅ Wrote {self.generated_operation_count} operation(s) to: {output_file}")
            self.save_settings()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            self.log.append(f"❌ {exc}")

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = ThreadMillingWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
