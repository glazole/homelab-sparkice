# Автокнопка Spark UI для JupyterHub (/user/<name>/proxy/<port>/jobs/)
import os, time, socket
from html import escape
from IPython.display import display, HTML, Javascript

def _hub_prefix():
    # обычно есть: /user/<name>/
    prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX")
    if prefix:
        return prefix.rstrip("/")
    user = os.environ.get("JUPYTERHUB_USER", "")
    return f"/user/{user}" if user else ""

def _pick_spark_ui_port(start=4040, end=4060, host="127.0.0.1", timeout=0.2):
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                s.connect((host, port))
                return port
            except Exception:
                pass
    return None

def spark_ui_url(wait_seconds=5, port_range=(4040, 4060), page="jobs"):
    """
    Возвращает ОТНОСИТЕЛЬНЫЙ URL, который всегда правильно открывается в браузере:
    /user/<u>/proxy/<port>/jobs/
    """
    hub = _hub_prefix()
    if not hub:
        raise RuntimeError("Not in JupyterHub (no JUPYTERHUB_SERVICE_PREFIX/JUPYTERHUB_USER).")

    end_time = time.time() + wait_seconds
    port = None
    while time.time() < end_time and port is None:
        port = _pick_spark_ui_port(port_range[0], port_range[1])
        if port is None:
            time.sleep(0.3)

    if port is None:
        print(f"Spark UI not found on {port_range[0]}..{port_range[1]}. Is SparkSession running?")
        return None

    page = (page or "").strip("/")
    tail = f"{page}/" if page else ""
    return f"{hub}/proxy/{port}/{tail}"

def spark_ui_link(*args, **kwargs):
    """Печатает кликабельную ссылку (относительную)"""
    url = spark_ui_url(*args, **kwargs)
    if not url:
        return None
    display(HTML(f'<a href="{escape(url)}" target="_blank">Spark UI: {escape(url)}</a>'))
    return url

def spark_ui_button(*args, **kwargs):
    """Рисует кнопку открытия Spark UI"""
    url = spark_ui_url(*args, **kwargs)
    if not url:
        return None
    display(HTML(f"""
    <button style="padding:6px 10px; cursor:pointer"
            onclick="window.open('{escape(url)}','_blank')">
      Open Spark UI
    </button>
    <span style="margin-left:10px; font-family:monospace">{escape(url)}</span>
    """))
    return url

def spark_ui_full(*args, **kwargs):
    """
    Печатает ПОЛНЫЙ URL (https://julab... + хвост) через JS.
    """
    url = spark_ui_url(*args, **kwargs)
    if not url:
        return None
    # JS выведет полный url прямо в output
    display(Javascript(f"""
    (function(){{
      const full = window.location.origin + {url!r};
      const pre = document.createElement('pre');
      pre.textContent = full;
      pre.style.fontSize = '12px';
      document.querySelector('.jp-OutputArea-output')?.appendChild(pre);
    }})();
    """))
    # и ссылку тоже покажем
    display(HTML(f'<a href="{escape(url)}" target="_blank">Spark UI (open)</a>'))
    return url