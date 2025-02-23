import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
print(libdir)
if os.path.exists(libdir):
    sys.path.append(libdir)

from flask import Flask, request, render_template_string, redirect, url_for, jsonify
from PIL import Image, ImageOps, ImageEnhance
import io
import time
import threading
import base64
import epd13in3E  # ご提示の電子ペーパー用モジュールを利用

app = Flask(__name__)

# グローバル変数：現在レンダリングされている画像(PIL Image)およびプレビュー用Base64画像、処理完了フラグ
current_image = None
rendered_image_data = None
rendering_complete = False

# 電子ペーパーの初期化（起動時は画像表示しない）
epd = epd13in3E.EPD()
try:
    print("EPD 初期化...")
    epd.Init()
    print("ディスプレイをクリア中...")
    epd.Clear()
except Exception as e:
    print("EPD 初期化エラー:", e)

# ターゲットサイズは常にランドスケープ（幅 > 高さ）にする
def get_target_size():
    return (max(epd.width, epd.height), min(epd.width, epd.height))

def apply_dithering(image):
    """
    誤差拡散法（Floyd–Steinberg）を用いて、画像をカスタムパレットに変換します。
    電子ペーパーで利用可能な色は、red, green, blue, yellow, black, white です。
    """
    # カスタムパレット：red, green, blue, yellow, black, white（RGBそれぞれの値）
    custom_palette = [
        255, 0, 0,    # red
        0, 255, 0,    # green
        0, 0, 255,    # blue
        255, 255, 0,  # yellow
        0, 0, 0,      # black
        255, 255, 255 # white
    ]
    # パレットは256色分（768個の値）必要なため、残りは0で埋める
    custom_palette.extend([0] * (768 - len(custom_palette)))
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(custom_palette)
    # 誤差拡散法(Floyd–Steinberg)を利用してパレット変換
    dithered = image.convert("RGB").convert("P", palette=palette_image, dither=Image.FLOYDSTEINBERG)
    return dithered

def update_epaper(image):
    """
    与えられた image (PIL Image) を電子ペーパーに表示し、
    プレビュー用の Base64 画像としてグローバル変数を更新します。
    ※ターゲットサイズは常にランドスケープ向け (例: 1600×1200) に調整し、
      その後誤差拡散法でカスタムパレット変換を実施します。
    """
    global current_image, rendered_image_data, rendering_complete
    try:
        # 再初期化＆クリア
        epd.Init()
        resample_filter = Image.Resampling.LANCZOS
        # ターゲットサイズにフィット（ランドスケープ向け）
        target_size = get_target_size()
        image = ImageOps.fit(image, target_size, method=resample_filter)
        # 誤差拡散法でカスタムパレット変換
        dithered = apply_dithering(image)
        buf = epd.getbuffer(dithered)
        epd.display(buf)
        epd.sleep()
        # グローバル変数更新（プレビュー用は dithered な画像を使用）
        current_image = dithered
        buffered = io.BytesIO()
        dithered.save(buffered, format="PNG")
        rendered_image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
        rendering_complete = True
    except Exception as e:
        print("EPD 更新エラー:", e)
        rendering_complete = False

def process_image(image_file):
    """
    アップロードされた画像に対して以下の処理を実施：
      - EXIF情報に基づく向き補正
      - 画像が縦長の場合のみ90°回転して横長に変換（ランドスケープ状態を維持）
      - 常に180°回転して上下逆転を修正
      - 画像を電子ペーパー表示用のサイズにリサイズ
      - 自動ヒストグラムストレッチでコントラスト調整
      - 彩度を3.0倍に強調
    ※誤差拡散法によるパレット変換は update_epaper 内で実施します。
    """
    image = Image.open(image_file).convert('RGB')
    image = ImageOps.exif_transpose(image)
    if image.height > image.width:
        image = image.rotate(90, expand=True)
    image = image.rotate(180, expand=True)
    resample_filter = Image.Resampling.LANCZOS
    # リサイズ：ターゲットサイズはランドスケープ (例: 1600×1200)
    target_size = get_target_size()
    image = image.resize(target_size, resample_filter)
    image = ImageOps.autocontrast(image)
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(3.0)
    return image

