from __future__ import annotations

from apps.openclaw_bridge.tool_runner import EmbodiedClawToolRunner


def main() -> None:
    runner = EmbodiedClawToolRunner()
    print('EmbodiedClaw OpenClaw-style demo chat loop started. 输入 quit/exit 结束。')
    while True:
        command = input('> ').strip()
        if command.lower() in {'quit', 'exit'}:
            print('Bye.')
            return
        if not command:
            continue

        results = runner.run_command_until_terminal(command)
        for item in results:
            print(item.message)


if __name__ == '__main__':
    main()
