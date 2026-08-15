from flask import Blueprint,jsonify,session
from ..db.analytics_repository import AnalyticsRepository
from ..db.admin_repository import current_admin
analytics_api=Blueprint('analytics_api',__name__);repo=AnalyticsRepository()
@analytics_api.get('')
def analytics():
 if not current_admin(session):return jsonify({'error':'仅管理员可以查看数据统计。'}),403
 return jsonify(repo.snapshot())
