__author__ = 'qingye3'
from datamodel import db, Project, Commit, Tree
from config import projects, local_repo_path
import os
import git


def get_repo_path(repo_name):
    return os.path.join(local_repo_path, repo_name)


def update_temp_repo(repo_url, repo_name):
    """
    updating the temp repo folder in local_repo_path
    The function may not be reliable because GitPython returns incorrect hash/
    clone files in a wrong way.
    TODO: switch to subprocess.Popen a git binary :param repo_url: url of the repo
    :param repo_name: name of the repo
    :return:
    """
    path = get_repo_path(repo_name)
    if os.path.exists(path):
        repo = git.Repo(path)
        repo.remote("origin").pull()
    else:
        # Due to a bug in the git extension, the SHA1 hash may not be
        # be calculated correctly
        # Therefore, manual clone is recommended
        git.Repo.clone_from(repo_url, path)


def insert_projects():
    for p in projects:
        repo = git.Repo(get_repo_path(p["name"]))
        master_commit = repo.heads.master.commit
        project = Project(name=p["name"],
                          display_name=p["display_name"],
                          repo_url=p["repo_url"],
                          message=master_commit.message,
                          date=master_commit.authored_date,
                          head_hexsha=master_commit.hexsha)
        db.session.add(project)
        update_temp_repo(p["repo_url"], p["name"])


def insert_commits_for_proj(repo_path):
    repo = git.Repo(repo_path)
    commit_dict = dict()
    for commit in repo.iter_commits():
        commit_model = Commit(hexsha=commit.hexsha,
                              message=commit.message,
                              author_name=commit.author.name,
                              author_email=commit.author.email,
                              authored_date=commit.authored_date)
        commit_dict[commit.hexsha] = commit_model
    for commit in repo.iter_commits():
        for parent_commit in commit.parents:
            commit_dict[commit.hexsha].add_parent(commit_dict[parent_commit.hexsha])

    for commit in repo.iter_commits():
        db.session.add(commit_dict[commit.hexsha])


def insert_commits():
    for project in projects:
        repo_path = get_repo_path(project["name"])
        insert_commits_for_proj(repo_path)


def add_tree_recursive(tree, commit_model, is_root):
    tree_model = Tree(hexsha=tree.hexsha,
                      commit=commit_model,
                      name=tree.name,
                      is_dir=True,
                      size=0)
    db.session.add(tree_model)
    for blob in tree.blobs:
        blob_model = Tree(hexsha=blob.hexsha,
                          commit=commit_model,
                          parent=tree_model,
                          name=blob.name,
                          is_dir=False,
                          size=blob.size)
        db.session.add(blob_model)


def insert_trees_for_proj(repo_path):
    repo = git.Repo(repo_path)
    commit_dict = dict()
    for commit in repo.iter_commits():
        commit_model = Commit.query.filter_by(hexsha=commit.hexsha).first()
        add_tree_recursive(commit.tree, commit_model, True)


def insert_trees():
    for project in projects:
        repo_path = get_repo_path(project["name"])
        insert_trees_for_proj(repo_path)


if __name__ == "__main__":
    db.drop_all()
    db.create_all()
    db.session.commit()

    insert_projects()
    db.session.commit()

    insert_commits()
    db.session.commit()

    insert_trees()
    db.session.commit()
