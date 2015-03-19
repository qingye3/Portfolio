__author__ = 'qingye3'

from flask import render_template, Flask
from datamodel import app
import datamodel


def get_projects_dict(projects):
    ret = dict()
    for project in projects:
        ret[project.name] = project.display_name
    return ret


@app.route("/Project/<project_name>")
def project(project_name):
    project_model = datamodel.Project.query.filter_by(name=project_name).first_or_404()
    projects = datamodel.Project.query.all()
    commit_model = datamodel.Commit.query.filter_by(hexsha=project_model.head_hexsha)

    return render_template("project.html",
                           project_name=project_model.display_name,
                           projects_dict=get_projects_dict(projects))

if __name__ == "__main__":
    app.run()
