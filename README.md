# Dither Frame
## プロジェクト概要
本プロジェクトは、Flask を用いた Web インターフェース経由で、ユーザーがアップロードした画像を電子ペーパーに表示するシステムです。
Webベースの操作画面から画像のアップロードや回転処理が可能で、Bootstrap によりモバイルにも対応しています。
また、画像に対しては自動で以下の処理を実施します。

- EXIF 情報に基づく向き補正
- 縦長画像の場合の 90° 回転による横長化
- 180° 回転による上下逆転の修正
- 電子ペーパー用サイズへのリサイズ
- 自動ヒストグラムストレッチによるコントラスト調整
- 彩度の強調
- Floyd–Steinberg の誤差拡散法によるカスタムパレット変換（電子ペーパーが対応している6色に対応）

## 動作環境
- Raspberry Pi 3B+
- 電子ペーパー用モジュール: [13.3inch E Ink Spectra 6 (E6) Full color E-Paper Display](https://www.waveshare.com/13.3inch-e-paper-hat-plus-e.htm?sku=29355)

## 環境構築
以下のリンクからデモファイルをダウンロードしてください。
waveshareteam/e-paper repositoryの[E-paper_Separate_Program/13.3inch_e-Paper_E/RaspberryPi/python/lib](https://github.com/waveshareteam/e-Paper/tree/master/E-paper_Separate_Program/13.3inch_e-Paper_E/RaspberryPi/python/lib)をダウンロードし、本ディレクトリのルート直下に移動してください。

ディレクトリ構成例
以下のようなツリー構造となるように配置します。

```sh
.
├── app.py
├── lib
│   ├── DEV_Config_32_b.so
│   ├── DEV_Config_32_w.so
│   ├── DEV_Config_64_b.so
│   ├── DEV_Config_64_w.so
│   ├── epd13in3E.py
│   ├── epdconfig.py
│   └── __init__.py
├── README.md
└── run.sh
```

次に本レポジトリ直下に仮想環境を作成し、必要なPythonパッケージをインストールします
```sh
$ cd ./dither_frame
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install pillow flask
```

## Dither Frameの実行
### Webサーバーの起動
```sh
$ source .venv/bin/activate
$ sudo python3 app.py
```
電子ペーパーの初期化に20秒ほどかかった後にWebサーバーが立ち上がります
sudoで実行することで、80番ポートでlistenします。

### 画像のアップロード
任意のブラウザで指定ホストにアクセスし、画像ファイルをアップロードしてください。
アップロード後、レンダリング時間を経て、電子ペーパーに画像が表示されます。

## コードの構成
Flask アプリケーション
主なエンドポイントは以下の通りです。

- `/`: メイン画面（画像アップロードフォームおよびプレビュー表示）
- `/upload`: ユーザーからの画像アップロードを受け付け、画像処理および電子ペーパーの更新処理を開始
- `/rotate`: 現在表示中の画像を 90° 回転し、更新処理を開始
- `/preview`: 現在のレンダリング状態とプレビュー画像（Base64 エンコード済み）を返却
- `process_image`: 画像の各種処理（向き補正、リサイズ、ヒストグラムストレッチ、彩度調整、誤差拡散法によるパレット変換）を適用

## 参考資料
- [13.3inch e-Paper HAT+ (E) Manual](https://www.waveshare.com/wiki/13.3inch_e-Paper_HAT+_(E)_Manual#Introduction)
