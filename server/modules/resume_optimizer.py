"""岗位定向简历匹配与星火优化建议。"""
import json
import re

from .spark_service import SparkService


class ResumeOptimizer:
    def __init__(self):self.spark=SparkService()

    @staticmethod
    def _base(resume:dict,job:dict)->dict:
        content=resume.get("content","").lower();matched=[x for x in job["skills"] if x.lower() in content];missing=[x for x in job["skills"] if x not in matched]
        score=round(len(matched)*100/max(1,len(job["skills"])))
        return {"match_score":score,"matched_keywords":matched,"missing_keywords":missing,"suggestions":["把最相关的项目放在前半页，并明确个人职责。","使用数字描述性能、效率或业务结果。","针对岗位要求补充技术取舍、故障定位和上线经验。"],"optimized_summary":resume.get("content","")[:800],"source":"fallback"}

    def optimize(self,resume:dict,job:dict)->dict:
        fallback=self._base(resume,job)
        prompt=f'''你是中文技术招聘专家。根据简历和岗位生成优化结果，只输出合法JSON：{{"match_score":0到100,"matched_keywords":[""],"missing_keywords":[""],"suggestions":[""],"optimized_summary":"优化后的300到600字职业概述与项目亮点"}}。不得编造简历中不存在的经历或数据。\n岗位：{job['title']}\n要求：{job['description']}；技能：{'、'.join(job['skills'])}\n简历：{resume['content'][:10000]}'''
        try:
            raw=self.spark.chat([{"role":"user","content":prompt}],temperature=.2,max_tokens=1800,uid=f"resume-{resume['id']}")
            match=re.search(r"\{.*\}",raw,re.S);data=json.loads(match.group(0)) if match else {}
            return {"match_score":max(0,min(100,int(data.get("match_score",fallback["match_score"])))),"matched_keywords":[str(x)[:30] for x in data.get("matched_keywords",fallback["matched_keywords"])][:15],"missing_keywords":[str(x)[:30] for x in data.get("missing_keywords",fallback["missing_keywords"])][:15],"suggestions":[str(x)[:180] for x in data.get("suggestions",fallback["suggestions"])][:8],"optimized_summary":str(data.get("optimized_summary") or fallback["optimized_summary"])[:3000],"source":"spark"}
        except Exception:return fallback
