
LIGHT_THEME = """
QWidget {
    background-color: #f0f0f0;
    color: #000000;
    font-family: "Segoe UI", sans-serif;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 4px;
}
QTableView {
    background-color: #ffffff;
    gridline-color: #cccccc;
    selection-background-color: #3d8ec9;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #e0e0e0;
    padding: 4px;
    border: 1px solid #cccccc;
}
QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #999999;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #d0d0d0;
}
QLabel#TitleLabel {
    color: #333333;
}
"""

DARK_THEME = """
QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: "Segoe UI", sans-serif;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit {
    background-color: #3c3f41;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px;
}
QTableView {
    background-color: #3c3f41;
    color: #ffffff;
    gridline-color: #555555;
    selection-background-color: #3d8ec9;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #454545;
    color: #ffffff;
    padding: 4px;
    border: 1px solid #555555;
}
QPushButton {
    background-color: #454545;
    color: #ffffff;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #505050;
}
QLabel#TitleLabel {
    color: #ffffff;
}
QMessageBox {
    background-color: #2b2b2b; 
}
QMessageBox QLabel {
    color: #ffffff;
}
"""