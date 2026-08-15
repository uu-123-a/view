"""基于用户求职数据的讯飞星火职业助手。"""
import json

from .spark_service import SparkService


class CareerService:
    def __init__(self):self.spark=SparkService()

    @staticmethod
    def fallback(question:str,context:dict)->str:
        role=(context.get("plan") or {}).get("target_role") or "目标岗位"
        weak="、".join(item["skill"] for item in context.get("mistakes",[])[:3]) or "结构化表达"
        return f"针对{role}，建议先完成三步：第一，梳理简历中最相关的两个项目并量化结果；第二，围绕{weak}进行专项练习；第三，根据最近面试报告逐项复盘。你问的是“{question[:80]}”，可以先把目标拆成一周内可完成的行动，再根据练习结果调整。"

    def answer(self,question:str,context:dict,messages:list[dict])->tuple[str,str]:
        system=f'''你是 MOSS AI 职业教练。根据用户真实数据回答中文求职问题，建议必须具体、可执行，不得编造经历，不得承诺录用。用户上下文：{json.dumps(context,ensure_ascii=False)}'''
        history=[{"role":"user" if item["role"]=="user" else "assistant","content":item["content"]} for item in messages[-8:]]
        try:return self.spark.chat([{"role":"user","content":system},*history,{"role":"user","content":question}],temperature=.45,max_tokens=1500,uid="career-assistant"),"spark"
        except Exception:return self.fallback(question,context),"fallback"

