# Dither Frame
## 環境構築
[13.3inch e-Paper HAT+ (E) Manual](https://www.waveshare.com/wiki/13.3inch_e-Paper_HAT+_(E)_Manual#Introduction)
[Demo](https://files.waveshare.com/wiki/13.3inch%20e-Paper%20HAT%2B/13.3inch_e-Paper_E.zip)をダウンロードし、
`13.3inch_e-Paper_E/RaspberryPi/python/lib`をこのレポジトリのルート直下に移動する

こういうツリー構造にする
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
│   ├── __init__.py
├── README.md
└── run.sh
```

repository cloneもあり
[waveshareteam/e-Paper](https://github.com/waveshareteam/e-Paper)

Part Number	Colors	Grey Scale	Resolution	Display size (mm)	Outline Dimension (mm)	Full Refresh Time (s)	Partial Refresh1	Pi Head-er2	Flexi-ble	Interface
13.3inch e-Paper HAT (E)	E6 full color	2	1600×1200	270.40 × 202.80	284.70 × 208.80	19	 	√	 	SPI


```sh
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install pillow flask
```

## 実行
```sh
$ source .venv/bin/activate
$ sudo python3 app.py
```
20秒くらい初期化に時間がかかる。

## 画像のアップロード

[スクショの画像]

画像をアップロードし、20秒ほどレンダリング時間をかけた後に、電子ペーパー上に画像が表示される


概要

本プロジェクトは、Flaskを用いたWebインターフェースを介して、ユーザーが画像をアップロードした画像を電子ペーパーに表示します。

特徴
	•	Webベースの操作画面
ユーザーはブラウザから画像のアップロードや回転処理を行えます。Bootstrapを利用しており、モバイルにも対応しています。
	•	画像処理機能
アップロードまたはダウンロードされた画像に対し、以下の処理を自動で実施します。
	•	EXIF情報に基づく向き補正
	•	縦長画像の場合は90°回転による横長化
	•	180°回転による上下逆転の修正
	•	ターゲットサイズ（電子ペーパー用サイズ）へのリサイズ
	•	自動ヒストグラムストレッチによるコントラスト調整
	•	彩度の強調
	•	誤差拡散法によるカスタムパレット変換
電子ペーパーで利用可能な色（red, green, blue, yellow, black, white）に合わせ、Floyd–Steinbergの誤差拡散法を用いて画像を変換します。

動作環境
	•	Python 3.x
	•	Flask
	•	Pillow (PIL)
	•	電子ペーパー用モジュール (epd13in3E)

使用方法
	1.	ソースコードの配置
本コード一式を適切なディレクトリに配置してください。
	2.	プログラムの実行
Pythonスクリプトを実行すると、Flaskサーバーが起動するとともに、バックグラウンドで24時間ごとにWebから画像をダウンロードする処理が開始されます。
	4.	Webインターフェースの利用
Webブラウザで指定ホスト（例: http://localhost）にアクセスすると、以下の操作が可能です。
	•	画像ファイルのアップロード
	•	現在表示中の画像のプレビュー
	•	「画像を90度回転」ボタンによる画像回転処理

コードの構成
	•	Flaskアプリケーション
主なエンドポイントは以下の通りです。
	•	/
メイン画面（画像アップロードフォーム、プレビュー表示）
	•	/upload
ユーザーからの画像アップロードを受け付け、画像処理および電子ペーパー更新処理を開始
	•	/rotate
現在表示中の画像を90度回転し、更新処理を開始
	•	/preview
現在のレンダリング状態とプレビュー画像（Base64エンコード済み）を返却
	•	画像処理関数
	•	process_image

