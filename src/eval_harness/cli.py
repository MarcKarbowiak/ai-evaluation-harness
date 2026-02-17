import argparse
from eval_harness.core.runner import run_eval

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", nargs="?")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--adapter", default="mock")
    args = parser.parse_args()

    report = run_eval(args.dataset, args.prompt, args.schema, args.adapter)
    print("Report written:", report)
