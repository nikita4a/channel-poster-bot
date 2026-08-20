"""
Channel Poster Bot v3 — чистый httpx + entities для премиум-эмодзи.
Берёт текст + entities из входящего сообщения, пересылает в канал.
"""

import json, os, time
from pathlib import Path
import httpx

TOK = "8913247320:AAE8PHf-qoAfsiwaUrz-zgyvceupx-JUk68"
API = f"https://api.telegram.org/bot{TOK}"
CH_FILE = Path(__file__).parent / "channels.json"

state = {}  # uid -> {text, entities, kb, fmt}

def api(method, data=None):
    try:
        r = httpx.post(f"{API}/{method}", json=data, timeout=20) if data else httpx.get(f"{API}/{method}", timeout=20)
        return r.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}

def send(chat_id, text, entities=None, reply_markup=None, parse_mode="HTML", **kw):
    """entities: list of {type,offset,length,custom_emoji_id?}"""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, **kw}
    if entities:
        payload["entities"] = entities
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api("sendMessage", payload)

def get_ch(uid):
    if CH_FILE.exists():
        return json.loads(CH_FILE.read_text(encoding="utf-8")).get(str(uid))

def set_ch(uid, ch):
    d = json.loads(CH_FILE.read_text(encoding="utf-8")) if CH_FILE.exists() else {}
    d[str(uid)] = ch
    CH_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_kb(raw):
    if not raw or not raw.strip():
        return None
    rows = []
    for line in raw.strip().split("\n"):
        btns = []
        for part in line.split("|"):
            part = part.strip()
            if not part: continue
            if " - " in part:
                txt, url = part.rsplit(" - ", 1)
                url = url.strip()
                if url.startswith("http"):
                    btns.append({"text": txt.strip(), "url": url})
                    continue
            btns.append({"text": part, "callback_data": f"nop"})
        if btns: rows.append(btns)
    return {"inline_keyboard": rows} if rows else None

def preview_kb():
    return {"inline_keyboard": [
        [{"text": "✅ Опубликовать", "callback_data": "pub"}],
        [{"text": "HTML", "callback_data": "f_html"},
         {"text": "Markdown", "callback_data": "f_md"},
         {"text": "Plain", "callback_data": "f_plain"}],
        [{"text": "🔄 Заново", "callback_data": "redo"},
         {"text": "❌ Отмена", "callback_data": "cancel"}],
    ]}

def on_msg(msg):
    cid = msg["chat"]["id"]
    uid = msg["from"]["id"]
    txt = msg.get("text", "") or msg.get("caption", "")
    ents = msg.get("entities") or msg.get("caption_entities")  # <-- KEY: preserve custom_emoji entities
    if not txt:
        return
    txt = txt.strip()
    print(f"[MSG] uid={uid} text={txt[:80]} entities={ents}")

    if txt == "/start":
        send(cid, "<b>Channel Poster Bot</b>\n\n"
             "<b>Быстрый старт:</b>\n"
             "1. <code>/channel @твойканал</code>\n"
             "2. Пришли текст с эмодзи — покажу превью\n"
             "3. Выбери формат и жми «Опубликовать»\n\n"
             "<b>Команды:</b> /post /channel /keyboard /format /publish",
             reply_markup={"inline_keyboard": [
                 [{"text": "📝 Новый пост", "callback_data": "mp"},
                  {"text": "📢 Канал", "callback_data": "mc"}],
                 [{"text": "⚙️ Формат", "callback_data": "mf"}],
             ]})
        return

    if txt.startswith("/channel"):
        ch = txt.replace("/channel", "").strip()
        if not ch:
            cur = get_ch(uid)
            send(cid, f"Текущий: <code>{cur}</code>" if cur else "Не задан. /channel @username")
            return
        set_ch(uid, ch)
        send(cid, f"✅ Канал: <code>{ch}</code>")
        return

    if txt.startswith("/format"):
        arg = txt.replace("/format", "").strip().lower()
        fm = {"html": "HTML", "md": "MarkdownV2", "markdown": "MarkdownV2", "plain": ""}
        fmt = fm.get(arg)
        st = state.get(uid, {})
        if fmt is not None:
            st["fmt"] = fmt
            state[uid] = st
            send(cid, f"✅ Формат: <b>{fmt or 'Plain'}</b>")
        else:
            send(cid, f"Текущий: <b>{st.get('fmt', 'HTML') or 'Plain'}</b>\n/format html | md | plain")
        return

    if txt.startswith("/keyboard "):
        raw = txt.replace("/keyboard ", "", 1).strip()
        st = state.get(uid, {})
        if not st.get("text"):
            send(cid, "Сначала пришли текст")
            return
        st["kb"] = raw
        state[uid] = st
        send(cid, "✅ Кнопки добавлены")
        return

    if txt == "/publish":
        do_pub(cid, uid)
        return

    if txt.startswith("/post"):
        txt = txt.replace("/post", "", 1).strip()
        if not txt:
            send(cid, "Пришли текст после /post")
            return

    # Save draft + show preview
    st = state.get(uid, {})
    st["text"] = txt
    st["entities"] = ents  # preserve custom_emoji entities
    state[uid] = st
    show_preview(cid, uid)


