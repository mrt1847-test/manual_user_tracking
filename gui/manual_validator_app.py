import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from utils.manual_validation_service import (
    ManualValidationInput,
    ManualValidationResult,
    ManualValidationService,
    pretty_json,
)


class ManualValidatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.service = ManualValidationService()
        self.current_result: Optional[ManualValidationResult] = None

        self.setWindowTitle("Tracking Manual Validator")
        self.resize(1600, 950)

        self._build_ui()
        self._load_initial_data()

    def _build_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        splitter.addWidget(left_widget)

        form_layout = QFormLayout()
        left_layout.addLayout(form_layout)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["pc", "app", "mweb"])
        self.platform_combo.setCurrentText("mweb")

        self.environment_combo = QComboBox()
        self.environment_combo.addItems(["dev", "stg", "prod"])

        self.area_combo = QComboBox()
        self.module_combo = QComboBox()
        self.nth_combo = QComboBox()
        self.event_combo = QComboBox()
        self.result_filter_combo = QComboBox()
        self.result_filter_combo.addItems(["all", "PASS", "FAIL"])

        self.goodscode_edit = QLineEdit()
        self.keyword_edit = QLineEdit()
        self.category_id_edit = QLineEdit()

        self.is_ad_combo = QComboBox()
        self.is_ad_combo.addItem("")
        self.is_ad_combo.addItems(["Y", "N"])

        self.origin_price_edit = QLineEdit()
        self.promotion_price_edit = QLineEdit()
        self.coupon_price_edit = QLineEdit()

        form_layout.addRow("플랫폼", self.platform_combo)
        form_layout.addRow("환경", self.environment_combo)
        form_layout.addRow("영역", self.area_combo)
        form_layout.addRow("모듈", self.module_combo)
        form_layout.addRow("nth", self.nth_combo)
        form_layout.addRow("이벤트", self.event_combo)
        form_layout.addRow("결과 필터", self.result_filter_combo)
        form_layout.addRow("상품번호", self.goodscode_edit)
        form_layout.addRow("검색어", self.keyword_edit)
        form_layout.addRow("카테고리 ID", self.category_id_edit)
        form_layout.addRow("광고 여부", self.is_ad_combo)
        form_layout.addRow("원가", self.origin_price_edit)
        form_layout.addRow("할인가", self.promotion_price_edit)
        form_layout.addRow("쿠폰적용가", self.coupon_price_edit)

        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("스키마 새로고침")
        self.validate_button = QPushButton("검증 실행")
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.validate_button)
        left_layout.addLayout(button_layout)

        payload_label = QLabel("Raw Payload")
        self.payload_input = QPlainTextEdit()
        self.payload_input.setPlaceholderText(
            "JSON 또는 key=value&key2=value2 또는 key=value, key2=value2 형태의 raw payload를 붙여넣으세요."
        )
        left_layout.addWidget(payload_label)
        left_layout.addWidget(self.payload_input, 1)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self.summary_label = QLabel("검증 전")
        self.schema_path_label = QLabel("")
        right_layout.addWidget(self.summary_label)
        right_layout.addWidget(self.schema_path_label)

        self.result_table = QTableWidget(0, 5)
        self.result_table.setHorizontalHeaderLabels(["field", "status", "expected", "actual", "message"])
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.result_table, 2)

        self.tab_widget = QTabWidget()
        self.schema_preview = self._create_readonly_text()
        self.parsed_payload_preview = self._create_readonly_text()
        self.decoded_params_preview = self._create_readonly_text()
        self.errors_preview = self._create_readonly_text()
        self.tab_widget.addTab(self.schema_preview, "스키마")
        self.tab_widget.addTab(self.parsed_payload_preview, "파싱된 Payload")
        self.tab_widget.addTab(self.decoded_params_preview, "Decoded Params")
        self.tab_widget.addTab(self.errors_preview, "오류")
        right_layout.addWidget(self.tab_widget, 1)

        self.area_combo.currentTextChanged.connect(self._on_area_changed)
        self.module_combo.currentTextChanged.connect(self._on_module_changed)
        self.nth_combo.currentTextChanged.connect(self._on_nth_changed)
        self.event_combo.currentTextChanged.connect(self._refresh_schema_preview)
        self.result_filter_combo.currentTextChanged.connect(self._apply_result_filter)
        self.refresh_button.clicked.connect(self._load_initial_data)
        self.validate_button.clicked.connect(self._run_validation)

    def _create_readonly_text(self) -> QPlainTextEdit:
        widget = QPlainTextEdit()
        widget.setReadOnly(True)
        return widget

    def _load_initial_data(self) -> None:
        self.environment_combo.setCurrentText(self.service.get_default_environment())

        self.area_combo.blockSignals(True)
        self.area_combo.clear()
        self.area_combo.addItems(self.service.list_areas())
        self.area_combo.blockSignals(False)

        self._on_area_changed()

    def _on_area_changed(self) -> None:
        area = self.area_combo.currentText()
        modules = self.service.list_modules(area) if area else []

        self.module_combo.blockSignals(True)
        self.module_combo.clear()
        self.module_combo.addItems(modules)
        self.module_combo.blockSignals(False)

        self._on_module_changed()

    def _on_module_changed(self) -> None:
        area = self.area_combo.currentText()
        module_title = self.module_combo.currentText()
        nth_values = self.service.list_nth_values(area, module_title) if area and module_title else []

        self.nth_combo.blockSignals(True)
        self.nth_combo.clear()
        self.nth_combo.addItem("기본", None)
        for nth in nth_values:
            self.nth_combo.addItem(nth, nth)
        self.nth_combo.blockSignals(False)

        self._on_nth_changed()

    def _on_nth_changed(self) -> None:
        area = self.area_combo.currentText()
        module_title = self.module_combo.currentText()
        nth = self.nth_combo.currentData()

        events = self.service.list_event_types(area, module_title, nth) if area and module_title else []
        self.event_combo.blockSignals(True)
        self.event_combo.clear()
        self.event_combo.addItems(events)
        self.event_combo.blockSignals(False)

        self._refresh_schema_preview()

    def _refresh_schema_preview(self) -> None:
        area = self.area_combo.currentText()
        module_title = self.module_combo.currentText()
        event_type = self.event_combo.currentText()
        nth = self.nth_combo.currentData()

        if not area or not module_title:
            self.schema_preview.setPlainText("")
            self.schema_path_label.setText("")
            return

        try:
            loaded = self.service.load_module_config_with_path(area, module_title, nth)
            preview = self.service.get_schema_preview(area, module_title, nth, event_type or None)
        except Exception as exc:
            self.schema_preview.setPlainText(str(exc))
            self.schema_path_label.setText("")
            return

        self.schema_path_label.setText(f"스키마 파일: {loaded['path']}")
        self.schema_preview.setPlainText(preview)

    def _build_request(self) -> ManualValidationInput:
        nth = self.nth_combo.currentData()
        return ManualValidationInput(
            platform=self.platform_combo.currentText(),
            environment=self.environment_combo.currentText(),
            area=self.area_combo.currentText(),
            module_title=self.module_combo.currentText(),
            nth=nth,
            event_type=self.event_combo.currentText(),
            goodscode=self.goodscode_edit.text(),
            keyword=self.keyword_edit.text(),
            category_id=self.category_id_edit.text(),
            is_ad=self.is_ad_combo.currentText(),
            origin_price=self.origin_price_edit.text(),
            promotion_price=self.promotion_price_edit.text(),
            coupon_price=self.coupon_price_edit.text(),
            payload_raw=self.payload_input.toPlainText(),
        )

    def _run_validation(self) -> None:
        try:
            result = self.service.validate(self._build_request())
        except Exception as exc:
            self.current_result = None
            self.result_table.setRowCount(0)
            self.summary_label.setText("검증 실패")
            self.errors_preview.setPlainText(str(exc))
            QMessageBox.critical(self, "검증 오류", str(exc))
            return

        self.current_result = result
        status_text = "PASS" if result.success else "FAIL"
        self.summary_label.setText(
            f"결과: {status_text} | 총 {result.summary['total']} | PASS {result.summary['passed']} | FAIL {result.summary['failed']}"
        )
        self.schema_path_label.setText(f"스키마 파일: {result.module_config_path}")
        self.schema_preview.setPlainText(result.schema_preview)
        self.parsed_payload_preview.setPlainText(pretty_json(result.parsed_payload))
        self.decoded_params_preview.setPlainText(pretty_json(result.decoded_params))
        self.errors_preview.setPlainText("\n".join(result.errors) if result.errors else "오류 없음")
        self._apply_result_filter()

    def _apply_result_filter(self) -> None:
        if not self.current_result:
            self.result_table.setRowCount(0)
            return

        selected_filter = self.result_filter_combo.currentText()
        rows = self.current_result.field_results
        if selected_filter != "all":
            rows = [row for row in rows if row.get("status") == selected_filter]

        self.result_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self._set_table_item(row_index, 0, row.get("field", ""))
            self._set_table_item(row_index, 1, row.get("status", ""))
            self._set_table_item(row_index, 2, pretty_json(row.get("expected")))
            self._set_table_item(row_index, 3, pretty_json(row.get("actual")))
            self._set_table_item(row_index, 4, row.get("message", ""))

    def _set_table_item(self, row: int, column: int, value: object) -> None:
        text = "" if value is None else str(value)
        item = QTableWidgetItem(text)
        if column == 1:
            status = text.upper()
            if status == "PASS":
                item.setBackground(QColor("#d8f5d0"))
            elif status == "FAIL":
                item.setBackground(QColor("#ffd8d8"))
        self.result_table.setItem(row, column, item)


def run() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = ManualValidatorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
