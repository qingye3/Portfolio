import time

__author__ = 'qingye3'

from flask import render_template, Flask, session, request
from datamodel import app
import datetime
import datamodel
import base64
import pygithub3
import profanity_filter
import jinja2
db = datamodel.db


def get_projects_dict(projects):
    """
    return a dictionary of with the name of the project as keys and dispaly name of hte project
    as value
    :param projects: list of Project model
    :return: dictionary
    """
    ret = dict()
    for project in projects:
        ret[project.name] = project.display_name
    return ret


def get_commit_names(head_commit):
    """
    :param head_commit:
    :return: list of tuple of (hash_of_commit, short_hash_of_commit)
    """
    ret = list()
    commit = head_commit
    ret.append((commit.hexsha, commit.hexsha[:6]))
    while commit.parent_nodes():
        commit = commit.parent_nodes()[0]
        ret.append((commit.hexsha, commit.hexsha[:6]))
    return ret


def int_to_strftime(gmtime):
    """
    :param gmtime: a gmttime struct
    :return: string in proper format
    """
    return time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(gmtime))


def get_commit_info(commit_model):
    """
    :param commit_model: Commit mode
    :return: dictionary of commit information
    """
    ret = dict()
    ret["hash"] = commit_model.hexsha[:7]
    ret["message"] = commit_model.message
    ret["author_name"] = commit_model.author_name
    ret["author_email"] = commit_model.author_email
    ret["authored_date"] = int_to_strftime(commit_model.authored_date)
    return ret


def get_project_info(project_model):
    """
    :param project_model: Project model
    :return: dictionary of project information
    """
    ret = dict()
    ret["repo_url"] = project_model.repo_url
    ret["name"] = project_model.name
    ret["display_name"] = project_model.display_name
    ret["date"] = int_to_strftime(project_model.date)
    ret["message"] = project_model.message
    return ret


def get_tree_table(root, result, depth=0):
    """
    :param root: root of Tree model
    :param result: where to store the result
    :param depth: current depth
    :return:
    """
    for tree in [d for d in root.children if not d.is_dir]:
        result.append((tree.name,
                       tree.hexsha,
                       tree.is_dir,
                       tree.size))
    for tree in [d for d in root.children if d.is_dir]:
        result.append(("+" * depth +
                       tree.name,
                       tree.hexsha,
                       tree.is_dir,
                       tree.size))
        get_tree_table(tree, result, depth + 1)


@app.route("/Source/<repo_name>/<source_hash>", methods=['GET'])
def source(repo_name, source_hash):
    """
    endpoint for displaying source code
    """
    gh = pygithub3.Github(user="qingye3", repo=repo_name)
    return render_template("sourcecode.html",
                           title=repo_name,
                           content=base64.b64decode(gh.git_data.blobs.get(source_hash).content))


def filter(input):
    """
    :param input: string
    :return: filtered text free of red words and XSS attack
    """
    clean_input = profanity_filter.filter(input)
    return clean_input


def submit_comment(author, content):
    """
    save a comment to the DB
    :param author: name of author
    :param content:  content of coment
    :return:
    """
    comment = datamodel.Comment(author=filter(author), content=filter(content), date=datetime.datetime.now())
    datamodel.db.session.add(comment)
    datamodel.db.session.commit()


def get_comments():
    """
    get all comment from the db
    :return: list of tuple ordered in date of format(author, content, date)
    """
    ret = []
    for comment in datamodel.Comment.query.order_by(datamodel.Comment.date).all():
        ret.append((comment.author, comment.content, str(comment.date)))
    print ret
    return ret



@app.route("/Project/<project_name>", methods=['GET', 'POST'])
def project(project_name):
    project_model = datamodel.Project.query.filter_by(name=project_name).first_or_404()

    # default to first commit
    if request.method == "GET":
        commit_hash = project_model.head_hexsha
    if request.method == "POST":
        # check if the form is from clicking one of the commit or from submitting a comment
        if "commit" in request.form:
            commit_hash = request.form["commit"]
        else:
            commit_hash = project_model.head_hexsha
            submit_comment(request.form["comment_author"], request.form["comment_content"])

    # getting information from the db
    projects = datamodel.Project.query.all()
    commit_model = datamodel.Commit.query.filter_by(hexsha=commit_hash).first_or_404()
    head_commit = datamodel.Commit.query.filter_by(hexsha=project_model.head_hexsha).first_or_404()
    commit_info = get_commit_info(commit_model)
    tree_table = list()
    tree_model = datamodel.Tree.query.filter_by(commit=commit_model).first_or_404()
    get_tree_table(tree_model, tree_table)

    return render_template("project.html",
                           project_name=project_model.display_name,
                           project_info=get_project_info(project_model),
                           projects_dict=get_projects_dict(projects),
                           comments=get_comments(),
                           commit_names=get_commit_names(head_commit),
                           commit_info=commit_info,
                           tree_table=tree_table)

if __name__ == "__main__":
    app.run()
    app.debug = True
