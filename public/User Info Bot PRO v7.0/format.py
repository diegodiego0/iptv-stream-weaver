# ══════════════════════════════════════════════
# 🎨  FORMATAÇÃO HTML — User Info Bot PRO v7.0
# 👨‍💻 Créditos: Edivaldo Silva @Edkd1
# ══════════════════════════════════════════════
"""
Conversor robusto de Markdown-leve (Telegram-style) → HTML do Telegram.

Por que HTML?
  - O parse_mode='md'/'markdown' do Telethon é rígido: caracteres como '_',
    '*', '`', '[' precisam de escape e quebram fácil quando há emojis,
    pontuação ou conteúdo dinâmico. Isso fazia o **negrito** não renderizar
    em várias mensagens.
  - HTML do Telegram é tolerante: basta escapar <, > e &.

Sintaxe suportada na origem (markdown-leve):
  *texto*        → <b>texto</b>
  **texto**      → <b>texto</b>
  __texto__      → <b>texto</b>   (alguns lugares usam essa convenção)
  _texto_        → <i>texto</i>
  `texto`        → <code>texto</code>
  ```texto```    → <pre>texto</pre>
  [label](url)   → <a href="url">label</a>

Uso:
  from format import to_html, HTML
  await bot.send_message(chat, to_html("Olá *mundo* `123`"), parse_mode=HTML)
"""

import re
from html import escape as _esc

HTML = "html"  # constante para parse_mode


# ── Tokenização para preservar trechos "literais" ──
_TOKEN_RE = re.compile(
    r"```(.+?)```"                              # 1: bloco code
    r"|`([^`\n]+)`"                             # 2: inline code
    r"|\*\*([^*\n]+?)\*\*"                      # 3: **bold**
    r"|__([^_\n]+?)__"                          # 4: __bold__
    r"|\*([^*\n]+?)\*"                          # 5: *bold*
    r"|_([^_\n]+?)_"                            # 6: _italic_
    r"|\[([^\]]+)\]\(([^)]+)\)",                # 7,8: [label](url)
    re.DOTALL,
)


def to_html(text: str) -> str:
    """Converte markdown-leve para HTML do Telegram, escapando o resto."""
    if not text:
        return ""

    out = []
    last = 0
    for m in _TOKEN_RE.finditer(text):
        # Texto cru entre tokens — escapa
        if m.start() > last:
            out.append(_esc(text[last:m.start()]))
        if m.group(1) is not None:                       # ```code block```
            out.append(f"<pre>{_esc(m.group(1))}</pre>")
        elif m.group(2) is not None:                     # `inline`
            out.append(f"<code>{_esc(m.group(2))}</code>")
        elif m.group(3) is not None:                     # **bold**
            out.append(f"<b>{_esc(m.group(3))}</b>")
        elif m.group(4) is not None:                     # __bold__
            out.append(f"<b>{_esc(m.group(4))}</b>")
        elif m.group(5) is not None:                     # *bold*
            out.append(f"<b>{_esc(m.group(5))}</b>")
        elif m.group(6) is not None:                     # _italic_
            out.append(f"<i>{_esc(m.group(6))}</i>")
        elif m.group(7) is not None:                     # [label](url)
            label = _esc(m.group(7))
            url   = _esc(m.group(8), quote=True)
            out.append(f'<a href="{url}">{label}</a>')
        last = m.end()
    if last < len(text):
        out.append(_esc(text[last:]))
    return "".join(out)


# ── Helpers explícitos (caso queira escrever HTML direto) ──
def b(t: str) -> str:    return f"<b>{_esc(t)}</b>"
def i(t: str) -> str:    return f"<i>{_esc(t)}</i>"
def code(t: str) -> str: return f"<code>{_esc(t)}</code>"
def link(label: str, url: str) -> str:
    return f'<a href="{_esc(url, quote=True)}">{_esc(label)}</a>'


__all__ = ["to_html", "HTML", "b", "i", "code", "link"]
