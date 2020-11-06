"""
Release the next version.
"""

import datetime
import os
import subprocess
from pathlib import Path

import docker
from github import Github
from github.ContentFile import ContentFile
from github.Repository import Repository


def get_version(github_repository: Repository) -> str:
    """
    Return the next version.
    This is today’s date in the format ``YYYY.MM.DD.MICRO``.
    ``MICRO`` refers to the number of releases created on this date,
    starting from ``0``.
    """
    utc_now = datetime.datetime.utcnow()
    date_format = '%Y.%m.%d'
    date_str = utc_now.strftime(date_format)
    tag_labels = [tag.name for tag in github_repository.get_tags()]
    today_tag_labels = [
        item for item in tag_labels if item.startswith(date_str)
    ]
    micro = int(len(today_tag_labels))
    new_version = f'{date_str}.{micro}'
    return new_version


def update_changelog(version: str, github_repository: Repository) -> None:
    """
    Add a version title to the changelog.
    """
    changelog_path = Path('CHANGELOG.rst')
    branch = 'master'
    changelog_content_file = github_repository.get_contents(
        path=str(changelog_path),
        ref=branch,
    )
    # ``get_contents`` can return a ``ContentFile`` or a list of
    # ``ContentFile``s.
    assert isinstance(changelog_content_file, ContentFile)
    changelog_bytes = changelog_content_file.decoded_content
    changelog_contents = changelog_bytes.decode('utf-8')
    new_changelog_contents = changelog_contents.replace(
        'Next\n----',
        f'Next\n----\n\n{version}\n------------',
    )
    github_repository.update_file(
        path=str(changelog_path),
        message=f'Update for release {version}',
        content=new_changelog_contents,
        sha=changelog_content_file.sha,
    )


def build_and_upload_to_pypi() -> None:
    """
    Build source and binary distributions.
    """
    for args in (
        ['git', 'fetch', '--tags'],
        ['git', 'merge', 'origin/master'],
        ['rm', '-rf', 'build'],
        ['git', 'status'],
        ['python', 'setup.py', 'sdist', 'bdist_wheel'],
        ['twine', 'upload', '-r', 'pypi', 'dist/*'],
    ):
        subprocess.run(args=args, check=True)

def build_and_publish_docker_images() -> None:
    """
    """
    pass
    repository_root = Path(__file__).parent.parent.parent
    client = docker.from_env()

    dockerfile_dir = repository_root / 'src/mock_vws/_flask_server/dockerfiles'
    base_dockerfile = dockerfile_dir / 'base' / 'Dockerfile'
    target_manager_dockerfile = (
        dockerfile_dir / 'target_manager' / 'Dockerfile'
    )
    vws_dockerfile = dockerfile_dir / 'vws' / 'Dockerfile'
    vwq_dockerfile = dockerfile_dir / 'vwq' / 'Dockerfile'

    base_tag = 'vws-mock:base'
    target_manager_tag = 'vws-mock-target-manager:latest'
    vws_tag = 'vws-mock-vws:latest'
    vwq_tag = 'vws-mock-vwq:latest'


def main() -> None:
    """
    Perform a release.
    """
    github_token = os.environ['GITHUB_TOKEN']
    github_owner = os.environ['GITHUB_OWNER']
    github_repository_name = os.environ['GITHUB_REPOSITORY_NAME']
    github_client = Github(github_token)
    github_repository = github_client.get_repo(
        full_name_or_id=f'{github_owner}/{github_repository_name}',
    )
    version_str = get_version(github_repository=github_repository)
    update_changelog(version=version_str, github_repository=github_repository)
    github_repository.create_git_tag_and_release(
        tag=version_str,
        tag_message='Release ' + version_str,
        release_name='Release ' + version_str,
        release_message='See CHANGELOG.rst',
        type='commit',
        object=github_repository.get_commits()[0].sha,
    )
    build_and_upload_to_pypi()
    build_and_publish_docker_images()


if __name__ == '__main__':
    main()
