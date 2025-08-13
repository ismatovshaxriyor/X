from peewee import (
    SqliteDatabase, Model, TextField, IntegerField, DateTimeField,
    BooleanField, ForeignKeyField, AutoField, BigIntegerField, CharField
)
from datetime import datetime
import os

DB_PATH = os.path.join("database", "main.db")
database = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = database

class Gift(BaseModel):
    id = BigIntegerField(primary_key=True)
    sticker_path = CharField(null=True)
    stars = IntegerField()
    limited = BooleanField(default=False)
    timestamp = DateTimeField(default=datetime.now)
    status = CharField(default="old") # "old" / "new"
    sold_out = BooleanField()
    first_sale_date = DateTimeField(null=True)
    last_sale_date = DateTimeField(null=True)


class User(BaseModel):
    user_id = AutoField()
    telegram_id = IntegerField(unique=True, null=True)
    username = TextField(null=True)
    first_name = TextField(null=True)
    stars = IntegerField(default=0, null=True)
    is_premium = BooleanField(default=False, null=True)
    is_monitoring_active = BooleanField(default=False, null=True)
    min_stars = IntegerField(null=True)  
    max_stars = IntegerField(null=True)  
    is_agree = BooleanField(default=False)
    gift_limit = IntegerField(null=True)
    send_to = TextField(null=True, default='user') # "user" / "channel" / "user_and_channel"
    joined_at = DateTimeField(default=datetime.now)


class Transactions(BaseModel):
    user = ForeignKeyField(User, backref="tr_user")
    gift = ForeignKeyField(Gift, backref="tr_gift")
    timestamp = DateTimeField(default=datetime.now)
    status = TextField()  # 'FAILED' / 'PURCHASED'
    stars = IntegerField()

class Payment(BaseModel):
    id = AutoField() 
    user = ForeignKeyField(User, backref='user')
    telegram_payment_charge_id = CharField(unique=True, null=True)
    invoice_payload = CharField()
    status = TextField() # "SUCCESS" / "REFUNDED" / "FAILED" / "FAILED_REFUND"
    currency = CharField()
    amount = IntegerField()
    timestamp = DateTimeField(default=datetime.now)

class Channels(BaseModel):
    user = ForeignKeyField(User, backref='user')
    channel_name = TextField()
    channel_id = IntegerField()
    gift_limit = IntegerField(null=True)