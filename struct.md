E:\BotApp\
├── dist\
├── build\
├── vunghixuan\
│   ├── account\
│   │   └── register\
│   │       ├── db_manager.py
│   │       └── ... (các file khác liên quan đến đăng ký)
│   ├── gui\
│   │   ├── widgets\
│   │   │   ├── MyQLabel.py
│   │   │   ├── MyQLineEdit.py
│   │   │   ├── MyQPushButton.py
│   │   │   ├── MyQTableWidget.py
│   │   │   └── ... (các widget tùy chỉnh khác)
│   │   ├── widgets_for_register\
│   │   │   ├── SearchTable.py
│   │   │   └── ... (các widget tùy chỉnh cho đăng ký)
│   │   └── ... (các file GUI khác)
│   ├── bot_station\
│   │   ├── thread_files.py
│   │   ├── load_gif_file.py
│   │   └── ... (các file liên quan đến bot station)
│   ├── settings.py
│   └── ... (các thư mục và file khác của gói vunghixuan)
├── main.py         (hoặc run_check_tickets.py có thể là entry point)
├── run_check_tickets.py
├── run_check_tickets.spec
├── ... (các file khác của dự án)
├── venv\           (thư mục virtual environment)
│   ├── Lib\
│   ├── Scripts\
│   └── ...
└── requirements.txt (có thể có)