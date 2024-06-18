
import shlex
import socket
import heroku3
import asyncio
from typing import Tuple

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from heda import log
from heda.config import HerokuConfig


async def install_req(cmd: str) -> Tuple[str, str, int, int]:
    args = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode("utf-8", "replace").strip(),
        stderr.decode("utf-8", "replace").strip(),
        process.returncode,
        process.pid,
    )


async def git():
    REPO_LINK = HerokuConfig.UPSTREAM_REPO
    if HerokuConfig.GIT_TOKEN:
        GIT_USERNAME = REPO_LINK.split("com/")[1].split("/")[0]
        TEMP_REPO = REPO_LINK.split("https://")[1]
        UPSTREAM_REPO = (
            f"https://{GIT_USERNAME}:{HerokuConfig.GIT_TOKEN}@{TEMP_REPO}"
        )
    else:
        UPSTREAM_REPO = HerokuConfig.UPSTREAM_REPO
    try:
        repo = Repo()
        log(__name__).info(
            f"Git Client Found [VPS DEPLOYER]"
        )
    except GitCommandError:
        log(__name__).info(f"Invalid Git Command")
    except InvalidGitRepositoryError:
        repo = Repo.init()
        if "origin" in repo.remotes:
            origin = repo.remote("origin")
        else:
            origin = repo.create_remote(
                "origin", UPSTREAM_REPO
            )
        origin.fetch()
        repo.create_head(
            HerokuConfig.UPSTREAM_BRANCH,
            origin.refs[HerokuConfig.UPSTREAM_BRANCH],
        )
        repo.heads[HerokuConfig.UPSTREAM_BRANCH].set_tracking_branch(
            origin.refs[HerokuConfig.UPSTREAM_BRANCH]
        )
        repo.heads[HerokuConfig.UPSTREAM_BRANCH].checkout(True)
        try:
            repo.create_remote(
                "origin", HerokuConfig.UPSTREAM_REPO
            )
        except BaseException:
            pass
        nrs = repo.remote("origin")
        nrs.fetch(HerokuConfig.UPSTREAM_BRANCH)
        try:
            nrs.pull(HerokuConfig.UPSTREAM_BRANCH)
        except GitCommandError:
            repo.git.reset("--hard", "FETCH_HEAD")
        await install_req(
            "pip3 install --no-cache-dir -r requirements.txt"
        )
        log(__name__).info(
            f"Fetched Updates from: {REPO_LINK}"
    )


HEROKU_APP = None

def is_heroku():
    log(__name__).info(socket.getfqdn())
    return "heroku" in socket.getfqdn()


def heroku():
    global HEROKU_APP
    if is_heroku():
        if HerokuConfig.HEROKU_API_KEY and HerokuConfig.HEROKU_APP_NAME:
            try:
                Heroku = heroku3.from_key(
                    HerokuConfig.HEROKU_API_KEY
                )
                HEROKU_APP = Heroku.app(
                    HerokuConfig.HEROKU_APP_NAME
                )
                log(__name__).info(
                    "Heroku App configured."
                )
            except Exception as e:
                log(__name__).error(str(e))
        else:
            log(__name__).warning(
                "Please make sure your Heroku API Key and Your App name are configured correctly in the heroku."
            )
