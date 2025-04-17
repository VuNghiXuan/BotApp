from setuptools import setup, find_packages

setup(
    name='vunghixuan',
    version='0.1.6',
    description='Get API, OTP, Create Project',
    long_description='Gói này cung cấp các chức năng để lấy API, tạo OTP và quản lý dự án.Tạo giao diện User - date: 250217',
    author='Đặng Thanh Vũ',
    author_email='vunghixuan.info@gmail.com',
    # url='http://vunghixuan.com',  # Thay thế bằng URL trang chủ của bạn
    url='https://github.com/VuNghiXuan/pypi_package',
    license='MIT',  # Hoặc loại giấy phép bạn muốn
    packages=find_packages(), # Tự động tìm tất cả các gói con
    install_requires=[
        'pyotp==2.9.0',
        'PySide6==6.8.0.1',
        'PySide6_Addons==6.8.0.1',
        'PySide6_Essentials==6.8.0.1',
        'shiboken6==6.8.0.1',
        'SQLAlchemy==2.0.36',
        'typing_extensions==4.12.2',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],

    entry_points={
        'console_scripts': [
            'vunghixuan=vunghixuan:main',
        ],
    },
    python_requires='>=3.11',
)


"""
Tải gói thành công:

1. Tạo ra các gói phân phối: python setup.py sdist bdist_wheel
2. twine upload --username __token__ --password pypi-AgEIcHlwaS5vcmcCJGI3M2QzMDRmLTQwMDQtNDRiMy1iOGQ5LWVlZTBkZTIyZTEzYgACKlszLCI4OWIwMTU4NS0wNzFhLTQ1M2ItYTU2Yi1lMjU2YTAyYzUzMzkiXQAABiCclcNA_QewKusm6sWeIMUaR7TjTg23tmwFdGgecgsPmg dist/*

----------------------------------------------
Tải gói bắng file .pypirc
1. Tạo ra các gói phân phối: python setup.py sdist bdist_wheel


2. Cấu hình file:  .pypirc 
    Ghi chú: %USERPROFILE%\.pypirc trên Windows
    Nội dung file:
        [pypi]
        repository = https://upload.pypi.org/legacy/
        token = pypi-AgEIcHlwaS5vcmcCJGI3M2QzMDRmLTQwMDQtNDRiMy1iOGQ5LWVlZTBkZTIyZTEzYgACKlszLCI4OWIwMTU4NS0wNzFhLTQ1M2ItYTU2Yi1lMjU2YTAyYzUzMzkiXQAABiCclcNA_QewKusm6sWeIMUaR7TjTg23tmwFdGgecgsPmg

3. Tải gói lên pypi: twine upload --repository vunghixuan dist/*


python setup.py sdist upload
Nếu lỗi: twine upload dist/* --verbose


1. Tạo ra các gói phân phối: python setup.py sdist bdist_wheel
2. twine upload --username __token__ --password pypi-AgEIcHlwaS5vcmcCJGI3M2QzMDRmLTQwMDQtNDRiMy1iOGQ5LWVlZTBkZTIyZTEzYgACKlszLCI4OWIwMTU4NS0wNzFhLTQ1M2ItYTU2Yi1lMjU2YTAyYzUzMzkiXQAABiCclcNA_QewKusm6sWeIMUaR7TjTg23tmwFdGgecgsPmg dist/*

Mai xem :https://www.youtube.com/watch?v=4gG8Ans-imw 
"""