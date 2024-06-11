from . import db
from sqlalchemy import Integer, String, ForeignKey, PickleType, LargeBinary, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from flask_login import UserMixin
from typing import List
import datetime

# user credential model
class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    histories: Mapped[List['History']] = relationship(cascade='all, delete-orphan')

# history model
class History(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    probs: Mapped[list] = mapped_column(PickleType, nullable=False)
    highest_prob: Mapped[float] = mapped_column(Float, nullable=False)
    pred: Mapped[str] = mapped_column(String, nullable=False)
    image: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=func.current_timestamp())