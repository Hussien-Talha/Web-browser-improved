import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QVBoxLayout, 
    QWidget, QFileDialog, QTabWidget, QMenu, QLabel, QHBoxLayout, QInputDialog, 
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit as QLE, QVBoxLayout as QVL, QHBoxLayout as QHL, QPushButton
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt, QTimer, pyqtSignal, QEventLoop, QThread
from PyQt5.QtGui import QIcon, QPixmap, QMovie

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_data()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        # Initialize UI components
        self.url_bar = QLineEdit()
        self.security_icon = QLabel()
        self.init_ui()

        self.showMaximized()

        # Restore previous session
        self.restore_session()

    def init_ui(self):
        # Create toolbar
        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        # Add buttons to the toolbar
        self.add_navbar_buttons()

    def load_data(self):
        if not os.path.exists("browser_data.json"):
            self.data = {
                "bookmarks": [],
                "history": [],
                "passwords": [],
                "open_tabs": []
            }
        else:
            with open("browser_data.json", "r") as f:
                self.data = json.load(f)

    def save_data(self):
        self.data["open_tabs"] = [self.tabs.widget(i).url().toString() for i in range(self.tabs.count())]
        with open("browser_data.json", "w") as f:
            json.dump(self.data, f)

    def add_navbar_buttons(self):
        back_btn = QAction("Back", self)
        back_btn.triggered.connect(lambda: self.current_browser().back())
        self.navbar.addAction(back_btn)

        forward_btn = QAction("Forward", self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        self.navbar.addAction(forward_btn)

        reload_btn = QAction("Reload", self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        self.navbar.addAction(reload_btn)

        home_btn = QAction("Home", self)
        home_btn.triggered.connect(self.navigate_home)
        self.navbar.addAction(home_btn)

        # Add a search bar and security icon to the toolbar
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(self.url_bar)

        self.update_security_icon("http://")
        self.navbar.addWidget(self.security_icon)

        # Add bookmark button
        bookmark_btn = QAction("Bookmark", self)
        bookmark_btn.triggered.connect(self.add_bookmark)
        self.navbar.addAction(bookmark_btn)

        # Create a menu for bookmarks
        self.bookmarks_menu = QMenu("Bookmarks", self)
        self.update_bookmarks_menu()
        self.navbar.addAction(self.bookmarks_menu.menuAction())

        # Add history button
        history_btn = QAction("History", self)
        history_btn.triggered.connect(self.show_history)
        self.navbar.addAction(history_btn)

        # Create a menu for history
        self.history_menu = QMenu("History", self)
        self.update_history_menu()
        self.navbar.addAction(self.history_menu.menuAction())

        # Add password manager button
        password_btn = QAction("Passwords", self)
        password_btn.triggered.connect(self.manage_passwords)
        self.navbar.addAction(password_btn)

        # Add new tab button
        new_tab_btn = QAction("New Tab", self)
        new_tab_btn.triggered.connect(self.add_new_tab)
        self.navbar.addAction(new_tab_btn)

    def create_new_tab(self, qurl=None, label="Blank"):
        if qurl is None:
            qurl = QUrl("http://www.google.com")
        browser = QWebEngineView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_url(qurl, browser))
        browser.loadFinished.connect(self.update_title)
        browser.loadStarted.connect(self.loading_animation)
        browser.setPage(WebEnginePage(browser.page(), self))
        self.update_url(qurl, browser)

    def add_new_tab(self):
        self.create_new_tab()

    def close_tab(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)
        self.save_data()

    def current_browser(self):
        return self.tabs.currentWidget()

    def current_tab_changed(self, i):
        if i != -1:
            qurl = self.current_browser().url()
            self.update_url(qurl, self.current_browser())
            self.update_title()

    def update_title(self):
        title = self.current_browser().page().title()
        self.setWindowTitle("%s - My Browser" % title)
        self.tabs.setTabText(self.tabs.currentIndex(), title)

    def navigate_home(self):
        self.current_browser().setUrl(QUrl("http://www.google.com"))

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http://") and not url.startswith("https://"):
            if '.' in url:
                url = "http://" + url
            else:
                url = "https://www.google.com/search?q=" + url
        self.current_browser().setUrl(QUrl(url))

    def update_url(self, qurl, browser=None):
        if browser != self.current_browser():
            return
        self.url_bar.setText(qurl.toString())
        self.update_security_icon(qurl.toString())
        self.data["history"].append(qurl.toString())
        self.update_history_menu()
        self.save_data()

    def update_security_icon(self, url):
        if url.startswith("https://"):
            self.security_icon.setPixmap(QPixmap("lock.png").scaled(20, 20, Qt.KeepAspectRatio))
        else:
            self.security_icon.setPixmap(QPixmap("caution.png").scaled(20, 20, Qt.KeepAspectRatio))

    def add_bookmark(self):
        url = self.current_browser().url().toString()
        if url in self.data["bookmarks"]:
            QMessageBox.information(self, "Bookmark", "This page is already bookmarked.")
        else:
            self.data["bookmarks"].append(url)
            self.update_bookmarks_menu()
            self.save_data()
            self.show_bookmark_confirmation()

    def show_bookmark_confirmation(self):
        confirmation_label = QLabel("Bookmarked!")
        confirmation_label.setStyleSheet("color: green; font-size: 14px;")
        confirmation_label.setAlignment(Qt.AlignCenter)
        self.navbar.addWidget(confirmation_label)
        QTimer.singleShot(2000, lambda: self.navbar.removeWidget(confirmation_label))

    def update_bookmarks_menu(self):
        self.bookmarks_menu.clear()
        for bookmark in self.data["bookmarks"]:
            action = QAction(bookmark, self)
            action.triggered.connect(lambda checked, url=bookmark: self.current_browser().setUrl(QUrl(url)))
            self.bookmarks_menu.addAction(action)

    def show_history(self):
        self.history_menu.clear()
        for url in self.data["history"]:
            action = QAction(url, self)
            action.triggered.connect(lambda checked, url=url: self.current_browser().setUrl(QUrl(url)))
            self.history_menu.addAction(action)

    def update_history_menu(self):
        self.history_menu.clear()
        for url in self.data["history"]:
            action = QAction(url, self)
            action.triggered.connect(lambda checked, url=url: self.current_browser().setUrl(QUrl(url)))
            self.history_menu.addAction(action)

    def manage_passwords(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Password Manager")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        username_input = QLineEdit()
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Username:", username_input)
        form_layout.addRow("Password:", password_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_password(username_input.text(), password_input.text(), dialog))
        button_box.rejected.connect(dialog.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_password(self, username, password, dialog):
        if username and password:
            self.data["passwords"].append({"username": username, "password": password})
            self.save_data()
            dialog.accept()
        else:
            QMessageBox.warning(self, "Input Error", "Please fill in both fields.")

    def loading_animation(self):
        self.setWindowTitle("Loading...")
        movie = QMovie("loading.gif")
        self.security_icon.setMovie(movie)
        movie.start()

    def restore_session(self):
        for tab_url in self.data["open_tabs"]:
            self.create_new_tab(QUrl(tab_url))
        if not self.data["open_tabs"]:
            self.create_new_tab()

class WebEnginePage(QWebEnginePage):
    def __init__(self, parent, browser):
        super().__init__(parent)
        self.browser = browser

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            self.browser.create_new_tab(url)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        open_link_action = QAction("Open link in new tab", self)
        open_link_action.triggered.connect(lambda: self.browser.create_new_tab(self.contextMenuData().linkUrl()))
        menu.addAction(open_link_action)
        menu.exec_(event.globalPos())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("My Browser")
    window = Browser()
    app.exec_()