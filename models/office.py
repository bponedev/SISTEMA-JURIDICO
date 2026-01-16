from database import db

class Office(db.Model):
    __tablename__ = 'offices'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True)

    clients = db.relationship('Client', backref='office', lazy=True)

    def __repr__(self):
        return f'<Office {self.code} - {self.name}>'
