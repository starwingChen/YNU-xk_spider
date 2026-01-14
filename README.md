# YNU-xk_spider

> [!CAUTION]
> **Disclaimer / 声明**
>
> This program is for technical exchange ONLY. Commercial use or charging fees is strictly prohibited. We reserve the right to discontinue all future maintenance if any unauthorized commercial activity is detected.
>
> 本程序仅供技术交流。严禁任何形式的收费行为。若再次发现违规收费，我们将停止后续一切维护。

云南大学选课爬虫，提供余课提醒服务，实现自动抢课功能。

> [重构版](https://github.com/davidwushi1145/YNU-xk_spider_Refactoring) - 若存在 bug 请到此版本提出 issue

## 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-01-14 | 线程安全重构：添加锁保护共享资源；优雅停止机制（stop() + _running）；移除死代码；Selenium 4.x Service 类适配；ThreadPoolExecutor 正确关闭；API 输入验证增强 |
| 2024-12-25 | 修复体育课问题及东陆校区问题 |
| 2024-06-26 | 修复完成 |
| 2024-03-08 | 修复已知的所有 bug |
| 2023-12-30 | 经测试 24 小时无异常 |
| 2023-12-28 | 解决 API 接口问题，多系统测试无异常 |
| 2023-06-23 | 解决自动注销问题，测试 3 小时无注销 |

## 功能特性

- 自动登录选课系统（含验证码识别）
- 课程余量实时监控
- 余课微信提醒（通过 Server酱）
- 自动抢课（检测到空位立即选课）
- 支持课程类型：素选课、主修课（必修/专选）、体育课

## 环境要求

| 依赖 | 版本要求 |
|------|----------|
| Python | 3.10+ |
| Chrome 浏览器 | 最新版本 |
| ChromeDriver | 与 Chrome 版本匹配 |

**Python 依赖库**：
```
selenium==4.1.0
requests
flask==3.0.0
ddddocr==1.5.5
fake_useragent
```

## 快速开始

### 1. 安装依赖

```bash
cd YNU-xk_spider
pip install -r requirements.txt
```

### 2. 下载 ChromeDriver

下载与你的 Chrome 版本匹配的 ChromeDriver：https://googlechromelabs.github.io/chrome-for-testing/

### 3. 启动验证码识别服务

```bash
python xk_spider/api.py
```

### 4. 配置并运行

编辑 `xk_spider/run.py`，填写以下字段：

```python
stdCode = '你的学号'
pswd = '你的密码'
key = '你的Server酱Key'  # 可选，用于微信通知
path = '/path/to/chromedriver'  # ChromeDriver 路径

# 要抢的素选课
publicCourses = [
    ['课程名称', '授课老师'],
]

# 要抢的体育课
peCourses = [
    # ['羽毛球（四）', '范丽霞'],
]

# 要抢的主修课
programCourse = [
    # ['大学生创新创业教育', '段连丽'],
]
```

运行程序：

```bash
python xk_spider/run.py
```

## 校区配置

如需选择**东陆校区**的课程，需修改 `xk_spider/GetCourse.py` 中的 `campus` 参数：

| 校区 | campus 值 |
|------|-----------|
| 呈贡校区（默认） | `"05"` |
| 东陆校区 | `"01"` |

## 验证码识别服务

### 本地部署（推荐）

```bash
pip install ddddocr flask
python xk_spider/api.py
```

服务地址：`http://127.0.0.1:5000/base64img`

### Windows 打包版

[下载 api.exe](https://drive.google.com/file/d/1IsszQXBuvdYbpmnyibLAGw92p8SdW54T/view?usp=sharing)（Windows x86 环境）

### 云函数部署

```bash
docker pull ccr.ccs.tencentyun.com/ocrr/ocr:2.0.0
```

使用云函数需修改 `AutoLogin.py` 中的 `imgcode_online` 函数，将请求地址改为云函数 URL。

<details>
<summary>点击查看云函数版代码</summary>

```python
def imgcode_online(imgurl):
    if not hasattr(imgcode_online, "counter"):
        imgcode_online.counter = 0
    if not hasattr(imgcode_online, "timestamp"):
        imgcode_online.timestamp = time.time()

    current_time = time.time()
    if current_time - imgcode_online.timestamp > 60:
        imgcode_online.counter = 0
        imgcode_online.timestamp = current_time

    imgcode_online.counter += 1
    if imgcode_online.counter > 10:
        imgcode_online.counter = 0
        imgcode_online.timestamp = current_time
        return False

    img_data = base64.b64decode(imgurl.split(",")[-1])
    files = {'image': ('image.jpg', img_data)}
    response = requests.post('云函数URL/ocr/file/json', files=files)

    if response.text:
        try:
            result = json.loads(response.text)
            if result['status'] == 200:
                print(result['result'])
                return result['result']
            elif result['status'] != 200:
                time.sleep(10)
                return imgcode_online(imgurl)
            else:
                print(result['msg'])
                return 'error'
        except json.JSONDecodeError:
            print("Invalid JSON received")
            return 'error'
    else:
        print("Empty response received")
        return 'error'
```

</details>

## 成功示例

<img src="./resource/res1.png" height="250"> <img src="./resource/res2.jpg" height="250">
<img src="./resource/res3.jpg" height="250"> <img src="./resource/1.png" height="250">

## 常见问题

**Q: 出现 401 错误怎么办？**
A: 这是 session 过期，程序会自动重新登录。

**Q: ChromeDriver 崩溃怎么办？**
A: 程序已有异常处理，会自动重试。确保 Chrome 和 ChromeDriver 版本匹配。

**Q: 跨专业选修课支持吗？**
A: 未经测试，如有问题请提 issue。

## 致谢

- 原项目：https://github.com/starwingChen/YNU-xk_spider
- Server酱：https://sct.ftqq.com/

## 声明

**此程序仅作为技术交流之用，请勿将其用于任何形式的收费行为。**

---

如果本项目对你有帮助，欢迎点击右上角的 Star 支持一下 :)
