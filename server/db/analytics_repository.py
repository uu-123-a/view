"""Read-only aggregate analytics over existing application records."""
import json,sqlite3
from collections import Counter
from .user_repository import DATABASE_PATH

# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class AnalyticsRepository:
 @staticmethod
 def _connect():
  c=sqlite3.connect(DATABASE_PATH,timeout=15);c.row_factory=sqlite3.Row;return c
 def snapshot(self):
  with self._connect() as c:
   users=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
   interviews=c.execute("SELECT COUNT(*) FROM interview_sessions WHERE status='complete' AND mode='interview'").fetchone()[0]
   practices=c.execute("SELECT COUNT(*) FROM interview_sessions WHERE status='complete' AND mode='practice'").fetchone()[0]
   avg=c.execute("SELECT COALESCE(ROUND(AVG(score),1),0) FROM interview_reports").fetchone()[0]
   sources=c.execute("SELECT source,COUNT(*) n FROM interview_turns GROUP BY source").fetchall()
   daily=c.execute("SELECT substr(COALESCE(completed_at,created_at),1,10) day,COUNT(*) n FROM interview_sessions WHERE status='complete' AND COALESCE(completed_at,created_at)>=date('now','-13 days') GROUP BY day ORDER BY day").fetchall()
   reports=c.execute("SELECT report_json FROM interview_reports ORDER BY created_at DESC LIMIT 300").fetchall()
   roles=c.execute("SELECT role,COUNT(*) n FROM interview_sessions WHERE status='complete' GROUP BY role ORDER BY n DESC LIMIT 8").fetchall()
  source={r['source']:r['n'] for r in sources};total=sum(source.values()) or 1
  weak=Counter()
  for r in reports:
   try:
    for item in json.loads(r['report_json']).get('weak_skills',[]): weak[str(item.get('name','未知'))]+=1
   except (json.JSONDecodeError,AttributeError):pass
  days={r['day']:r['n'] for r in daily}
  from datetime import date,timedelta
  trend=[{'date':(date.today()-timedelta(days=i)).isoformat(),'count':days.get((date.today()-timedelta(days=i)).isoformat(),0)} for i in range(13,-1,-1)]
  return {'summary':{'users':users,'interviews':interviews,'practices':practices,'average_score':avg,'spark_rate':round(source.get('spark',0)*100/total,1),'bank_rate':round(source.get('question_bank',0)*100/total,1)},'daily':trend,'sources':[{'name':k,'count':v} for k,v in source.items()],'weak_skills':[{'name':k,'count':v} for k,v in weak.most_common(8)],'roles':[dict(r) for r in roles]}
