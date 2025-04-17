from vunghixuan.account.account_form import AccountForm
from vunghixuan.gui.login import LoginGroupBox  # Import LoginGroupBox
# Import the RegisterForm class (assuming its location)
# from vunghixuan.account.register.register_form import RegisterForm

class FormManager:
    def __init__(self, app_manager, main_window):
        self.app_manager = app_manager
        self.main_window = main_window
        self._login_form = None
        self._account_form = None
        self._register_form = None  # Initialize _register_form

    @property
    def login_form(self):
        if self._login_form is None:
            self._login_form = LoginGroupBox(self.main_window, self.app_manager.user_manager)
        return self._login_form

    @property
    def account_form(self):
        if self._account_form is None:
            self._account_form = AccountForm()
        return self._account_form

    # @property
    # def register_form(self):
    #     if self._register_form is None:
    #         # Assuming RegisterForm needs no special arguments here
    #         # You might need to pass app_manager or main_window if RegisterForm requires them
    #         # self._register_form = RegisterForm(self.app_manager, self.main_window)
    #         from vunghixuan.account.register.register_form import RegisterForm # Import here to avoid circular dependencies if any
    #         self._register_form = RegisterForm(self._account_form.user_permissions_table)
    #     return self._register_form