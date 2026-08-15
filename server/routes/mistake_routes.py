from flask import Blueprint,jsonify,request,session
from ..db.mistake_repository import MistakeRepository
from ..modules.interview_service import InterviewService
mistake_api=Blueprint('mistake_api',__name__);repo=MistakeRepository();evaluator=InterviewService()
def uid():
 value=session.get('user_id');return value if isinstance(value,int) else None
@mistake_api.get('')
def items():
 user_id=uid()
 if user_id is None:return jsonify({'error':'请先登录。'}),401
 return jsonify({'items':repo.list(user_id,request.args.get('skill',''))})
@mistake_api.post('/<int:mistake_id>/retry')
def retry(mistake_id):
 user_id=uid()
 if user_id is None:return jsonify({'error':'请先登录。'}),401
 item=repo.get(user_id,mistake_id);answer=str((request.get_json(silent=True) or {}).get('answer','')).strip()
 if item is None:return jsonify({'error':'错题不存在。'}),404
 if len(answer)<10:return jsonify({'error':'请至少输入 10 个字符的回答。'}),400
 evaluation=evaluator._evaluate_answer({'session_id':f'mistake-{mistake_id}','role':'专项复盘','level':'自适应','interview_type':'错题重答'},item['question'],answer)
 repo.retry(user_id,mistake_id,answer,evaluation)
 return jsonify({'evaluation':evaluation,'item':repo.get(user_id,mistake_id)})
