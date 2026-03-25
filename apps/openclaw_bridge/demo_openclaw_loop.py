from __future__ import annotations

import time

from apps.openclaw_bridge.tool_runner import OpenClawToolFacade


def main() -> None:
    facade = OpenClawToolFacade()
    print('EmbodiedClaw OpenClaw/Feishu two-tool demo started. 输入 quit/exit 结束。')

    while True:
        command = input('> ').strip()
        if command.lower() in {'quit', 'exit'}:
            print('Bye.')
            return
        if not command:
            continue

        message = facade.handle_message(command)
        print(message.reply_text)

        if not message.needs_polling or not message.task_id:
            continue

        while True:
            polled = facade.poll_task(message.task_id)
            print(polled.reply_text)
            if polled.terminal:
                break
            time.sleep(1.0)


if __name__ == '__main__':
    main()
