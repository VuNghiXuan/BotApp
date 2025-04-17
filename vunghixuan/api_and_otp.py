# src/vunghixuan/create_project.py
"""
Đây là code lấy mã Otp cho pypi vunghixuan
"""
import pyotp
class APIKey:
    def __init__(self, key):
        self.key = key

    def get_api(self):
        # Thực hiện các tác vụ của bạn
        print(self.key)

class Otp:
    def __init__(self):
        pass

    def get_otp(self, key):
        # Thực hiện các tác vụ của bạn
        topt = pyotp.TOTP(key)
        print(topt.now())

    # Đây là mã của pypi vunghixuan
    def otp_vunghixuan(self):
        key = 'OXATAFVTTUIVMXNQCKMZAOFZYUYE6MGZ'
        self.get_otp(key)