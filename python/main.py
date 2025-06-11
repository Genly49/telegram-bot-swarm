from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import docker
import os
from dotenv import load_dotenv
import getMonitor # getMonitor.py
import dockerSwarm # dockerSwarm.py

load_dotenv()

client = docker.DockerClient(
    base_url = 'unix://var/run/docker.sock',
    version = None,
    timeout = 30,
    tls = False # can be changed with CA
)

async def node_command(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    if not context.args :
        await update.message.reply_text("請以 /node <參數> <節點名稱> 輸入指令。\n參數包括：\ncpu - CPU\nram - 記憶體\ndisk - 儲存空間\nrx - 下載速度\ntx - 上傳速度\nload - 系統負載情況")
        return
    param = context.args[0].lower()
    instance = context.args[1]
    result = getMonitor.query_prometheus(instance, f"/node_{param}")
    if result == "No queries" :
        await update.message.reply_text("未知的參數，請輸入正確的參數。\n參數包括：\ncpu - CPU\nram - 記憶體\ndisk - 儲存空間\nrx - 下載速度\ntx - 上傳速度\nload - 系統負載情況")
    else :
        with open(result, 'rb') as photo_file :
            await update.message.reply_photo(photo = photo_file)
    return

async def container_command(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    if not context.args :
        await update.message.reply_text("請以 /con <參數> <容器名稱> <true | false 標籤> 輸入指令。\n參數包括：\ncpu - CPU\nram - 記憶體\n\nrx - 下載速度\ntx - 上傳速度")
        return
    param = context.args[0].lower()
    container = context.args[1].lower()
    use_label = context.args[2].lower() == "true"
    key = f"/container_{param}_label" if use_label else f"/container_{param}"
    result = getMonitor.query_prometheus(container, key)
    if result == "No queries" :
        await update.message.reply_text("未知的參數，請輸入正確的參數。\n參數包括：\ncpu - CPU\nram - 記憶體\nrx - 下載速度\ntx - 上傳速度")
    else :
        with open(result, 'rb') as photo_file :
            await update.message.reply_photo(photo = photo_file)# update.message.send_photo(chat_id = update.effective_chat.id, photo = photo_file)
    return

async def list_instance(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    if not context.args :
        await update.message.reply_text("請以 /ls node 或 /ls <con | ser> <節點名稱> 輸入指令。")
        return
    param = context.args[0].lower()
    if param == "node" :
        result = dockerSwarm.list_nodes(client)
        if isinstance(result, str) :
            await update.message.reply_text(result)
        else :
            message = "節點清單：\n"
            message += "主機名稱\tIP\t狀態\t可用性\t角色\n"
            for n in result :
                message += f"{n['hostname']}\t{n['ip']}\t{n['status']}\t{n['availability']}\t{n['manager_status']}\n"
            await update.message.reply_text(f"<pre>{message}</pre>", parse_mode = "HTML")

    elif param == "con" :
        if len(context.args) < 2 :
            await update.message.reply_text("請輸入節點名稱。")
            return
        node = context.args[1]
        result = dockerSwarm.list_containers(client, node)
        if isinstance(result, str) :
            await update.message.reply_text(result)
        else :
            message = f"{node} 節點上的 container 清單：\n"
            message += "名稱\t狀態\tport\t建立時間\t\tCPU\tRAM\n"
            for c in result :
                message += (f"{c['name']}\t{c['status']}\t{c['ports']}\t{c['created']}\t{c['cpu']}\t{c['memory']}\n")
            await update.message.reply_text(f"<pre>{message}</pre>", parse_mode = "HTML")

    elif param == "ser" :
        data = dockerSwarm.list_services(client)
        if isinstance(data, str) :
            await update.message.reply_text(data)
            return
        message = "服務清單：\n"
        message += "名稱\timage\treplicas\tport\n"
        for s in data :
            message += f"{s['name']}\t{s['image']}\t{s['replicas']}\t{s['ports']}\n"
        await update.message.reply_text(f"<pre>{message}</pre>", parse_mode="HTML")

    else :
        await update.message.reply_text("未知的查詢參數，請使用 /ls node 或 /ls <con | ser> <節點名稱>。")

async def modify_container(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    if len(context.args) < 3 :
        await update.message.reply_text("請以 /modify <con | ser> <create | start | run | pause | resume | restart | remove> <名稱> <image> <port> <replicas> 輸入指令。")
        return
    kind = context.args[0]
    action = context.args[1]
    name = context.args[2]
    result = ""

    if kind == "con" :
        if action == "create" :
            print(len(context.args))
            if len(context.args) < 5 :
                await update.message.reply_text("建立容器至少需要 容器名稱、image 與 port。\n格式： /modify <con | ser> <create | start | run | pause | resume | restart | remove> <名稱> <image> <port>")
                return
            image = context.args[3]
            if (context.args[4]).isdigit() :
                port = int(context.args[4])
            else :
                await update.message.reply_text("port 輸入不正確。")
                return
            result = dockerSwarm.create_container(client, name, image, ports = {f"{port}/tcp": port})
        if action == "start" :
            result = dockerSwarm.start_container(client, name, image, ports = {f"{port}/tcp": port})
        if action == "run" :
            print(len(context.args))
            if len(context.args) < 5 :
                await update.message.reply_text("建立容器至少需要 容器名稱、image 與 port。\n格式： /modify <con | ser> <create | start | run | pause | resume | restart | remove> <名稱> <image> <port>")
                return
            image = context.args[3]
            if (context.args[4]).isdigit() :
                port = int(context.args[4])
            else :
                await update.message.reply_text("port 輸入不正確。")
                return
            result = dockerSwarm.run_container(client, name, image, ports = {f"{port}/tcp": port})
        elif action == "pause" :
            result = dockerSwarm.pause_container(client, name)
        elif action == "resume" :
            result = dockerSwarm.resume_container(client, name)
        elif action == "restart" :
            result = dockerSwarm.restart_container(client, name)
        elif action == "remove" :
            result = dockerSwarm.remove_container(client, name)
        else :
            await update.message.reply_text("未知的動作參數，請再確認一次。\n參數包括：\ncreate - 建立\nstart - 啟動\nrun - 建立並啟動\npause - 暫停\nresume - 繼續\nrestart - 重新啟動\nrm - 刪除")
            return
        await update.message.reply_text(f"{result}")

    elif kind == "ser" :
        if action == "create" :
            if len(context.args) < 5 :
                await update.message.reply_text("建立服務至少需要 容器名稱、image 與 port。\n格式： /modify ser <create | restart | remove> <名稱> <image> <port> <replicas>")
                return
            image = context.args[3]
            if (context.args[4]).isdigit() :
                port = int(context.args[4])
            else :
                await update.message.reply_text("port 輸入不正確。")
                return
            replicas = int(context.args[4]) if (context.args[4]).isdigit() and len(context.args) > 5 else 1
            result = dockerSwarm.create_service(client, name, image, port = port, replicas = replicas)
        elif action == "restart" :
            result = dockerSwarm.restart_service(client, name)
        elif action == "remove" :
            result = dockerSwarm.remove_service(client, name)
        else :
            await update.message.reply_text("未知的動作參數，請再確認一次。")
            return
        await update.message.reply_text(f"{result}")

    else :
        await update.message.reply_text("未知的資源類型，請再確認一次。")

app = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
app.add_handler(CommandHandler("node", node_command))
app.add_handler(CommandHandler("con", container_command))
app.add_handler(CommandHandler("ls", list_instance))
app.add_handler(CommandHandler("modify", modify_container))
app.run_polling()
