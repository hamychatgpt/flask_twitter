from flask_admin import BaseView, expose
from flask import redirect, url_for, request, flash
from flask_login import current_user, login_required
from ..collector.service import CollectorService

class CollectorView(BaseView):
    """نمای سفارشی برای فرآیند جمع‌آوری"""
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    @expose('/')
    def index(self):
        return self.render('admin/collector.html')
    
    @expose('/keyword', methods=['POST'])
    @login_required
    def collect_keyword(self):
        """جمع‌آوری براساس کلمه کلیدی"""
        keyword = request.form.get('keyword')
        max_tweets = request.form.get('max_tweets', 100, type=int)
        
        if not keyword:
            flash('لطفاً کلمه کلیدی را وارد کنید', 'error')
            return redirect(url_for('.index'))
        
        # ایجاد نمونه سرویس جمع‌آوری
        service = CollectorService()
        
        # انجام جمع‌آوری
        try:
            collection, count = service.collect_by_keyword(keyword, max_tweets)
            flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        except Exception as e:
            flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
        
        return redirect(url_for('.index'))
    
    @expose('/username', methods=['POST'])
    @login_required
    def collect_username(self):
        """جمع‌آوری براساس نام کاربری"""
        username = request.form.get('username')
        max_tweets = request.form.get('max_tweets', 100, type=int)
        
        if not username:
            flash('لطفاً نام کاربری را وارد کنید', 'error')
            return redirect(url_for('.index'))
        
        # حذف @ از ابتدای نام کاربری در صورت وجود
        if username.startswith('@'):
            username = username[1:]
        
        # ایجاد نمونه سرویس جمع‌آوری
        service = CollectorService()
        
        # انجام جمع‌آوری
        try:
            collection, count = service.collect_by_username(username, max_tweets)
            flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        except Exception as e:
            flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
        
        return redirect(url_for('.index'))