import sys, os

for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ[k] = ""
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

sys.stdout.write("[RUN] Starting uvicorn...\n")
sys.stdout.flush()

sys.path.insert(0, "c:/code/stock-chanlun/backend")
import uvicorn
uvicorn.run("main:app", host="0.0.0.0", port=8000)
