# receiptori
レシートを整理するための個人用アプリ

## 概要
- OpenAI APIを使って、レシートから情報を抽出する
- JSONだけでなく、レシート画像も保存する

## 準備
- Pythonの仮想環境を用意する
  ```
  python -m venv venv
  venv/Scripts/activate
  pip install -r requirements.txt
  ```
    - これはWindows環境用
- 変数を指定する
  - `_Variables.py`を`Variables.py`に変更する
  - `Variables.py`の値を変更する
    - OPENAI_API_KEY: OpenAI APIキー
    - IP_ADDRESS: 自身のデバイスのIPアドレス

### 使い方
- app.pyを実行する
  ```
  python app.py
  ```
- 撮影用ページ、確認用ページにアクセスする
  ```
  http://{IP_ADDRESS}:8000/capture/
  ```
  ```
  http://{IP_ADDRESS}:8000/review/
  ```
- 撮影用ページでレシートの写真を撮る
- 確認用ページで分析結果を確認する
- 確認用ページの保存ボタンで、解析結果と画像が保存される

## 開発メモ
- 出力されるJSONは以下のような形式
  ```json
  {
    'shop':'{店名}',
    'datetime':'{日時(ISO8601形式)}',
    'items':[
      {
        'name':'{商品名}' 
        'amount':{個数},
        'price':{値段},
        'tax_rate':{税率}
      },
      ...
    ],
    'total_price':'{合計金額}',
    'payment_method':'{支払い方法}',
  }
  ```
- 処理の流れは以下
  1. 撮影用ページ(capture.html)でレシートを撮影し、バックエンドに送る
  2. OpenAI APIを使用して、バックエンドで解析し、結果を確認用ページに送る
       - バックエンド→確認用ページは、WebSocketを使う
  3. 確認用ページ(review.html)で確認したのち、バックエンドに送り、結果を保存する
- gpt-4oにつくらせた。プロンプトは以下の通り
  ```plaintext
  レシート画像を整理するツールを作成します。以下のような構成で作成してください。
  ----
  スマホで撮影する
  　HTML, JSで実装する
  　input type="file"で撮影する
  　撮影した画像を、バックエンドに送信する
  バックエンドで処理する
  　PythonのFastAPIで実装する
  　POSTされた画像をOpenAI APIで処理し、レシートの情報をJSONにする
  　　(ここは私が実装します。# TODO と印をつけておいてください)
  　　shop, datetime, items, total_price, payment_methodの要素があるJSONが生成される
  　処理結果(画像、JSON化された情報)を確認画面に送る
  　　websocketで、サーバーから送る
  確認画面で確認・修正する
  　HTML, JSで実装する
  　これはスマホとは別端末(PCなど)で動かす
  　　バックエンドのPythonが動いている端末かな
  　WebSocketで送られてきた結果を表示する
  　　左に画像、右にJSON(textareaに)を表示する
  　textareaの一番下に「保存する」ボタンを設置する
  　　入力されたJSONが正しい形式か(parseできるか)を判断する
  　　このボタンが押されたら、画像とJSONをバックエンドに送る
  バックエンドでデータを保存する
  　画像・JSONのファイル名は、「{購入日時}-{店名}」とする
  　　これらのデータはJSONから抽出する
  　POSTされた画像・JSONを、上記のファイル名で保存する
  ```