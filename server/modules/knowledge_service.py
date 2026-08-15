"""从岗位、简历、报告和错题构建个人能力图谱。"""
import json
import sqlite3

from ..db.user_repository import DATABASE_PATH


ROLE_PATHS={
    "大模型":[("Python","基础"),("Transformer","核心"),("模型微调","核心"),("RAG","应用"),("模型评测","工程"),("部署监控","工程")],
    "多模态":[("Python","基础"),("PyTorch","基础"),("计算机视觉","核心"),("Transformer","核心"),("多模态","应用"),("模型部署","工程")],
    "后端":[("Python","基础"),("Flask","框架"),("MySQL","数据"),("Redis","数据"),("Docker","工程"),("系统设计","进阶")],
    "前端":[("JavaScript","基础"),("TypeScript","基础"),("React","框架"),("Vue","框架"),("可视化","应用"),("性能优化","进阶")],
}


class KnowledgeService:
    @staticmethod
    def _connect():
        connection=sqlite3.connect(DATABASE_PATH,timeout=15);connection.row_factory=sqlite3.Row;return connection

    def build(self,user_id:int)->dict:
        with self._connect() as connection:
            plan=connection.execute("SELECT target_role,focus_skill FROM training_plans WHERE user_id=?",(user_id,)).fetchone()
            resume=connection.execute("SELECT analysis_json,content FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 1",(user_id,)).fetchone()
            reports=connection.execute("""SELECT r.report_json,r.score FROM interview_reports r JOIN interview_sessions s ON s.id=r.session_id
                WHERE s.user_id=? ORDER BY r.created_at DESC LIMIT 5""",(user_id,)).fetchall()
            mistakes=connection.execute("SELECT skill,COUNT(*) count,ROUND(AVG(best_score)) score FROM mistake_book WHERE user_id=? AND resolved=0 GROUP BY skill",(user_id,)).fetchall()
            saved=connection.execute("""SELECT j.title,j.skills_json FROM saved_jobs s JOIN jobs j ON j.id=s.job_id WHERE s.user_id=? ORDER BY s.created_at DESC LIMIT 1""",(user_id,)).fetchone()
        role=(plan["target_role"] if plan else None) or (saved["title"] if saved else None) or "通用技术岗位"
        path=next((value for key,value in ROLE_PATHS.items() if key.lower() in role.lower()),[("技术基础","基础"),("项目表达","表达"),("问题分析","通用"),("系统设计","进阶"),("工程实践","工程")])
        required=[name for name,_ in path]
        if saved:
            for skill in json.loads(saved["skills_json"]):
                if skill not in required:path.append((skill,"岗位要求"));required.append(skill)
        resume_skills=[]
        if resume:
            analysis=json.loads(resume["analysis_json"] or "{}")
            resume_skills=[str(x) for x in analysis.get("skills",[])]
            content=resume["content"].lower()
        else:content=""
        weak={row["skill"]:int(row["score"] or 55) for row in mistakes}
        report_score=round(sum(row["score"] for row in reports)/len(reports)) if reports else 0
        nodes=[]
        for index,(name,category) in enumerate(path):
            matched=name.lower() in content or any(name.lower()==skill.lower() for skill in resume_skills)
            weak_score=next((score for skill,score in weak.items() if skill in name or name in skill),None)
            score=weak_score if weak_score is not None else (82 if matched else (report_score if report_score else 45))
            status="mastered" if score>=75 else "learning" if score>=55 else "recommended"
            nodes.append({"id":index+1,"name":name,"category":category,"score":max(0,min(100,score)),"status":status,"question":f"请结合真实项目，说明你如何应用{name}解决问题，并分析技术取舍。"})
        links=[{"from":nodes[i]["id"],"to":nodes[i+1]["id"]} for i in range(len(nodes)-1)]
        mastered=sum(node["status"]=="mastered" for node in nodes)
        return {"role":role,"focus_skill":plan["focus_skill"] if plan else "结构化表达","nodes":nodes,"links":links,"coverage":round(mastered*100/max(1,len(nodes))),"summary":{"mastered":mastered,"learning":sum(n["status"]=="learning" for n in nodes),"recommended":sum(n["status"]=="recommended" for n in nodes)}}

