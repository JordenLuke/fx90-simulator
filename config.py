import os
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent
DATA_DIR=BASE_DIR/'data'; CERT_DIR=BASE_DIR/'certs'
HOST=os.getenv('FX90_HOST','0.0.0.0'); HTTPS_PORT=int(os.getenv('FX90_HTTPS_PORT','443'))
CERT_FILE=Path(os.getenv('FX90_CERT_FILE',str(CERT_DIR/'server.crt'))); KEY_FILE=Path(os.getenv('FX90_KEY_FILE',str(CERT_DIR/'server.key')))
TAGS_FILE=Path(os.getenv('FX90_TAGS_FILE',str(DATA_DIR/'tags.json')))
USERNAME=os.getenv('FX90_USERNAME','admin'); PASSWORD=os.getenv('FX90_PASSWORD','admin'); BEARER_TOKEN=os.getenv('FX90_BEARER_TOKEN','fx90-simulator-token')
RUNNER_COUNT=int(os.getenv('FX90_RUNNER_COUNT','400')); NOISE_PERCENT=float(os.getenv('FX90_NOISE_PERCENT','5')); MAX_BURST_SIZE=int(os.getenv('FX90_MAX_BURST_SIZE','20')); MAX_BURST_SECONDS=float(os.getenv('FX90_MAX_BURST_SECONDS','0.8'))
BETWEEN_BURSTS_MIN=float(os.getenv('FX90_BETWEEN_BURSTS_MIN','2')); BETWEEN_BURSTS_MAX=float(os.getenv('FX90_BETWEEN_BURSTS_MAX','8')); REPORT_EACH_TAG_ONCE=os.getenv('FX90_REPORT_EACH_TAG_ONCE','true').lower()=='true'; NOISE_POOL_SIZE=int(os.getenv('FX90_NOISE_POOL_SIZE','50')); AUTO_START=os.getenv('FX90_AUTO_START','false').lower()=='true'
