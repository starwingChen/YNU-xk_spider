# 部署方法
# https://cloud.tencent.com/document/product/583/55594#install
import base64
import ddddocr
# pip install ddddocr
# 腾讯云，云函数：pip3 install ddddocr -t ./src
import binascii
from flask import Flask, request, jsonify, render_template
import codecs
import sys

# 设置网页编码
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

app = Flask(__name__)
app.config.update(DEBUG=False)
UPLOAD_FOLDER = 'upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF', 'jfif', 'jpeg'}

# ocr验证码识别初始化
ocr = ddddocr.DdddOcr()


# 获取文件后缀
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# 判断是否为base64
def isBase64Img(str_img):
    try:
        base64_img = str_img.split(',')[1]
        return base64.b64decode(base64_img)
    except binascii.Error:
        return False


@app.route('/')
def index():
    return render_template('index.html')


# 识别base64图片
@app.route('/base64img', methods=['GET', 'POST'])
def base64img():
    if request.method == 'GET':
        src = request.args['data']
    else:
        src = request.form['data']
    if isBase64Img(src):
        data = src.split(',')[1]
        image_data = base64.b64decode(data)
        res = ocr.classification(image_data)
        if not res:
            return jsonify({'code': -404, 'msg': '识别失败'})
        return jsonify({'code': 200, 'data': str(res), 'msg': '识别成功'})
    else:
        return jsonify({'code': -300, 'msg': 'base64图片转存失败'})


# 识别上传的图片
@app.route('/up_file', methods=['POST'], strict_slashes=False)
def up_file():
    if request.method == 'POST':  # 如果是 POST 请求方式
        file = request.files.get('file')  # 获取上传的文件
        if not file:
            return jsonify({'code': -201, 'msg': '没有上传图片'})
        if not allowed_file(file.filename):
            return jsonify({'code': -202, 'msg': '文件格式不支持'})
        img = file.stream.read()
        res = ocr.classification(img)
        if not res:
            return jsonify({'code': -404, 'msg': '识别失败'})
        return jsonify({'code': 200, 'data': str(res), 'msg': '识别成功'})
    # 使用 GET 方式请求页面时或是上传文件失败时返回上传文件的表单页面
    return jsonify({'code': -200, 'msg': '图片上传失败'})


@app.errorhandler(400)
def error(e):
    print(e)
    return jsonify({'code': -400, 'msg': str(e)})


@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'code': -3000, 'msg': '非法请求'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
