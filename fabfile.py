from fabric.contrib.files import exists
from fabric.api import local, settings
from fabric.context_managers import cd
from fabric.operations import sudo, run


class FabricException(Exception):
    pass


REPO_URL = "https://github.com/rhawiz/instabot.git"


def deploy():
    site_folder = "~"
    source_folder = site_folder + "/instabot"
    container_name = "instabot"
    _get_latest_source(source_folder)
    _build_docker_image(source_folder)
    _stop_docker_container(container_name)
    _remove_docker_container(container_name)
    _run_docker_container()


def _get_latest_source(source_folder):
    if exists(source_folder + "/.git"):
        sudo("cd {} && git fetch".format(source_folder))
    else:
        sudo("git clone -b dev {} {}".format(REPO_URL, source_folder))
    current_commit = local("git log -n 1 --format=%H", capture=True)
    sudo("cd {} && git reset --hard {}".format(source_folder, current_commit))


def _update_virtualenv(virtualenv_folder, source_folder):
    sudo("{}/bin/pip install -r {}/requirements.txt".format(virtualenv_folder, source_folder))


def _stop_docker_container(container_name):
    with settings(abort_exception=FabricException):
        try:
            sudo("docker stop {}".format(container_name))
        except FabricException:
            pass


def _remove_docker_container(container_name):
    with settings(abort_exception=FabricException):
        try:
            sudo("docker rm {}".format(container_name))
        except FabricException:
            pass


def _build_docker_image(source_folder):
    with cd(source_folder):
        sudo("docker build -t instabot:latest .")


def _run_docker_container():
    command = """
    docker run -d -p 80:80
    --name instabot
    --restart always
    --volume ~/instabot:/app/
    instabot
    """.replace("\n", " ")
    sudo(command)
