"""Workspace CLI: discover models, export validated variants, show and render."""

import argparse
from importlib import import_module

from cadkit.export import export_model
from cadkit.model import discover


def main():
    """Console entry point for installed cadkit products."""
    parser = argparse.ArgumentParser(prog="cadkit")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    for action in ("build", "show"):
        cmd = commands.add_parser(action)
        cmd.add_argument("model")
        cmd.add_argument("-v", "--variant", default="full")
        if action == "build":
            cmd.add_argument("--all", action="store_true")
            cmd.add_argument("--render", action="store_true")
            cmd.add_argument("--animate", action="store_true")
    args = parser.parse_args()
    models = discover()
    if args.command == "list":
        for name, model in sorted(models.items()):
            print(f"{name} {model.version}: {', '.join(model.variants)}")
        return
    if args.model not in models:
        parser.error(f"Unknown model {args.model}; available: {', '.join(models)}")
    model = models[args.model]
    if args.variant not in model.variants:
        parser.error(f"Unknown variant {args.variant}")
    if args.command == "show":
        from ocp_vscode import show

        parts = model.build(model.variants[args.variant])
        show(*parts.values(), names=list(parts))
        return
    for variant in model.variants if args.all else [args.variant]:
        out = export_model(model, variant)
        print(out)
        if args.render or args.animate:
            from cadkit.render import render_model

            module = import_module(model.build.__module__)
            render_model(model, variant, out, module, animate=args.animate)


if __name__ == "__main__":
    main()
