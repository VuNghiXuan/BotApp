# menu_toolbar_actions_for_basewindow.py
from widgets import  MyQVBoxLayout, MyQTableWidget
from gui.menu_bar import MyQMenuBar
from gui.tab_bar import  MyQTabWidget
from settings import MENUS_INFO, TABS_INFO

class MenuToolBarActions():
    """
    Đây là lớp tạo Thanh MenuBar, ToolBar và các Actions và đặt lên đầu lớp BaseWindow"""
    def __init__(self) -> None:
        self.top_layout, self.menu_bar, self.tab_bar = self.init_menubar_and_actions()
        

    def init_menubar_and_actions(self):    
        top_layout = MyQVBoxLayout()

        # Tạo (QMenuBar) đặt vào topLayout
        menu_bar = MyQMenuBar()
        menu_bar.add_multiple_menus_and_actions(MENUS_INFO)
        top_layout.addWidget(menu_bar)
        
        # Tạo (QTab, QToolBar) đặt vào topLayout        
        tab_bar = MyQTabWidget()
        tab_bar.add_tabs(TABS_INFO)
        top_layout.addWidget(tab_bar)

        return top_layout, menu_bar, tab_bar
    
    class TableForTab(MyQTableWidget):
        pass