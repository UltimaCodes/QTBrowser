import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QTabBar, QPushButton, QLineEdit,
    QVBoxLayout, QDialog, QListWidget, QMessageBox, QToolBar
)
from PyQt5.QtGui import QIcon, QColor, QPainter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt


# Database setup
def setup_database():
    conn = sqlite3.connect('browser_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                      id INTEGER PRIMARY KEY,
                      url TEXT, title TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookmarks (
                      id INTEGER PRIMARY KEY, url TEXT, title TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS customization (
                      id INTEGER PRIMARY KEY, bg_color TEXT, text_color TEXT)''')
    conn.commit()
    conn.close()


class Browser(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.loadFinished.connect(self.update_title)

    def update_title(self, ok):
        if ok:
            title = self.page().title()
            if self.parent_window:
                self.parent_window.update_url_bar(self.url(), title)


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle("PyQt Browser")
        self.setGeometry(50, 50, 1200, 800)

        # Create the toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        # Add buttons to the toolbar
        self.add_toolbar_buttons()

        # Create tab widget to support multiple tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)  # Handle closable logic manually
        self.tabs.currentChanged.connect(self.switch_tab)

        # Set custom tab bar with hover-close functionality
        self.tabs.setTabBar(self.CustomTabBar(self))

        self.setCentralWidget(self.tabs)

        # Load customization settings
        self.load_customization()

        # Open the first tab with the home page
        self.new_tab("https://www.google.com")

    def add_toolbar_buttons(self):
        # Back button
        back_btn = QPushButton("Back", self)
        back_btn.setIcon(QIcon("icons/back.png"))
        back_btn.clicked.connect(self.go_back)
        self.toolbar.addWidget(back_btn)

        # Forward button
        forward_btn = QPushButton("Forward", self)
        forward_btn.setIcon(QIcon("icons/forward.png"))
        forward_btn.clicked.connect(self.go_forward)
        self.toolbar.addWidget(forward_btn)

        # Reload button
        reload_btn = QPushButton("Reload", self)
        reload_btn.setIcon(QIcon("icons/reload.png"))
        reload_btn.clicked.connect(self.reload_page)
        self.toolbar.addWidget(reload_btn)

        # Home button
        home_btn = QPushButton("Home", self)
        home_btn.setIcon(QIcon("icons/home.png"))
        home_btn.clicked.connect(self.go_home)
        self.toolbar.addWidget(home_btn)

        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.url_bar)

        # Bookmark button
        bookmark_btn = QPushButton("Bookmark", self)
        bookmark_btn.setIcon(QIcon("icons/bookmark.png"))
        bookmark_btn.clicked.connect(self.add_bookmark)
        self.toolbar.addWidget(bookmark_btn)

        # New Tab button
        new_tab_btn = QPushButton("New Tab", self)
        new_tab_btn.setIcon(QIcon("icons/new_tab.png"))
        new_tab_btn.clicked.connect(self.new_tab)
        self.toolbar.addWidget(new_tab_btn)

        # Customize button
        customize_btn = QPushButton("Customize", self)
        customize_btn.setIcon(QIcon("icons/settings.png"))
        customize_btn.clicked.connect(self.open_customize_menu)
        self.toolbar.addWidget(customize_btn)

        # History button
        history_btn = QPushButton("History", self)
        history_btn.setIcon(QIcon("icons/history.png"))
        history_btn.clicked.connect(self.show_history)
        self.toolbar.addWidget(history_btn)

        # Bookmarks button
        bookmarks_btn = QPushButton("Bookmarks", self)
        bookmarks_btn.setIcon(QIcon("icons/bookmark.png"))
        bookmarks_btn.clicked.connect(self.show_bookmarks)
        self.toolbar.addWidget(bookmarks_btn)

    def new_tab(self, url="https://www.google.com"):
        """Opens a new tab with the specified URL and saves to history."""
        browser = Browser(self)
        browser.setUrl(QUrl(url))
        i = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(i)
        self.save_history(url, "New Tab")

    def navigate_to_url(self):
        """Navigates to the URL in the URL bar and saves to history."""
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "http://" + url
        self.tabs.currentWidget().setUrl(QUrl(url))
        self.save_history(url, self.tabs.currentWidget().page().title())

    def update_url_bar(self, url, title):
        """Updates the URL bar and tab title."""
        self.url_bar.setText(url.toString())
        current_index = self.tabs.currentIndex()
        self.tabs.setTabText(current_index, title)

    def go_back(self):
        """Goes back in the web view."""
        self.tabs.currentWidget().back()

    def go_forward(self):
        """Goes forward in the web view."""
        self.tabs.currentWidget().forward()

    def reload_page(self):
        """Reloads the current page."""
        self.tabs.currentWidget().reload()

    def go_home(self):
        """Navigates to the home page in the current tab."""
        self.tabs.currentWidget().setUrl(QUrl("https://www.google.com"))

    def switch_tab(self, index):
        """Switches to the selected tab and updates the URL bar."""
        if index >= 0:
            url = self.tabs.widget(index).url().toString()
            self.url_bar.setText(url)

    def close_tab(self, index):
        """Closes the selected tab. Ensures at least one tab remains open."""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def add_bookmark(self):
        """Adds the current page to bookmarks."""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            url = current_browser.url().toString()
            title = current_browser.page().title()

            conn = sqlite3.connect('browser_data.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO bookmarks (url, title) VALUES (?, ?)', (url, title))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Bookmark Added", f"'{title}' has been bookmarked.")

    def show_history(self):
        """Displays the browsing history in a dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("History")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout()
        history_list = QListWidget()

        conn = sqlite3.connect('browser_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT url, title FROM history ORDER BY timestamp DESC')
        for url, title in cursor.fetchall():
            history_list.addItem(f"{title} - {url}")
        conn.close()

        layout.addWidget(history_list)
        dialog.setLayout(layout)
        dialog.exec_()

    def show_bookmarks(self):
        """Displays the bookmarks in a dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Bookmarks")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout()
        bookmarks_list = QListWidget()

        conn = sqlite3.connect('browser_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT url, title FROM bookmarks')
        bookmarks = cursor.fetchall()
        conn.close()

        for bookmark in bookmarks:
            item = f"{bookmark[1]} - {bookmark[0]}"
            bookmarks_list.addItem(item)

        bookmarks_list.itemClicked.connect(lambda item: self.open_bookmark(item.text()))

        layout.addWidget(bookmarks_list)
        dialog.setLayout(layout)

        dialog.exec_()

    def open_bookmark(self, bookmark_text):
        """Opens a bookmark in the current tab."""
        url = bookmark_text.split(" - ")[0]
        self.tabs.currentWidget().setUrl(QUrl(url))

    def open_customize_menu(self):
        """Opens the customization menu."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Customize Browser")
        dialog.setFixedSize(300, 200)

        layout = QVBoxLayout()

        # Add a button to change the color theme
        color_btn = QPushButton("Change Color Theme")
        color_btn.clicked.connect(self.select_color_theme)
        layout.addWidget(color_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def select_color_theme(self):
        """Allows the user to select a color theme."""
        color = QColorDialog.getColor()
        if color.isValid():
            bg_color = color.name()

            # Apply color to the browser
            self.setStyleSheet(f"background-color: {bg_color};")

            # Save customization to the database
            self.save_customization(bg_color, "white")

    def save_customization(self, bg_color, text_color):
        """Saves the customization settings to the database."""
        conn = sqlite3.connect('browser_data.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customization")  # Clear previous customization
        cursor.execute('INSERT INTO customization (bg_color, text_color) VALUES (?, ?)', (bg_color, text_color))
        conn.commit()
        conn.close()

    def load_customization(self):
        """Loads the customization settings from the database."""
        conn = sqlite3.connect('browser_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT bg_color, text_color FROM customization ORDER BY id DESC LIMIT 1')
        customization = cursor.fetchone()
        conn.close()

        if customization:
            bg_color, text_color = customization
            self.setStyleSheet(f"background-color: {bg_color}; color: {text_color};")

    def save_history(self, url, title):
        """Saves the visited page to the browsing history."""
        conn = sqlite3.connect('browser_data.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO history (url, title) VALUES (?, ?)', (url, title))
        conn.commit()
        conn.close()

    class CustomTabBar(QTabBar):
        """Custom TabBar that shows an 'X' on hover to close the tab."""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.browser_window = parent

        def paintEvent(self, event):
            """Draws the 'X' on the tab when hovered."""
            super().paintEvent(event)
            painter = QPainter(self)
            for index in range(self.count()):
                rect = self.tabRect(index)
                if self.tabAt(self.mapFromGlobal(self.cursor().pos())) == index:
                    # Draw the close button ('X')
                    x_rect = rect.adjusted(rect.width() - 20, 5, -5, -5)
                    painter.drawText(x_rect, Qt.AlignCenter, "X")

        def mousePressEvent(self, event):
            """Handles click on the 'X' to close the tab."""
            clicked_index = self.tabAt(event.pos())
            rect = self.tabRect(clicked_index)
            x_rect = rect.adjusted(rect.width() - 20, 5, -5, -5)

            if x_rect.contains(event.pos()) and self.browser_window.tabs.count() > 1:
                self.browser_window.close_tab(clicked_index)
            else:
                super().mousePressEvent(event)


# Main function
def main():
    app = QApplication(sys.argv)
    setup_database()
    window = BrowserWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
