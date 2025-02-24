from fastapi import FastAPI, Form, WebSocket, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
import shutil
import os
import json
import base64
import re
from openai import OpenAI

import uvicorn
from Variables import Variables

app = FastAPI()
review_websocket = None

# ---OpenAI APIの設定
client = OpenAI(api_key=Variables.OPENAI_API_KEY)
SYSTEM_PROMPT = """
レシートの画像が与えられます。これを注意深く分析し、以下のようなJSON形式で情報を抽出してください。なお、「```json」は不要です。出力に含めないでください。
---
{
  "shop":"{店名}",
  "datetime":"{日時(YYYYMMDD_HHMMss)}",
  "items":[
    {
      "name":"{商品名}" 
      "amount":{個数},
      "price":{値段},
      "tax_rate":{税率}
    },
    ...
  ],
  "total_price":"{合計金額}",
  "payment_method":"{支払い方法}",
}
""".strip()

# ---保存先ディレクトリの作成
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------
# ---HTMLの読み込み
# ----------
with open("capture.html", encoding="utf-8") as f:
    CAPTURE_HTML = f.read()
with open("review.html", encoding="utf-8") as f:
    REVIEW_HTML = f.read()


# ----------
# ---HTMLの表示
# ----------
@app.get("/capture/", response_class=HTMLResponse)
def capture():
    return HTMLResponse(content=CAPTURE_HTML)


@app.get("/review/", response_class=HTMLResponse)
def review():
    return HTMLResponse(content=REVIEW_HTML)


# ----------
# ---画像のアップロード
# ----------
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    global review_websocket
    file_contents = await file.read()
    base64_image = base64.b64encode(file_contents).decode("utf-8")

    # ---OpenAI APIを使用してレシートを解析し、JSONを生成する
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    }
                ],
            },
        ],
    )
    response_text = response.choices[0].message.content
    print(response_text)
    response_json = json.loads(response_text)
    receipt_data = response_json

    if review_websocket:
        await review_websocket.send_json({"image": base64_image, "data": receipt_data})

    return JSONResponse(content={"message": "Data processed and sent via WebSocket."})


@app.websocket("/ws/review/")
async def websocket_endpoint(websocket: WebSocket):
    global review_websocket
    await websocket.accept()
    review_websocket = websocket
    await websocket.send_json({"message": "WebSocket connection established."})

    while True:
        data = await websocket.receive_json()
        print(data)


@app.post("/save/")
async def save_data(file: UploadFile = File(...), json_data: str = Form()):
    # ---json_dataの解析
    data = json.loads(json_data)
    datetime = data["datetime"]
    shop_name = data["shop"]
    filename = f"{datetime}-{shop_name}"
    filename = re.sub(r'[\/:*?"<>|]', "", filename)

    # ---画像の保存
    image_path = os.path.join(UPLOAD_DIR, f"{filename}.jpg")
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ---JSONの保存
    json_path = os.path.join(UPLOAD_DIR, f"{filename}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return {"message": "Data saved successfully."}


if __name__ == "__main__":
    uvicorn.run(app, host=Variables.IP_ADDRESS, port=8000, log_level="debug")
