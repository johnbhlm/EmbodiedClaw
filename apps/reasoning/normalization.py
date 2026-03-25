from __future__ import annotations

import re

_FULLWIDTH_PUNCT = {
    '，': ',',
    '。': '.',
    '：': ':',
    '；': ';',
    '？': '?',
    '！': '!',
}

_CANONICAL_PATTERNS: list[tuple[str, str]] = [
    (r'^前进\s*1\s*米$', '往前走一米'),
    (r'^前进一米$', '往前走一米'),
    (r'^左转\s*45\s*度$', '左转45度'),
    (r'^右转\s*45\s*度$', '右转45度'),
    (r'^你看见了什么$', '你看到了什么'),
    (r'^桌上有什么$', '桌子上都有什么'),
    (r'^整理一下桌面$', '收拾一下桌子'),
    (r'^把餐桌上的苹果给我$', '将餐桌上苹果给我'),
    (r'^每晚九点巡检窗户和灯$', '每天晚上九点巡检窗户和灯是否关闭'),
]


def normalize_command_text(text: str) -> str:
    normalized = text.strip()
    for src, dst in _FULLWIDTH_PUNCT.items():
        normalized = normalized.replace(src, dst)

    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip(' .!?')

    for pattern, target in _CANONICAL_PATTERNS:
        if re.fullmatch(pattern, normalized):
            return target

    return normalized
