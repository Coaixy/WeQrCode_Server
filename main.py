import uvicorn
import hashlib
import config
import vercel_kv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = vercel_kv.KVConfig(
    url=config.url,
    rest_api_url=config.rest_api_url,
    rest_api_token=config.rest_api_token,
    rest_api_read_only_token=config.rest_api_read_only_token,
)
kv = vercel_kv.KV(config)


def md5_hash(text):
    text = text + "WeQrCode"
    hash = hashlib.md5()
    hash.update(text.encode("utf-8"))
    return hash.hexdigest()


class create_item(BaseModel):
    uuid: str
    wxUrl: str
    auth: str


class change_item(BaseModel):
    token: str
    key: str
    wxUrl: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/test")
async def test():
    return {kv.set("test", "ok")}


@app.post("/create")
def create(item: create_item):
    print(item)
    if item.auth != "coaixy":
        return {"code": "201", "data": "暂未向外开放"}
    if kv.get(item.uuid) is None:
        key = md5_hash(item.uuid)
        kv.set(item.uuid, item.wxUrl.replace("/", "!!"))
        kv.set(f"pwd_{item.uuid}", key)
        return {"code": 200, "data": key}
    else:
        return {"code": 200, "data": "Token已存在"}


@app.post("/change")
async def change(item: change_item):
    print(item)
    code = 400
    if kv.get(item.token) is None:
        code = 201
    elif kv.get(f"pwd_{item.token}") == item.key:
        kv.set(item.token, item.wxUrl.replace("/", "!!"))
        code = 200
    else:
        code = 202

    return {"code": code}


@app.get("/get_url")
async def get_url(token: str = ""):
    print(token)
    if kv.get(token) is not None:
        return {"url": kv.get(token).replace("!!", "/")}
    else:
        return {"url": ""}

