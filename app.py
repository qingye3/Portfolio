import time

__author__ = 'qingye3'

from flask import render_template, Flask, session, request
from datamodel import app
import datamodel
import base64
import pygithub3


def get_projects_dict(projects):
    ret = dict()
    for project in projects:
        ret[project.name] = project.display_name
    return ret


def get_commit_names(head_commit):
    ret = list()
    commit = head_commit
    ret.append((commit.hexsha, commit.hexsha[:6]))
    while commit.parent_nodes():
        commit = commit.parent_nodes()[0]
        ret.append((commit.hexsha, commit.hexsha[:6]))
    return ret


def int_to_strftime(gmtime):
    return time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(gmtime))


def get_commit_info(commit_model):
    ret = dict()
    ret["hash"] = commit_model.hexsha[:7]
    ret["message"] = commit_model.message
    ret["author_name"] = commit_model.author_name
    ret["author_email"] = commit_model.author_email
    ret["authored_date"] = int_to_strftime(commit_model.authored_date)
    return ret


def get_project_info(project_model):
    ret = dict()
    ret["repo_url"] = project_model.repo_url
    ret["name"] = project_model.name
    ret["display_name"] = project_model.display_name
    ret["date"] = int_to_strftime(project_model.date)
    ret["message"] = project_model.message
    return ret


def get_tree_table(root, result, depth=0):
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
    gh = pygithub3.Github(user="qingye3", repo=repo_name)
    return render_template("sourcecode.html",
                           title=repo_name,
                           content=base64.b64decode(gh.git_data.blobs.get(source_hash).content))


@app.route("/Project/<project_name>", methods=['GET', 'POST'])
def project(project_name):
    project_model = datamodel.Project.query.filter_by(name=project_name).first_or_404()
    if request.method == "GET":
        commit_hash = project_model.head_hexsha
    if request.method == "POST":
        commit_hash = request.form["commit"]
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
                           commit_names=get_commit_names(head_commit),
                           commit_info=commit_info,
                           tree_table=tree_table)

if __name__ == "__main__":
    app.run()
