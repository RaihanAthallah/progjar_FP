# from chatcli import *
from flet import *
import flet as ft
import shutil
import os
# TARGET_IP = "127.0.0"
# TARGET_PORT = "55555"
# ON_WEB = os.getenv("ONWEB") or "0"

class Message():
    def __init__(self, user_name: str, text: str, message_type: str):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type

class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment="start"
        self.controls=[
                ft.CircleAvatar(
                    content=ft.Text(self.get_initials(message.user_name)),
                    color=ft.colors.WHITE,
                    bgcolor=self.get_avatar_color(message.user_name),
                ),
                ft.Column(
                    [
                        ft.Text(message.user_name, weight="bold"),
                        ft.Text(message.text, selectable=True),
                    ],
                    tight=True,
                    spacing=5,
                ),
            ]

    def get_initials(self, user_name: str):
        return user_name[:1].capitalize()

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]

def main(page: ft.Page):
    page.horizontal_alignment = "stretch"
    page.title = "Group Chat"
    page.bgcolor = "#001a26"
    file_location = Text("")

    def join_chat_click(e):
        if not join_user_name.value:
            join_user_name.error_text = "Name cannot be blank!"
            join_user_name.update()
        else:
            page.session.set("user_name", join_user_name.value)
            page.dialog.open = False
            new_message.prefix = ft.Text(f"{join_user_name.value}: ")
            page.pubsub.send_all(Message(user_name=join_user_name.value, text=f"{join_user_name.value} has joined the chat.", message_type="login_message"))
            page.update()

    def send_message_click(e):
        if new_message.value != "":
            page.pubsub.send_all(Message(page.session.get("user_name"), new_message.value, message_type="chat_message"))
            new_message.value = ""
            new_message.error_text = ""
            new_message.focus()
            page.update()
            # txt = new_message.value
            # chat.controls.append(ft.Text(f"command: {txt}"))
            # txt = cc.proses(txt)
            # chat.controls.append(ft.Text(f"result {cc.tokenid}: {txt}"))
            # cmd.value=""
            # page.update()
        else:
            new_message.error_text = "masukkan message"
            page.update()

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = ChatMessage(message)
        elif message.message_type == "login_message":
            m = ft.Text(message.text, italic=True, color=ft.colors.BLACK45, size=12)
        chat.controls.append(m)
        page.update()

    # Upload file
    def dialog_picker(e: FilePickerResultEvent):
        for x in e.files:
            if x.path is not None:
                file_name = os.path.basename(x.path)
                directory = f"uploads/{file_name}"
                shutil.copy(x.name, directory)

                file_location.value = directory
                file_location.update()

                chat_message = Message(
                    page.session.get("user_name"),
                    f"Uploaded file: {file_name}",
                    message_type="chat_message"
                )
                page.pubsub.send_all(chat_message)
                file_location.value = ""
        page.update()

    page.pubsub.subscribe(on_message)

    # A dialog asking for a user display name
    join_user_name = ft.TextField(
        label="Enter your name to join the chat",
        autofocus=True,
        on_submit=join_chat_click,
    )
    page.dialog = ft.AlertDialog(
        open=True,
        modal=True,
        title=ft.Text("Welcome!"),
        content=ft.Column([join_user_name], width=300, height=70, tight=True),
        actions=[ft.ElevatedButton(text="Join chat", on_click=join_chat_click)],
        actions_alignment="end",
    )

    # Chat messages
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True
    )

    # A new message entry form
    new_message = ft.TextField(
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=send_message_click,
    )

    mypick = FilePicker(on_result=dialog_picker)
    page.overlay.append(mypick)
    # Add everything to the page
    page.add(
        ft.Container(
            content=chat,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=5,
            padding=10,
            expand=True,
        ),
        ft.Row(
            [
                new_message,
                ft.IconButton(
                    icon=ft.icons.UPLOAD_ROUNDED,
                    tooltip="Upload file",
                    on_click=lambda _: mypick.pick_files(),
                ),
                ft.IconButton(
                    icon=ft.icons.SEND_ROUNDED,
                    tooltip="Send message",
                    on_click=send_message_click,
                ),
            ]
        ),
    )

ft.app(port=8550, target=main, view=ft.WEB_BROWSER)
#
#
# def main(page: ft.page):
#     def btn_click(e):
#         if not cmd.value:
#             cmd.error_text = "masukkan command"
#             page.update()
#         else:
#             txt = cmd.value
#             lv.controls.append(ft.Text(f"command: {txt}"))
#             txt = cc.proses(txt)
#             lv.controls.append(ft.Text(f"result {cc.tokenid}: {txt}"))
#             cmd.value=""
#             page.update()
#
#     # cc = ChatClient()
#
#
#     lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
#     cmd = ft.TextField(label="text field", width=1000)
#     send = ft.ElevatedButton("Send", on_click=btn_click)
#     textField = ft.Row(controls=[cmd, send], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
#     page.add(lv)
#     page.add(textField)
#
#
# if __name__=='__main__':
#     ft.app(target=main, view=ft.WEB_BROWSER)
#     # if (ON_WEB=="1"):
#     #     ft.app(target=main,view=ft.WEB_BROWSER,port=8550)
#     # else:
#     #     ft.app(target=main)
#
