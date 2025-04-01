# from builtins import str
# from metagpt.actions import Action
# from metagpt.actions.action_node import ActionNode
# from metagpt.roles.role import Role, RoleReactMode
#
# DIRECTORY_STRUCTION1 = """
# 你现在是一个读者,你要对下方文字进行分割
# """
# Content1 = """
# 故事如下
# {story}
#
# 对于这个故事
# 1.输出语言为中文
# 2.对每句完整的话进行分割,对句号和分段进行分割
# 3.严格按照字典格式进行回答,如{{"partition":[{{"person":[{{"person1","person2}}],"content":"content1"}}]}}
# 4.person为一个存放集合,用于存放这个分段中出现的所有人物
# 5.不要有空格和换行
# """
# # 实例化一个ActionNode，输入对应的参数
# DIRECTORY_WRITE = ActionNode(
#     # ActionNode的名称
#     key="Partition",
#     # 期望输出的格式
#     expected_type=str,
#     # 命令文本
#     instruction=DIRECTORY_STRUCTION1,
#     # 例子输入，在这里我们可以留空
#     example="",
# )
# class Partition(Action):
#     async def run(self, story: str, *args, **kwargs) -> dict:
#         prompt = Content1.format(story=story)
#         resp_node = await DIRECTORY_WRITE.fill(context=prompt, llm=self.llm, schema="raw")
#         # # 选取ActionNode.content，获得我们期望的返回信息
#         resp = resp_node.content
#         dictionary = eval(resp)
#         return dictionary
#
# class PartitionActionNode(Role):
#     name: str = "PartitionActionNode"
#     profile: str = "reader"
#     story: str = ""
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.set_actions([Partition])
#         self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)
#
#     async def _act(self) -> dict:
#         todo = self.rc.todo
#         story = self.get_memories(k=1)[0]
#         resp = await todo.run(story=story.content)
#         return resp
#
#
# if __name__ == "__main__":
#     import asyncio
#
#     async def main(story):
#         role = PartitionActionNode()
#         return_code = await role.run(story)
#         print(type(return_code))
#         print(return_code)
#         return return_code
#
#     # Pass the story here
#     story = "孔融把李让给了哥哥姐姐。"
#     asyncio.run(main(story))

import requests
import os
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from pydantic import BaseModel
from zhipuai import ZhipuAI
from search_test import FashionResearcher

class input(BaseModel):
    inform: dict[str, str] = None
    content: str = ""

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
2.对传入的信息进行总结思考选择出一套搭配，注意明确性别、服装种类、服装颜色
3.一句话概括：谁+身穿什么
4，请注意需求中提到角色的身份和行为请在结果中体现出来
5.描述性的语言例如：一位女士穿着宽松廓形外套，颜色为摩卡慕斯色，搭配浅蓝色短裤
6.如果需求是类似于头饰、配饰等细节，以满足需求为主上不用遵从上面的例子
7.不要有空格和换行
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

class FashionSum(Action):
    async def run(self, topic, information: str, *args, **kwargs):
        prompt = Content_SU.format(topic=topic, information=information)
        resp_node = await DIRECTORY_WRITE_SU.fill(context=prompt, llm=self.llm, schema="raw")
        # # 选取ActionNode.content，获得我们期望的返回信息
        resp = resp_node.content
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

if __name__ == "__main__":
    import asyncio

    async def main(require):
        actio = FashionSum()
        role2 = FashionerSum()
        my_dict = {"topic": require, "content": ""}
        print(my_dict)
        rek = await actio.run(my_dict["topic"], my_dict["content"])
        print(rek)
        res = await role2.run(Message(content="", instruct_content=input(inform=my_dict)))

        return res

    # Pass the story here
    require = "2025年中国大学女生去洗澡"
    asyncio.run(main(require))
