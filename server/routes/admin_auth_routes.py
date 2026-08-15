from flask import Blueprint,jsonify,request,session
from ..db.admin_repository import repository,current_admin
admin_auth_api=Blueprint('admin_auth_api',__name__)
@admin_auth_api.post('/login')
def login():
 p=request.get_json(silent=True) or {};admin=repository.authenticate(str(p.get('email','')).strip().lower(),str(p.get('password','')))
 if not admin:return jsonify({'error':'管理员账号或密码不正确。'}),401
 session.clear();session['admin_id']=admin['id'];return jsonify({'admin':admin})
@admin_auth_api.post('/logout')
def logout():session.clear();return jsonify({'ok':True})
@admin_auth_api.get('/me')
def me():
 admin=current_admin(session);return (jsonify({'admin':admin}),200) if admin else (jsonify({'admin':None}),401)
