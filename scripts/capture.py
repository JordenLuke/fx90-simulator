import argparse
import asyncio
import ssl
from pathlib import Path

import websockets

URL = "wss://fxr90c94e1c/ws"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "fxr90-tag-data.log"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=URL)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--cafile", type=Path, help="PEM CA certificate for self-signed FX90 certificates")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS verification for testing only")
    args = parser.parse_args()
    if args.cafile and args.insecure:
        parser.error("--cafile cannot be used together with --insecure")
    return args


def create_ssl_context(args):
    context = ssl.create_default_context()
    if args.cafile:
        context.load_verify_locations(cafile=str(args.cafile))
    if args.insecure:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


async def capture(url: str, output: Path, ssl_context: ssl.SSLContext):
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as log:
        while True:
            try:
                print(f"Connecting to {url}...")
                async with websockets.connect(url, ssl=ssl_context) as ws:
                    print("Connected.")
                    print(f"Saving messages to {output}")
                    async for msg in ws:
                        if isinstance(msg, bytes):
                            msg = msg.decode("utf-8")
                        print(msg)
                        log.write(msg + "\n")
                        log.flush()
            except Exception as ex:
                print(f"Connection ended: {type(ex).__name__}: {ex}")
            await asyncio.sleep(2)


if __name__ == "__main__":
    arguments = parse_args()
    try:
        asyncio.run(capture(arguments.url, arguments.output, create_ssl_context(arguments)))
    except KeyboardInterrupt:
        print("Capture stopped.")
