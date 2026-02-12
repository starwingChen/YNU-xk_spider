import PyInstaller.__main__

fake_useragent_data_path = 'xk_spider/data/browsers.json'

PyInstaller.__main__.run([
    'xk_spider/run.py',  # 替换为你的脚本名
    '--onefile',
    '--add-data', 'xk_spider/AutoLogin.py;.',
    '--add-data', 'xk_spider/GetCourse.py;.',
    f'--add-data={fake_useragent_data_path};fake_useragent/data',
    '--hidden-import=fake_useragent',
    '--hidden-import=concurrent.futures',
    '--name', 'run'
])
