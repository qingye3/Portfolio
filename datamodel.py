__author__ = 'qingye3'


from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["PORTFOLIO_DB_URL"]
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.debug = True

db = SQLAlchemy(app)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    author = db.Column(db.Text)
    content = db.Column(db.Text)


class Tree(db.Model):
    __tablename__ = 'trees'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('trees.id'))
    children = db.relationship("Tree",
                               backref=db.backref('parent',
                                                  remote_side=[id]))
    hexsha = db.Column(db.String(40))
    commit_hexsha = db.Column(db.String(40), db.ForeignKey('commits.hexsha'))
    name = db.Column(db.String(255))
    is_dir = db.Column(db.Boolean)
    size = db.Column(db.BigInteger)


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    display_name = db.Column(db.String(255))
    repo_url = db.Column(db.Text)
    date = db.Column(db.BigInteger)
    message = db.Column(db.Text)
    head_hexsha = db.Column(db.String(40))


class Commit(db.Model):
    __tablename__ = "commits"
    hexsha = db.Column(db.String(40), primary_key=True)
    message = db.Column(db.Text)
    author_name = db.Column(db.String(255))
    author_email = db.Column(db.String(255))
    authored_date = db.Column(db.BigInteger)
    files = db.relationship("Tree",
                            backref=db.backref('commit'),
                            primaryjoin="Commit.hexsha==Tree.commit_hexsha")

    def add_parent(self, node):
        CommitDependency(self, node)
        return self

    def parent_nodes(self):
        return [e.parent_node for e in self.parent_edges]

    def child_nodes(self):
        return [e.child_node for e in self.child_edges]


class CommitDependency(db.Model):
    __tablename__ = "commit_dependencies"
    child_hexsha = db.Column(db.String(40),
                             db.ForeignKey('commits.hexsha'),
                             primary_key=True)
    parent_hexsha = db.Column(db.String(40),
                              db.ForeignKey('commits.hexsha'),
                              primary_key=True)
    child_node = db.relationship(Commit,
                                 primaryjoin=child_hexsha == Commit.hexsha,
                                 backref='parent_edges')
    parent_node = db.relationship(Commit,
                                  primaryjoin=parent_hexsha == Commit.hexsha,
                                  backref='child_edges')

    def __init__(self, child, parent):
        self.child_node = child
        self.parent_node = parent

if __name__ == "__main__":
    db.create_all()
