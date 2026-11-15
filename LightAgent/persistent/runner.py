"""Run the generic execution supervisor. Research and its UI are optional extensions."""
import argparse
import signal
from .execution import ExecutionService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--max-concurrent-jobs", type=int, default=8)
    args = parser.parse_args()
    service = ExecutionService(args.root, max_concurrent_jobs=args.max_concurrent_jobs)
    if args.stop:
        service.request_shutdown()
        return
    signal.signal(signal.SIGTERM, lambda *_: service.stop())
    signal.signal(signal.SIGINT, lambda *_: service.stop())
    from .maintenance import runtime_logging
    with runtime_logging(service.root):
        service.serve_forever()


if __name__ == "__main__":
    main()
