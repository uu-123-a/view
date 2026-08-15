from flask import Blueprint,jsonify,request,session
from ..db.training_plan_repository import TrainingPlanRepository
training_plan_api=Blueprint('training_plan_api',__name__);repo=TrainingPlanRepository()
def uid():
 value=session.get('user_id');return value if isinstance(value,int) else None
@training_plan_api.get('')
def get_plan():
 user_id=uid()
 if user_id is None:return jsonify({'error':'请先登录。'}),401
 return jsonify(repo.get(user_id))
@training_plan_api.put('')
def save_plan():
 user_id=uid()
 if user_id is None:return jsonify({'error':'请先登录。'}),401
 p=request.get_json(silent=True) or {};role=str(p.get('target_role') or '').strip();skill=str(p.get('focus_skill') or '').strip()
 if not role or not skill:return jsonify({'error':'请填写目标岗位和重点能力。'}),400
 try:return jsonify(repo.save(user_id,role,p.get('weekly_target',3),skill))
 except (ValueError,TypeError):return jsonify({'error':'每周训练次数必须是 1 到 7。'}),400
@training_plan_api.patch('/tasks/<int:task_id>')
def complete(task_id):
 user_id=uid()
 if user_id is None:return jsonify({'error':'请先登录。'}),401
 ok=repo.complete(user_id,task_id,bool((request.get_json(silent=True) or {}).get('completed')))
 return (jsonify({'ok':True,'data':repo.get(user_id)}),200) if ok else (jsonify({'error':'任务不存在。'}),404)
