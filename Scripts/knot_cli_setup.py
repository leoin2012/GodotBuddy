#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knot CLI 自动安装与团队 Token 更新工具（从 CrashBuddy 迁移）

功能：
  1. 检测 knot-cli 是否已安装
  2. 未安装时，使用团队 Token 自动安装
  3. 已安装时，更新本地 token 配置
"""

import os
import sys
import shutil
import subprocess
import platform


KNOT_CLI_INSTALL_SCRIPT_URL = "https://mirrors.tencent.com/repository/generic/knot-cli/install.sh"


def is_knot_cli_installed(knot_cli_command="knot-cli"):
    """检测 knot-cli 是否已安装。"""
    if not shutil.which(knot_cli_command):
        return False, "命令不在 PATH 中"
    
    try:
        result = subprocess.run(
            [knot_cli_command, "--version"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            return True, version
        else:
            return False, f"返回码: {result.returncode}"
    except FileNotFoundError:
        return False, "命令未找到"
    except subprocess.TimeoutExpired:
        return False, "版本检测超时"
    except Exception as e:
        return False, str(e)


def install_knot_cli(token, workspace="", version="", verbose=True):
    """使用团队 Token 安装 knot-cli。"""
    if not token:
        return False, "团队 Token 为空，无法安装"
    
    is_windows = platform.system() == "Windows"
    
    bash_args = f"--token {token} --origin knot --codebase"
    
    if workspace:
        for ws in workspace.split(";"):
            ws = ws.strip()
            if ws:
                bash_args += f' --workspace "{ws}"'
    
    if version:
        bash_args += f" --version {version}"
    
    if is_windows:
        git_bash = _find_git_bash()
        if git_bash:
            cmd = f'curl -v -L "{KNOT_CLI_INSTALL_SCRIPT_URL}" | bash -s -- {bash_args}'
            full_cmd = [git_bash, "-c", cmd]
            shell_name = "Git Bash"
        else:
            wsl_path = shutil.which("wsl")
            if wsl_path:
                cmd = f'curl -v -L "{KNOT_CLI_INSTALL_SCRIPT_URL}" | bash -s -- {bash_args}'
                full_cmd = ["wsl", "bash", "-c", cmd]
                shell_name = "WSL"
            else:
                return False, (
                    "Windows 环境未找到 Git Bash 或 WSL，无法自动安装 knot-cli。\n"
                    "请手动安装：\n"
                    f"  1. 安装 Git for Windows（包含 Git Bash）\n"
                    f"  2. 在 Git Bash 中执行：\n"
                    f"     curl -v -L '{KNOT_CLI_INSTALL_SCRIPT_URL}' | bash -s -- {bash_args}"
                )
    else:
        cmd = f'curl -v -L "{KNOT_CLI_INSTALL_SCRIPT_URL}" | bash -s -- {bash_args}'
        full_cmd = ["bash", "-c", cmd]
        shell_name = "bash"
    
    if verbose:
        print(f"  [Knot CLI] 正在安装 knot-cli（通过 {shell_name}）...")
    
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True, text=True, timeout=300,
            encoding="utf-8", errors="replace"
        )
        
        if result.returncode == 0:
            if verbose:
                print(f"  [Knot CLI] ✅ 安装成功")
            return True, "安装成功"
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            if verbose:
                print(f"  [Knot CLI] ❌ 安装失败 (返回码: {result.returncode})")
            return False, f"安装失败 (返回码: {result.returncode}): {error_msg[:200]}"
    
    except subprocess.TimeoutExpired:
        return False, "安装超时（300s）"
    except Exception as e:
        return False, f"安装异常: {e}"


def update_knot_cli_token(token, knot_cli_command="knot-cli", version="", verbose=True):
    """更新已安装的 knot-cli 的团队 Token。"""
    if not token:
        return False, "团队 Token 为空"
    
    if verbose:
        print(f"  [Knot CLI] 正在更新团队 Token...")
    
    cmd = [knot_cli_command, "update", "--token", token]
    if version:
        cmd.extend(["--version", version])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace"
        )
        
        if result.returncode == 0:
            if verbose:
                print(f"  [Knot CLI] ✅ Token 更新成功")
            return True, "Token 更新成功"
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            return False, f"Token 更新失败: {error_msg[:200]}"
    
    except FileNotFoundError:
        return False, f"{knot_cli_command} 命令未找到"
    except subprocess.TimeoutExpired:
        return False, "Token 更新超时"
    except Exception as e:
        return False, f"Token 更新异常: {e}"


def ensure_knot_cli(cfg, verbose=True):
    """
    确保 knot-cli 已安装且 Token 已配置。
    
    :param cfg: configparser.ConfigParser 对象
    :param verbose: 是否输出详细日志
    :return: (bool, str) - (是否就绪, 消息)
    """
    if not cfg.has_section("Analysis"):
        return True, "无 [Analysis] 配置段，跳过 knot-cli 检查"
    
    team_token = cfg.get("Analysis", "knot_team_token", fallback="").strip()
    if not team_token:
        if verbose:
            print(f"  [Knot CLI] knot_team_token 未配置，跳过自动安装/更新")
        return True, "knot_team_token 未配置，跳过"
    
    cli_command = cfg.get("Analysis", "cli_tool_command", fallback="knot-cli").strip()
    cli_version = cfg.get("Analysis", "knot_cli_version", fallback="").strip()
    cli_workspace = cfg.get("Analysis", "cli_tool_workspace", fallback="").strip()
    
    if verbose:
        print(f"  [Knot CLI] 检测 knot-cli 环境...")
    
    installed, version_info = is_knot_cli_installed(cli_command)
    
    if installed:
        if verbose:
            print(f"  [Knot CLI] ✅ 已安装 ({version_info})")
        success, msg = update_knot_cli_token(team_token, cli_command, version=cli_version, verbose=verbose)
        if not success and verbose:
            print(f"  [Knot CLI] ⚠️  Token 更新失败，将使用现有配置继续: {msg}")
        return True, f"已安装 ({version_info})"
    else:
        if verbose:
            print(f"  [Knot CLI] ❌ 未安装 ({version_info})")
        success, msg = install_knot_cli(
            token=team_token,
            workspace=cli_workspace,
            version=cli_version,
            verbose=verbose
        )
        if success:
            installed2, version_info2 = is_knot_cli_installed(cli_command)
            if installed2:
                return True, f"安装成功 ({version_info2})"
            else:
                return False, "安装脚本执行成功但 knot-cli 仍不可用"
        else:
            return False, f"自动安装失败: {msg}"


def _find_git_bash():
    """在 Windows 上查找 Git Bash 的路径。"""
    if platform.system() != "Windows":
        return None
    
    candidates = [
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Git", "bin", "bash.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Git", "bin", "bash.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Git", "bin", "bash.exe"),
    ]
    
    bash_in_path = shutil.which("bash")
    if bash_in_path:
        return bash_in_path
    
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    
    return None
