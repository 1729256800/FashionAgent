from flask import Flask, request, jsonify, render_template
from fashion_design import FashionerSum, TutorialAssistantWithActionNode, Download
from search_test import FashionResearcher
from metagpt.schema import Message
import asyncio
from pydantic import BaseModel

app = Flask(__name__)

class InputData(BaseModel):
    inform: dict[str, str] = None
    content: str = ""

async def main(require):
    role1 = FashionResearcher()
    information = await role1.run(require)

    role2 = FashionerSum()
    my_dict = {"topic": information.instruct_content.topic, "content": information.instruct_content.content}
    res = await role2.run(Message(content="", instruct_content=InputData(inform=my_dict)))

    role3 = TutorialAssistantWithActionNode()
    link = await role3.run(res)

    prompt = "时尚图示.png"
    Download(prompt, link)

    return {"content": information.instruct_content.content, "image_url": link}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.get_json()
        require = data.get("require")

        if not require:
            return jsonify({"error": "请求参数错误"}), 400

        try:
            # 显式创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(main(require))
            loop.close()

            print("后端返回数据:", result)
            return jsonify(result)

        except Exception as e:
            print("处理请求时出错:", str(e))
            return jsonify({"error": "内部服务器错误"}), 500

    return render_template("index.html")

@app.route("/result")
def result():
    content = request.args.get("content", "暂无推荐")
    image_url = request.args.get("image_url", "")

    print(f"获取参数: content={content}, image_url={image_url}")  # 调试信息

    return render_template("result.html", content=content, image_url=image_url)

if __name__ == "__main__":
    app.run(debug=True, threaded=True)  # 启用多线程模式
