"""Git 协作示例：向参与者打招呼。"""

import sys


def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to Git collaboration."


def main():
    if len(sys.argv) > 1:
        for name in sys.argv[1:]:
            print(greet(name))
    else:
        print(greet("participant"))


if __name__ == "__main__":
    main()
