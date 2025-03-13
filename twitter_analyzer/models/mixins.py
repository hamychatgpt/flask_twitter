from datetime import datetime
from . import db

class CRUDMixin:
    """
    میکسین افزودن عملیات CRUD به همه مدل‌ها
    """
    @classmethod
    def create(cls, **kwargs):
        """ایجاد یک نمونه جدید و ذخیره آن در دیتابیس"""
        instance = cls(**kwargs)
        return instance.save()
        
    def update(self, commit=True, **kwargs):
        """به‌روزرسانی چندین فیلد با یک فراخوانی"""
        for attr, value in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, value)
        if commit:
            return self.save()
        return self
        
    def save(self, commit=True):
        """ذخیره نمونه در دیتابیس"""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self
        
    def delete(self, commit=True):
        """حذف نمونه از دیتابیس"""
        db.session.delete(self)
        if commit:
            db.session.commit()
        return self

class TimestampMixin:
    """
    میکسین افزودن فیلدهای timestamp به مدل‌ها
    """
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)