from tasks.base.download import download_with_progress
from managers.logger_manager import logger
from managers.config_manager import config
from managers.translate_manager import _
from tasks.base.runsubprocess import RunSubprocess
from tasks.base.windowswitcher import WindowSwitcher
from tasks.base.command import run_command
import subprocess
import tempfile
import os


class PythonChecker:
    @staticmethod
    def run(python_path=config.python_path):
        if python_path != '' and PythonChecker.check(python_path):
            return True
        else:
            paths = run_command(["where", "python.exe"])
            if paths is not None:
                for path in paths.split("\n"):
                    path_dir = os.path.dirname(path)
                    if PythonChecker.check(path_dir):
                        config.set_value("python_path", path_dir)
                        logger.debug(_("Python 路径更新成功：{path}").format(path=path_dir))
                        return True
            logger.warning(_("没有在环境变量中找到可用的 Python 路径"))
            logger.warning(_("如果已经修改了环境变量，请尝试重启程序，包括图形界面"))

        logger.warning(_("Python 路径不存在: {path}").format(path=python_path))

        download_url = "http://mirrors.huaweicloud.com/python/3.11.5/python-3.11.5-amd64.exe"
        download_file_path = os.path.join(tempfile.gettempdir(), os.path.basename(download_url))
        destination_path = os.path.join(os.getenv('LocalAppData'), 'Programs\Python\Python311')

        while True:
            try:
                os.makedirs(os.path.dirname(download_file_path), exist_ok=True)
                logger.info(_("开始下载：{url}").format(url=download_url))
                download_with_progress(download_url, download_file_path)
                logger.info(_("下载完成：{destination}").format(destination=download_file_path))
                break
            except Exception as e:
                logger.error(_("下载失败：{e}").format(e=e))
                input(_("按任意键重试. . ."))

        while True:
            try:
                if not subprocess.run(f"{download_file_path} /passive InstallAllUsers=0 PrependPath=1 Include_launcher=0 Include_test=0", shell=True, check=True):
                    raise Exception
                logger.info(_("安装完成"))
                break
            except Exception as e:
                logger.error(_("安装失败：{e}").format(e=e))
                input(_("按任意键重试. . ."))

        try:
            os.remove(download_file_path)
            logger.info(_("清理完成：{path}").format(path=download_file_path))
        except Exception as e:
            logger.error(_("清理失败：{e}").format(e=e))

        if PythonChecker.check(destination_path):
            config.set_value("python_path", destination_path)
            WindowSwitcher.check_and_switch(config.game_title_name)
            return True

        logger.error(_("仍未找到可用的 Python 路径，请尝试重启程序，包括图形界面"))
        logger.error(_("也可卸载后重新运行或在 config.yaml 中手动修改 python_path（文件夹）"))
        return False

    @staticmethod
    def check(python_path):
        python_result = run_command([f"{python_path}\\python.exe", '-V'])
        if python_result is not None and python_result[0:7] == "Python ":
            logger.debug(_("Python 路径: {path}").format(path=python_path))
            python_version = python_result.split(' ')[1]
            if python_version < "3.11":
                logger.warning(_("Python 版本: {version} < 3.11 若出现异常请尝试升级").format(version=python_version))
            else:
                logger.debug(_("Python 版本: {version}").format(version=python_version))
            pip_result = run_command([f"{python_path}\\Scripts\\pip.exe", '-V'])
            if pip_result is not None and pip_result[0:4] == "pip ":
                pip_version = pip_result.split(' ')[1]
                logger.debug(_("pip 版本: {version}").format(version=pip_version))
                return True
            else:
                logger.debug(_("开始安装 pip"))
                from tasks.base.fastest_mirror import FastestMirror
                if RunSubprocess.run(f"{python_path}\\python.exe .\\assets\\config\\get-pip.py -i {FastestMirror.get_pypi_mirror()} --no-warn-script-location", 600):
                    logger.debug(_("pip 安装完成"))
                    return True
                else:
                    logger.error(_("pip 安装失败"))
                    return False
        return False
