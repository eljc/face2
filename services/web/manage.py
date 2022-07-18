from flask.cli import FlaskGroup

from project import app, db, User


cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    print('Limpando o banco')    
    db.drop_all()    
    print('criando as tabelas')
    db.create_all()
    print('Fim')
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    db.session.add(User(email="elder.camara@cidadania.gov.br"))
    db.session.commit()


if __name__ == "__main__":
    cli()
