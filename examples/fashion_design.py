import re

import requests
import os
from pydantic import BaseModel
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from zhipuai import ZhipuAI
from search_test import FashionResearcher

client = ZhipuAI(api_key="91cd07dc14064e98a425cda376696eb3.5GbNHBEr6u0g0nIH")

class input(BaseModel):
    inform: dict[str, str] = None
    content: str = ""

DIRECTORY_STRUCTION_FA = """
你现在是一个时尚分析员,请你根据总结的网页信息对相关领域的时尚趋势进行分析
"""
Content_FA = """
信息如下
{require}

对于这个要求
1.输出语言为中文，专有名词可用原语种
2.请根据信息你分析时尚的趋势，给出一些时尚的搭配
3.总结的信息可能存在语意不通的情况，请根据全文适当总结，提取精华
2.可以分段进行回答，说出“具体会穿什么款式衣服，以什么颜色为主”
3.大概,400字左右，语言精炼
4.不要有空格
"""

# 实例化一个ActionNode，输入对应的参数
DIRECTORY_WRITE_FA = ActionNode(
    # ActionNode的名称
    key="Partition",
    # 期望输出的格式
    expected_type=str,
    # 命令文本
    instruction=DIRECTORY_STRUCTION_FA,
    # 例子输入，在这里我们可以留空
    example="2025年女装搭配潮流中，流行款式和颜色呈现出多样化特点。款式方面，中长款西服与短裤搭配，简约且优雅；箱型外套以宽松廓形和直线线条为主，舒适又具层次感。此外，流苏元素成为春夏系列的亮点，可搭配牛仔布或铅笔裙，展现俏皮与优雅。颜色上，摩卡慕斯色调偏粉，与蓝色系搭配能营造复古感；灰玫瑰红融合高贵与内敛，适合展现都市女性的自信。整体风格强调个性化与视觉冲击力，极繁主义回归，色彩对比强烈。",
)

DIRECTORY_STRUCTION_SU = """
你现在是一位总结员,请你根据传入的信息总结一套有代表性的搭配
"""
Content_SU = """
需求如下
{topic}
信息如下
{information}

对于这个要求
1.输出语言为中文
2.对传入的信息进行总结思考选择出一套搭配，注意明确性别、服装种类、服装颜色。如：一位女士穿着宽松廓形外套，颜色为摩卡慕斯色，搭配浅蓝色短裤
3.如果需求是类似于头饰、配饰等细节，请将描述放在头饰、配饰等细节上，可以不给出详细服装搭配，如：一位大学男生面试时选择经典短发，两侧修剪整齐，顶部稍长并自然梳理。
4.一句话概括，突出需要的主体
5，请注意需求中提到角色的身份和行为请在结果中体现出来
6.不要有空格和换行
"""

# 实例化一个ActionNode，输入对应的参数
DIRECTORY_WRITE_SU = ActionNode(
    # ActionNode的名称
    key="FashionSum",
    # 期望输出的格式
    expected_type=str,
    # 命令文本
    instruction=DIRECTORY_STRUCTION_SU,
    # 例子输入，在这里我们可以留空
    example="一位女士穿着宽松廓形外套，颜色为摩卡慕斯色，搭配浅蓝色短裤",
)


class FashionAna(Action):
    async def run(self, require: str, *args, **kwargs):
        prompt = Content_FA.format(require=require)
        resp_node = await DIRECTORY_WRITE_FA.fill(context=prompt, llm=self.llm, schema="raw")
        # # 选取ActionNode.content，获得我们期望的返回信息
        resp = resp_node.content
        # print(type(resp))
        # print(resp)
        return resp


class FashionSum(Action):
    async def run(self, topic, information: str, *args, **kwargs):
        prompt = Content_SU.format(topic=topic, information=information)
        resp_node = await DIRECTORY_WRITE_SU.fill(context=prompt, llm=self.llm, schema="raw")
        # # 选取ActionNode.content，获得我们期望的返回信息
        resp = resp_node.content
        return resp


class Fashioner(Role):
    name: str = "Fashioner"
    profile: str = "analyze"
    story: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([FashionAna])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        require = self.get_memories(k=1)[0]
        resp = await todo.run(require=require)
        return resp


class FashionerSum(Role):
    name: str = "FashionerSum"
    profile: str = "Sum"
    story: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([FashionSum])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        information = self.get_memories(k=1)[0]
        information = information.instruct_content.inform
        resp = await todo.run(topic=information["topic"], information=information["content"])
        return resp


class WriteContentWithActionNode(Action):
    Prompt: str = """
{content}
"""

    async def run(self, content: str, *args, **kwargs) -> str:
        prompt = self.Prompt.format(content=content)
        print(prompt)
        response = client.images.generations(
            model="cogview-3-flash",  # 填写需要调用的模型名称
            prompt=prompt,
        )
        print(response.data[0].url)
        return response.data[0].url


class TutorialAssistantWithActionNode(Role):
    name: str = "Stitch"
    profile: str = "Tutorial Assistant"
    topic: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteContentWithActionNode()])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> str:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]
        resp = await todo.run(content=msg.content)
        print(type(resp))
        print(resp)
        return resp


def Download(name, url):
    r = requests.get(url)
    folder_path = "./illustration"  # 指定文件夹路径
    file_name = name  # 文件名

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, file_name)  # 构建完整的文件路径
    with open(file_path, "wb") as f:
        f.write(r.content)


if __name__ == "__main__":
    import asyncio

    async def main(require):
        role1 = FashionResearcher()
        information = await role1.run(require)
        # print(type(return_code))
        role2 = FashionerSum()
        my_dict = {"topic": information.instruct_content.topic, "content": information.instruct_content.content}
        res = await role2.run(Message(content="", instruct_content=input(inform=my_dict)))
        role3 = TutorialAssistantWithActionNode()
        link = await role3.run(res)
        prompt = "时尚图示.png"
        Download(prompt, link)
        return res

    # Pass the story here
    require = "女生推荐"
    asyncio.run(main(require))
