import logging
import logging.handlers


# Nội dung từ file log_manager_log.py
class LoggingConfig:
    """
    Cấu hình logging cho ứng dụng.
    """
    _instance = None  # Thuộc tính lớp để lưu trữ thể hiện duy nhất

    def __init__(self, log_file="my_app.log", log_level=logging.ERROR, log_format="%(asctime)s - %(levelname)s - %(message)s", max_bytes=10*1024*1024, backup_count=5, encoding="utf-8"):
        """
        Khởi tạo cấu hình logging.

        Args:
            log_file (str): Tên file log. Mặc định là "my_app.log".
            log_level (int): Mức log. Mặc định là logging.ERROR.
            log_format (str): Định dạng log. Mặc định là "%(asctime)s - %(levelname)s - %(message)s".
            max_bytes (int): Kích thước tối đa của file log (bytes). Mặc định là 10MB.
            backup_count (int): Số lượng file log cũ được giữ lại. Mặc định là 5.
            encoding (str): Mã hóa của file log. Mặc định là "utf-8".
        """
        if self._instance is not None:
            raise Exception("Cannot create multiple instances of LoggingConfig. Use get_logger() instead.")
        self.log_file = log_file
        self.log_level = log_level
        self.log_format = log_format
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.encoding = encoding
        self.logger = None  # Thêm thuộc tính logger

    @classmethod
    def get_logger(cls, *args, **kwargs):
        """
        Trả về thể hiện duy nhất của logger.  Nếu chưa có, tạo mới.

        Returns:
            logging.Logger: Đối tượng logger.
        """
        if not cls._instance:
            cls._instance = cls(*args, **kwargs)  # Tạo thể hiện chỉ khi nó chưa tồn tại
            cls._instance.configure_logging() # Gọi cấu hình ở đây
        return cls._instance.logger

    def configure_logging(self):
        """
        Cấu hình logging với các thiết lập đã cho.
        """
        # Kiểm tra nếu logger đã được cấu hình trước đó
        if self.logger:
            return  # Không cấu hình lại nếu đã có

        # Tạo handler cho file log
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding=self.encoding,
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(logging.Formatter(self.log_format))

        # Lấy logger và thêm handler
        self.logger = logging.getLogger(__name__)  # Sử dụng self.logger
        self.logger.addHandler(file_handler)
        self.logger.setLevel(self.log_level)

# Khởi tạo logger từ LoggingConfig
logmanager = LoggingConfig.get_logger()