def show_preview(cid, uid):
    st = state.get(uid, {})
    txt = st.get("text", "")
    if not txt:
        send(cid, "Нет текста. Пришли сообщение.")
        return
    fmt = st.get("fmt", "HTML")
    ents = st.get("entities")
    send(cid, f"<b>Превью ({fmt or 'Plain'}):</b>\n\n{txt}",
         entities=ents, reply_markup=preview_kb(), parse_mode=fmt or None)


def do_pub(cid, uid):
    st = state.get(uid, {})
    txt = st.get("text", "")
    if not txt:
        send(cid, "Нет черновика.")
        return
    ch = get_ch(uid)
    if not ch:
        send(cid, "Сначала /channel @username")
        return
    fmt = st.get("fmt", "HTML")
    ents = st.get("entities")
    kb = parse_kb(st.get("kb", ""))
    r = send(ch, txt, entities=ents, reply_markup=kb, parse_mode=fmt or None,
             disable_web_page_preview=True)
    if r.get("ok"):
        mid = r["result"]["message_id"]
        link = f"https://t.me/{ch.lstrip('@')}/{mid}" if ch.startswith("@") else f"msg_id={mid}"
        send(cid, f"✅ Опубликовано!\n{link}")
        state.pop(uid, None)
    else:
        send(cid, f"⚠️ Ошибка: {r.get('description', r)}")


def on_cb(cb):
    cid = cb["message"]["chat"]["id"]
    uid = cb["from"]["id"]
    data = cb.get("data", "")
    mid = cb["message"]["message_id"]
    cbid = cb["id"]
    print(f"[CB] uid={uid} data={data}")

    def ack(t="ok"):
        api("answerCallbackQuery", {"callback_query_id": cbid, "text": t})

    if data == "pub":
        ack("Публикуем...")
        do_pub(cid, uid)
    elif data == "redo":
        ack("Жду текст")
        api("editMessageText", {"chat_id": cid, "message_id": mid, "text": "Отправь новый текст."})
    elif data == "cancel":
        ack("Отменено")
        state.pop(uid, None)
        api("editMessageText", {"chat_id": cid, "message_id": mid, "text": "❌ Отменено."})
    elif data.startswith("f_"):
        fm = {"f_html": "HTML", "f_md": "MarkdownV2", "f_plain": ""}
        fmt = fm.get(data, "HTML")
        st = state.get(uid, {})
        st["fmt"] = fmt
        state[uid] = st
        ack(f"Формат: {fmt or 'Plain'}")
        show_preview(cid, uid)
    elif data == "mp":
        ack(); send(cid, "Пришли текст — покажу превью.")
    elif data == "mc":
        ack(); ch = get_ch(uid)
        send(cid, f"Текущий: <code>{ch}</code>\n/cmd: /channel @username" if ch else "Не задан. /channel @username")
    elif data == "mf":
        ack(); st = state.get(uid, {})
        send(cid, f"Текущий: <b>{st.get('fmt', 'HTML') or 'Plain'}</b>\n/format html | md | plain")
    else:
        ack("?")


def main():
    api("deleteWebhook", {"drop_pending_updates": True})
    me = api("getMe")
    print(f"[OK] @{me['result']['username']}")
    off = 0
    while True:
        try:
            r = httpx.get(f"{API}/getUpdates",
                         params={"offset": off, "timeout": 25,
                                 "allowed_updates": ["message", "callback_query"]},
                         timeout=30)
            for u in r.json().get("result", []):
                off = u["update_id"] + 1
                if "message" in u:
                    on_msg(u["message"])
                elif "callback_query" in u:
                    on_cb(u["callback_query"])
        except Exception as e:
            print(f"[ERR] {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()