# HTMLテンプレート（Bootstrap利用＋AJAXによる非同期更新）
INDEX_HTML = """
<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>電子ペーパー画像操作</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
      body { padding-top: 50px; background-color: #f8f9fa; }
      .container { max-width: 600px; }
      .preview { margin-top: 20px; text-align: center; }
    </style>
  </head>
  <body>
    <div class="container">
      <h1 class="mb-4 text-center">電子ペーパー画像操作</h1>
      <form id="uploadForm" enctype="multipart/form-data">
        <div class="form-group">
          <label for="image">画像ファイルを選択</label>
          <input type="file" class="form-control-file" id="image" name="image" accept="image/*" required>
        </div>
        <button type="submit" class="btn btn-primary btn-block">アップロード</button>
      </form>
      <div id="message" class="mt-3"></div>
      <div class="preview" id="previewSection" style="display: none;">
        <h4>レンダリング画像プレビュー</h4>
        <img id="previewImg" src="" class="img-fluid" alt="Rendered Image">
        <br>
        <button id="rotateBtn" class="btn btn-secondary mt-3">画像を90度回転</button>
      </div>
    </div>
    <script>
      // プレビュー更新用のポーリング関数
      function pollPreview() {
        fetch('/preview')
          .then(response => response.json())
          .then(data => {
            if (data.success && data.rendered_image) {
              document.getElementById('previewImg').src = "data:image/png;base64," + data.rendered_image;
              document.getElementById('previewSection').style.display = 'block';
              document.getElementById('message').innerHTML = '<div class="alert alert-success" role="alert">操作が成功しました！</div>';
            } else {
              document.getElementById('message').innerHTML = '<div class="alert alert-info" role="alert">レンダリング中...</div>';
              setTimeout(pollPreview, 2000);
            }
          })
          .catch(error => {
            console.error('Error:', error);
            document.getElementById('message').innerHTML = '<div class="alert alert-info" role="alert">レンダリング中...</div>';
            setTimeout(pollPreview, 2000);
          });
      }

      // アップロードフォーム送信時の処理（AJAXでPOST）
      document.getElementById('uploadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        document.getElementById('message').innerHTML = '<div class="alert alert-info" role="alert">アップロード処理中...</div>';
        var formData = new FormData(this);
        fetch('/upload', {
          method: 'POST',
          body: formData
        })
        .then(response => response.json())
        .then(data => {
          document.getElementById('message').innerHTML = '<div class="alert alert-info" role="alert">レンダリング中...</div>';
          pollPreview();
        })
        .catch(error => {
          console.error('Error:', error);
          document.getElementById('message').innerHTML = '<div class="alert alert-danger" role="alert">エラーが発生しました</div>';
        });
      });

      // 「画像を90度回転」ボタン押下時の処理（AJAXでGET）
      document.getElementById('rotateBtn').addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('message').innerHTML = '<div class="alert alert-info" role="alert">回転処理中...</div>';
        fetch('/rotate')
          .then(response => response.json())
          .then(data => {
            document.getElementById('message').innerHTML = '<div class="alert alert-info" role="alert">レンダリング中...</div>';
            pollPreview();
          })
          .catch(error => {
            console.error('Error:', error);
            document.getElementById('message').innerHTML = '<div class="alert alert-danger" role="alert">エラーが発生しました</div>';
          });
      });
    </script>
  </body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(INDEX_HTML)

@app.route('/upload', methods=['POST'])
def upload():
    global current_image, rendered_image_data, rendering_complete
    rendering_complete = False
    if 'image' not in request.files:
        return jsonify({'message': '画像が選択されていません'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'message': 'ファイルがありません'}), 400
    try:
        processed = process_image(file)
        threading.Thread(target=update_epaper, args=(processed,)).start()
    except Exception as e:
        return jsonify({'message': "画像処理エラー: {}".format(e)}), 500
    return jsonify({'message': 'アップロード処理を開始しました'})

@app.route('/rotate', methods=['GET'])
def rotate():
    global current_image, rendered_image_data, rendering_complete
    if current_image is None:
        return jsonify({'message': '表示中の画像がありません'}), 400
    try:
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.LANCZOS
        rotated = current_image.rotate(90, expand=True)
        target_size = get_target_size()
        rotated = ImageOps.fit(rotated, target_size, method=resample_filter)
        rendering_complete = False
        threading.Thread(target=update_epaper, args=(rotated,)).start()
    except Exception as e:
        return jsonify({'message': "回転エラー: {}".format(e)}), 500
    return jsonify({'message': '回転処理を開始しました'})

@app.route('/preview', methods=['GET'])
def preview():
    global rendered_image_data, rendering_complete
    return jsonify({
        'rendered_image': rendered_image_data,
        'success': rendering_complete
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

