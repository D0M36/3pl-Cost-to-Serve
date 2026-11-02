import json,os,uuid
from sqlalchemy import create_engine,text

URL=os.getenv('DATABASE_URL','sqlite:///extolla_cts.db')
engine=create_engine(URL,pool_pre_ping=True)
with engine.begin() as conn:
    conn.execute(text('CREATE TABLE IF NOT EXISTS models (id VARCHAR(80) PRIMARY KEY, name TEXT NOT NULL, payload TEXT NOT NULL)'))

def all_models():
    with engine.connect() as c:return [dict(x._mapping) for x in c.execute(text('SELECT id,name FROM models ORDER BY name')).fetchall()]

def save(model,id=None):
    id=id or uuid.uuid4().hex
    with engine.begin() as c:
        c.execute(text('DELETE FROM models WHERE id=:id'),{'id':id})
        c.execute(text('INSERT INTO models (id,name,payload) VALUES (:id,:name,:payload)'),{'id':id,'name':model.get('name','Untitled'),'payload':json.dumps(model)})
    return id

def load(id):
    with engine.connect() as c:r=c.execute(text('SELECT payload FROM models WHERE id=:id'),{'id':id}).scalar()
    return json.loads(r) if r else None
