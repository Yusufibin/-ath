import argparse

from .tui import AthApp

EXT_FLAGS = {
    "py": "Python",
    "rs": "Rust",
    "js": "JavaScript",
    "ts": "TypeScript",
    "tsx": "TypeScript React",
    "jsx": "JavaScript React",
    "sh": "Shell",
    "bash": "Bash",
    "zsh": "Zsh",
    "md": "Markdown",
    "txt": "Text",
    "json": "JSON",
    "yaml": "YAML",
    "yml": "YAML",
    "toml": "TOML",
    "html": "HTML",
    "css": "CSS",
    "sql": "SQL",
    "go": "Go",
    "rb": "Ruby",
    "c": "C",
    "h": "C Header",
    "cpp": "C++",
    "hpp": "C++ Header",
    "java": "Java",
    "kt": "Kotlin",
    "swift": "Swift",
    "zig": "Zig",
    "nim": "Nim",
    "lua": "Lua",
    "vim": "Vimscript",
    "tf": "Terraform",
    "nix": "Nix",
    "patch": "Patch",
    "diff": "Diff",
}


def main():
    parser = argparse.ArgumentParser(
        prog="ath",
        description="A beautiful TUI code search tool powered by ripgrep",
    )
    parser.add_argument(
        "term", nargs="?", default="",
        help="search term"
    )
    parser.add_argument(
        "-g", "--glob", action="append", metavar="EXT",
        help="filter by extension (e.g. -g py -g rs)"
    )
    for ext, desc in EXT_FLAGS.items():
        parser.add_argument(
            f"--{ext}", action="append_const",
            dest="glob", const=ext,
            help=f"only search *.{ext} files ({desc})"
        )

    args = parser.parse_args()
    extensions = args.glob if args.glob else None

    app = AthApp(initial_term=args.term, extensions=extensions)
    app.run()


if __name__ == "__main__":
    main()
