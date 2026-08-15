"""学习知识图谱接口。"""


class KnowledgeGraph:
    def recommend(self, weak_skills: list[str]) -> list[dict]:
        return [{"skill": skill, "resources": []} for skill in weak_skills]
