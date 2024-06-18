
import os
import shutil
import asyncio
import urllib3
from datetime import datetime

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from pyrogram import Client, filters
from pyrogram.types import Message

from heda import paste, log
from heda.config import HerokuConfig, LogConfig, DataConfig
from heda.utils.heroku import is_heroku


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


@Client.on_message(
    filters.command(["getlog"])
    & filters.user([DataConfig.OWNER_ID])
)
async def get_log(_, message: Message):
    try:
        if is_heroku():
            if HEROKU_APP is None:
                return await message.reply_text(
                    "Please make sure your Heroku API Key, Your App name are configured correctly in the heroku."
                )
            data = HEROKU_APP.get_log()
            link = await paste.dpaste(data)
            return await message.reply_text(link)
        else:
            if os.path.exists(LogConfig.LOG_FILE_PATH):
                l = open(LogConfig.LOG_FILE_PATH)
                lines = l.readlines()
                data = ""
                try:
                    NUMB = int(message.text.split(None, 1)[1])
                except:
                    NUMB = 100
                for x in lines[-NUMB:]:
                    data += x
                link = await paste.dpaste(data)
                return await message.reply_text(link)
            else:
                return await message.reply_text(
                    "You can only get logs of Heroku Apps."
                )
    except Exception as e:
        log(__name__).error(f"Error: {str(e)}")
        await message.reply_text(
            "You can only get logs of Heroku Apps."
        )


@Client.on_message(
    filters.command(["update"])
    & filters.user([DataConfig.OWNER_ID])
)
async def update_(client: Client, message: Message):
    if is_heroku():
        if HEROKU_APP is None:
            return await message.reply_text(
                "Please make sure your Heroku API Key, Your App name are configured correctly in the heroku."
            )
    msg = await message.reply_text(
        "Checking for available updates..."
    )
    try:
        repo = Repo()
    except GitCommandError:
        return await msg.edit("Git Command Error")
    except InvalidGitRepositoryError:
        return await msg.edit(
            "Invalid Git Repsitory"
        )
    to_exc = f"git fetch origin {HerokuConfig.UPSTREAM_BRANCH} &> /dev/null"
    os.system(to_exc)
    await asyncio.sleep(7)
    verification = ""
    REPO_ = repo.remotes.origin.url.split(".git")[0]
    for checks in repo.iter_commits(
        f"HEAD..origin/{HerokuConfig.UPSTREAM_BRANCH}"
    ):
        verification = str(checks.count())
    if verification == "":
        return await msg.edit("Bot is up-to-date!")
    updates = ""
    ordinal = lambda format: "%d%s" % (
        format,
        "tsnrhtdd"[
            (format // 10 % 10 != 1)
            * (format % 10 < 4)
            * format
            % 10 :: 4
        ],
    )
    for info in repo.iter_commits(
        f"HEAD..origin/{HerokuConfig.UPSTREAM_BRANCH}"
    ):
        updates += f"#{info.count()}: [{info.summary}]({REPO_}/commit/{info}) by -> {info.author}\n\t\t\t\tCommited on: {ordinal(int(datetime.fromtimestamp(info.committed_date).strftime('%d')))} {datetime.fromtimestamp(info.committed_date).strftime('%b')}, {datetime.fromtimestamp(info.committed_date).strftime('%Y')}\n\n"
    _update_response_ = "A new update is available for the Bot!\n\nPushing Updates Now\n\nUpdates:\n\n"
    _final_updates_ = _update_response_ + updates
    if len(_final_updates_) > 4096:
        url = await paste.dpaste(updates)
        nrs = await msg.edit(
            f"A new update is available for the Bot!\n\nPushing Updates Now\n\nUpdates:\n\n[Click Here to checkout Updates]({url})"
        )
    else:
        nrs = await msg.edit(
            _final_updates_,
            disable_web_page_preview=True
        )
    os.system("git stash &> /dev/null && git pull")
    if is_heroku():
        try:
            await msg.edit(
                f"{nrs.text}\n\nBot was updated successfully on Heroku! Now, wait for 2 - 3 mins until the bot restarts!"
            )
            os.system(
                f"git push https://heroku:{str(HerokuConfig.HEROKU_API_KEY)}@git.heroku.com/{str(HerokuConfig.HEROKU_APP_NAME)}.git HEAD:main"
            )
            return
        except Exception as err:
            await msg.edit(
                f"{nrs.text}\n\nSomething went wrong while initiating reboot! Please try again later or check logs for more info."
            )
            return await client.send_message(
                LogConfig.LOG_CHAT_ID,
                f"AN EXCEPTION OCCURRED AT #UPDATER DUE TO: `{err}`",
            )
    else:
        await msg.edit(
            f"{nrs.text}\n\nBot was updated successfully! Now, wait for 1 - 2 mins until the bot reboots!"
        )
        os.system("pip3 install -r requirements.txt")
        os.system(f"kill -9 {os.getpid()} && bash start")
        exit()


@Client.on_message(
    filters.command(["reboot"])
    & filters.user([DataConfig.OWNER_ID])
)
async def restart_(_, message: Message):
    msg = await message.reply_text("Restarting....")
    try:
        shutil.rmtree("downloads")
        shutil.rmtree("raw_files")
        shutil.rmtree("cache")
    except:
        pass
    await msg.edit(
        "Reboot has been initiated successfully!\nWait for 1 - 2 minutes until the bot restarts."
    )
    os.system(f"kill -9 {os.getpid()} && bash start")
