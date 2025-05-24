import mailbox
import requests
import os
import time
import sys

MAIL_PATH = f"/var/mail/{sys.argv[1]}"
WEBHOOK_URL = f"{sys.argv[2]}?wait=true"

# 読み取り
mbox = mailbox.mbox(MAIL_PATH)
try:
    mbox.lock()
except mailbox.ExternalClashError:
    print("メールボックスがロックされているため、処理を中断します。")
    print("他のプロセスがメールボックスを使用している可能性があります。")
    sys.exit(1)

to_delete = []

try:
    # for key, msg in mbox.iteritems():
    while len(mbox) > 0:
        # mbox = mailbox.mbox(MAIL_PATH)
        key, msg = next(iter(mbox.items()))


        subject = msg['subject']
        body = msg.get_payload(decode=True)
        date_header = msg.get('Date', '(no Date header)')
        if isinstance(body, bytes):
            body = body.decode(errors='replace')

        # Webhookに送信
        content = (
            f"----------------------\n" +
            f"Subject: {subject}\n" + 
            f"Date: {date_header}\n" + 
            f"Body: \n{body.strip()}\n" + 
            f"-----------------------\n"
        )
        
        chunk_size = 1900
        chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]

        for i, chunk in enumerate(chunks):
            # if i == 0:
            #     content = chunk
            # else:
            #     content = f"続き: {i+1}\n" + chunk
            content = chunk

            response = requests.post(WEBHOOK_URL, json={
                "username": msg['From'],
                "content": content
            }, headers={"Content-Type": "application/json"})


            # if response.status_code == 200:
            #     # to_delete.append(key)
            #     mbox.remove(key)
            #     mbox.flush()
            # else:
            #     print(response.status_code)
            #     print(response.headers)
            #     print(response.text)
            if response.status_code != 200:
                print(f"Webhookの送信に失敗しました: {response.status_code}")
                print("レスポンスヘッダー:", response.headers)
                print("レスポンステキスト:", response.text)
                
                break
            else:
                time.sleep(3)
            # break # ひとつだけ試す

        if response.status_code == 200:
            # メールを削除する
            # to_delete.append(key)
            mbox.remove(key)
            mbox.flush()
            print(f"メールを削除しました: {key}")

    # 削除処理
    for key in to_delete:
        mbox.remove(key)
        mbox.flush()

except KeyboardInterrupt:
    print("\n中断されました（Ctrl+C）")

except Exception as e:
    print(f"エラーが発生しました: {e}")
    print("メールボックスをロック解除して終了します。")
    print("エラーの詳細:", e)

finally:
    mbox.unlock()
    mbox.close()
    # mbox.close()

