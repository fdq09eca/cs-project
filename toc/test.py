from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    addresses = relationship("Address", backref='user')

class Address(Base):
    __tablename__ = 'Address'
    id = Column(Integer, primary_key=True)
    email = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))

Base.metadata.create_all()

if __name__ == '__main__':
    session = Session()
    user = User(name = 'Chris')
    session.add(user)
    session.commit()
    c = Address(email = '123@gmail.com',user_id=user.id)
    b = Address(email = 'abc@gmail.com',user_id=user.id)
    session.add(c)
    session.add(b)
    session.commit()
    print(f"addresses: {[address.email for address in user.addresses]}")
    print(f"c.user.name: {c.user.name}")
    print(f"b.user.name: {b.user.name}")