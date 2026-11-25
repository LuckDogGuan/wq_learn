import os
from pathlib import Path
import yaml
import requests
from urllib.parse import urljoin
from Core.api.client import BrainClient, API_BASE_URL

def load_config(config_path: str = None) -> dict:
    """
    读取 WorldQuant Brain 凭据配置文件 (Password/config.yaml)
    """
    if config_path:
        target_path = Path(config_path)
        if not target_path.is_file():
            raise FileNotFoundError("显式指定的凭据配置文件不存在")
    else:
        target_path = None
        search_roots = []
        try:
            file_dir = Path(__file__).resolve().parent
            search_roots.extend([file_dir] + list(file_dir.parents))
        except Exception:
            pass

        cwd_dir = Path(os.getcwd()).resolve()
        search_roots.extend([cwd_dir] + list(cwd_dir.parents))

        for root in search_roots:
            candidate = root / "Password" / "config.yaml"
            if candidate.exists():
                target_path = candidate
                break

        if target_path is None:
            raise FileNotFoundError("未找到凭据配置文件 Password/config.yaml，请检查文件是否存在及路径是否正确。")

    with open(target_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise ValueError("凭据配置必须是 YAML 映射")
    return config


def _credentials(config):
    username = config.get("username") or config.get("email")
    password = config.get("password")
    if not isinstance(username, str) or not username.strip() or not isinstance(password, str) or not password:
        raise ValueError("凭据必须包含 username/email 和 password")
    return username, password

def login(config_path: str = None) -> BrainClient:
    """
    登录 WorldQuant Brain 平台，自动从 Password/config.yaml 读取凭据并返回包含认证信息的 BrainClient 实例。
    """
    config = load_config(config_path)
    username, password = _credentials(config)

    s = requests.Session()
    s.auth = (username, password)
    
    # 我们包装为 BrainClient
    client = BrainClient(session=s)

    response = client.post("/authentication")
    if response is not None and response.status_code in (200, 201):
        client.mark_authenticated()
        print("登录成功。")
        return client
    status = response.status_code if response is not None else "无响应"
    s.close()
    raise RuntimeError(f"WorldQuant Brain 登录失败：HTTP {status}")

def login_hk(config_path: str = None) -> BrainClient:
    """
    适用于香港区域/包含人脸生物认证 (Persona Biometrics) 的 Brain 平台登录函数。
    """
    config = load_config(config_path)
    username, password = _credentials(config)

    s = requests.Session()
    s.auth = (username, password)
    client = BrainClient(session=s)
    
    response = client.post("/authentication")
    
    if response is not None and response.status_code == requests.codes.unauthorized:
        if response.headers.get("WWW-Authenticate") == "persona":
            print(
                "请通过人脸识别完成生物特征认证。请打开以下链接: \n"
                + urljoin(response.url, response.headers["Location"]) + "\n"
            )
            input("完成生物特征认证后按任意键继续...")
            
            biometrics_response = client.post(urljoin(response.url, response.headers["Location"]))
            
            while biometrics_response is not None and biometrics_response.status_code != 201:
                input("生物特征认证未完成，请重试后按任意键继续...")
                biometrics_response = client.post(urljoin(response.url, response.headers["Location"]))
            if biometrics_response is None:
                raise RuntimeError("生物特征认证响应不可观测")
            client.mark_authenticated()
            print("生物特征认证已完成。")
            return client
        else:
            raise PermissionError("账号或密码不正确，请检查凭据文件")
    elif response is not None and response.status_code in (200, 201):
        client.mark_authenticated()
        print("登录成功。")
        return client
    else:
        status = response.status_code if response is not None else "无响应"
        raise RuntimeError(f"WorldQuant Brain 登录失败：HTTP {status}")
