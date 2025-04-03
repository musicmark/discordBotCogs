import discord, os, json, datetime, asyncio, io
from discord import ui, ButtonStyle, app_commands
from discord.ext import commands, tasks

# 1 = mobile
# 2 = desktop
mod = 2
if mod == 1:
    file_path = "/storage/emulated/0/discord_bot/7bg_bus"
elif mod == 2:
    file_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
else:
    print("mod error")
    exit()

votes = {}
admin = [622098032854433813, 1009612327236157511]

class PlayerCheckButton(ui.View):
    def __init__(self, vote_name, bet_player, token, bet_token, plus):
        super().__init__()
        self.vote_name = vote_name
        self.bet_player = bet_player
        self.token = token
        self.bet_token = bet_token
        self.plus = plus
    
    @ui.button(label="네", style=ButtonStyle.blurple, custom_id="PlayerCheckButton:yes_button")
    async def yes_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        interaction.followup
        with open(f"{file_path}/data/event/AWC2025/tokens/{interaction.user.id}.bin", 'wb') as f:
            f.write((self.token - self.bet_token).to_bytes(((self.token - self.bet_token).bit_length() + 7) // 8, byteorder="little"))
        if self.plus:
            old_bet_token = votes[self.vote_name][self.bet_player]["bet_users"][str(interaction.user.id)]
            votes[self.vote_name][self.bet_player]["bet_users"][str(interaction.user.id)] += self.bet_token
        else:
            votes[self.vote_name][self.bet_player]["bet_users"][str(interaction.user.id)] = self.bet_token
        votes[self.vote_name]["token_total"] += self.bet_token
        votes[self.vote_name][self.bet_player]["token"] += self.bet_token
        if votes[self.vote_name][self.bet_player]["max_token"] < self.bet_token:
            votes[self.vote_name][self.bet_player]["max_token"] = self.bet_token
        '' if str(interaction.user.id) in votes[self.vote_name]["bet_users"] else votes[self.vote_name]["bet_users"].append(interaction.user.id)
        await interaction.followup.send(f"{votes[self.vote_name][self.bet_player]["name"]}의 승리를 예측하였습니다.\n({f"{old_bet_token:,} + {self.bet_token:,}" if self.plus else f"{self.bet_token:,}"}<:AWC_token:1332385291054612500> 사용됨.)", ephemeral=True)
    
    @ui.button(label="취소 : 메시지 닫기", style=ButtonStyle.grey, disabled=True)
    async def disabled_button(self):
        pass

class VotingTokenInputModal(ui.Modal):
    def __init__(self, vote_name, bet_player, token, plus, user=None):
        super().__init__(title=f"{votes[vote_name][bet_player]["name"]}에게 베팅할 토큰 수 입력", timeout=3600)
        self.vote_name = vote_name
        self.bet_player = bet_player
        self.token = token
        self.plus = plus
        self.user = user
        if plus:
            self.old_token = votes[vote_name][bet_player]["bet_users"][user]
        self.add_item(ui.TextInput(label=f"베팅할 토큰 수 {f"(이전에 베팅한 토큰 수 : {votes[vote_name][bet_player]["bet_users"][user]})" if plus else ""}", placeholder=f"본인의 토큰 보유 수({token:,})", style=discord.TextStyle.short))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        interaction.followup
        if not self.children[0].value.isdecimal():
            await interaction.followup.send("소수가 아닌 숫자만 입력할 수 있습니다.", ephemeral=True)
            return
        bet_token = int(self.children[0].value)
        if bet_token <= 0:
            await interaction.followup.send("0 이하의 숫자는 입력 할 수 없습니다.", ephemeral=True)
            return
        if bet_token > self.token:
            await interaction.followup.send("입력한 토큰 수가 보유한 토큰 수 보다 많습니다.", ephemeral=True)
            return
        await interaction.followup.send(f"{votes[self.vote_name][self.bet_player]["name"]}에게 {bet_token:,}<:AWC_token:1332385291054612500>을 베팅하시겠습니까?{f"\n이전에 베팅한 토큰 수 : {self.old_token:,}" if self.plus else ""}", view=PlayerCheckButton(self.vote_name, self.bet_player, self.token, bet_token, self.plus), ephemeral=True)
        

class VotingButtonTournament(ui.View):
    def __init__(self, p1, p2, vote_name):
        super().__init__(timeout=3600)
        
        self.vote_name = vote_name
        self.vote_button1.label = p1
        self.vote_button2.label = p2
        self.vote_button1.custom_id = "T_p1"
        self.vote_button2.custom_id = "T_p2"
        

    @ui.button(label="error", style=ButtonStyle.grey, custom_id="VotingButtonTournament:vote_button1")
    async def vote_button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open(f"{file_path}/data/event/AWC2025/tokens/{interaction.user.id}.bin", 'rb') as f:
            token = int.from_bytes(f.read(), byteorder="little")
        if not token:
            await interaction.response.send_message("보유한 토큰이 없습니다.", ephemeral=True)
            return
        if interaction.user.id in votes[self.vote_name]["bet_users"]:
            if str(interaction.user.id) in votes[self.vote_name][button.custom_id.split("_")[1]]["bet_users"]:
                await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, True, str(interaction.user.id)))
                return
            else:
                for i in range(votes[self.vote_name]["players"]):
                    if str(interaction.user.id) in votes[self.vote_name][f"p{i+1}"]["bet_users"]:
                        bet_user = f"p{i+1}"
                        break
                await interaction.response.send_message(f"이미 다른 선수의 승리을 예측하였습니다.\n(예측한 선수 : {votes[self.vote_name][bet_user]['name']})", ephemeral=True)
                return
        await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, False))

    @ui.button(label="error", style=ButtonStyle.grey, custom_id="VotingButtonTournament:vote_button2")
    async def vote_button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open(f"{file_path}/data/event/AWC2025/tokens/{interaction.user.id}.bin", 'rb') as f:
            token = int.from_bytes(f.read(), byteorder="little")
        if not token:
            await interaction.response.send_message("보유한 토큰이 없습니다.", ephemeral=True)
            return
        if interaction.user.id in votes[self.vote_name]["bet_users"]:
            if str(interaction.user.id) in votes[self.vote_name][button.custom_id.split("_")[1]]["bet_users"]:
                await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, True, str(interaction.user.id)))
                return
            else:
                for i in range(votes[self.vote_name]["players"]):
                    if str(interaction.user.id) in votes[self.vote_name][f"p{i+1}"]["bet_users"]:
                        bet_user = f"p{i+1}"
                        break
                await interaction.response.send_message(f"이미 다른 선수의 승리을 예측하였습니다.\n(예측한 선수 : {votes[self.vote_name][bet_user]['name']})", ephemeral=True)
                return
        await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, False))

class VotingButtonGroup(ui.View):
    def __init__(self, p1, p2, p3, p4, vote_name):
        super().__init__(timeout=3600)
        
        self.vote_name = vote_name
        self.vote_button1.label = p1
        self.vote_button2.label = p2
        self.vote_button3.label = p3
        self.vote_button4.label = p4
        self.vote_button1.custom_id = "G_p1"
        self.vote_button2.custom_id = "G_p2"
        self.vote_button3.custom_id = "G_p3"
        self.vote_button4.custom_id = "G_p4"

    @ui.button(label="error", style=ButtonStyle.grey, custom_id="VotingButtonGroup:vote_button1")
    async def vote_button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open(f"{file_path}/data/event/AWC2025/tokens/{interaction.user.id}.bin", 'rb') as f:
            token = int.from_bytes(f.read(), byteorder="little")
        if not token:
            await interaction.response.send_message("보유한 토큰이 없습니다.", ephemeral=True)
            return
        if interaction.user.id in votes[self.vote_name]["bet_users"]:
            if str(interaction.user.id) in votes[self.vote_name][button.custom_id.split("_")[1]]["bet_users"]:
                await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, True, str(interaction.user.id)))
                return
            else:
                for i in range(votes[self.vote_name]["players"]):
                    if str(interaction.user.id) in votes[self.vote_name][f"p{i+1}"]["bet_users"]:
                        bet_user = f"p{i+1}"
                        break
                await interaction.response.send_message(f"이미 다른 선수의 승리을 예측하였습니다.\n(예측한 선수 : {votes[self.vote_name][bet_user]['name']})", ephemeral=True)
                return
        await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, False))

    @ui.button(label="error", style=ButtonStyle.grey, custom_id="VotingButtonGroup:vote_button2")
    async def vote_button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open(f"{file_path}/data/event/AWC2025/tokens/{interaction.user.id}.bin", 'rb') as f:
            token = int.from_bytes(f.read(), byteorder="little")
        if not token:
            await interaction.response.send_message("보유한 토큰이 없습니다.", ephemeral=True)
            return
        if interaction.user.id in votes[self.vote_name]["bet_users"]:
            if str(interaction.user.id) in votes[self.vote_name][button.custom_id.split("_")[1]]["bet_users"]:
                await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, True, str(interaction.user.id)))
                return
            else:
                for i in range(votes[self.vote_name]["players"]):
                    if str(interaction.user.id) in votes[self.vote_name][f"p{i+1}"]["bet_users"]:
                        bet_user = f"p{i+1}"
                        break
                await interaction.response.send_message(f"이미 다른 선수의 승리을 예측하였습니다.\n(예측한 선수 : {votes[self.vote_name][bet_user]['name']})", ephemeral=True)
                return
        await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, False))

    @ui.button(label="error", style=ButtonStyle.grey, custom_id="VotingButtonGroup:vote_button3")
    async def vote_button3(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open(f"{file_path}/data/event/AWC2025/tokens/{interaction.user.id}.bin", 'rb') as f:
            token = int.from_bytes(f.read(), byteorder="little")
        if not token:
            await interaction.response.send_message("보유한 토큰이 없습니다.", ephemeral=True)
            return
        if interaction.user.id in votes[self.vote_name]["bet_users"]:
            if str(interaction.user.id) in votes[self.vote_name][button.custom_id.split("_")[1]]["bet_users"]:
                await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, True, str(interaction.user.id)))
                return
            else:
                for i in range(votes[self.vote_name]["players"]):
                    if str(interaction.user.id) in votes[self.vote_name][f"p{i+1}"]["bet_users"]:
                        bet_user = f"p{i+1}"
                        break
                await interaction.response.send_message(f"이미 다른 선수의 승리을 예측하였습니다.\n(예측한 선수 : {votes[self.vote_name][bet_user]['name']})", ephemeral=True)
                return
        await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, False))

    @ui.button(label="없음", style=ButtonStyle.grey, custom_id="VotingButtonGroup:vote_button4")
    async def vote_button4(self, interaction: discord.Interaction, button: discord.ui.Button):
        if button.label == "없음":
            await interaction.response.send_message("해당 버튼은 선수의 부재 혹은 기권으로 인해 `없음`으로 표기된 버튼입니다.\n다른 선수를 선택 해주시길 바랍니다.", ephemeral=True)
            return
        with open(f"{file_path}/data/event/AWC2025/tokens/{interaction.user.id}.bin", 'rb') as f:
            token = int.from_bytes(f.read(), byteorder="little")
        if not token:
            await interaction.response.send_message("보유한 토큰이 없습니다.", ephemeral=True)
            return
        if interaction.user.id in votes[self.vote_name]["bet_users"]:
            if str(interaction.user.id) in votes[self.vote_name][button.custom_id.split("_")[1]]["bet_users"]:
                await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, True, str(interaction.user.id)))
                return
            else:
                for i in range(votes[self.vote_name]["players"]):
                    if str(interaction.user.id) in votes[self.vote_name][f"p{i+1}"]["bet_users"]:
                        bet_user = f"p{i+1}"
                        break
                await interaction.response.send_message(f"이미 다른 선수의 승리을 예측하였습니다.\n(예측한 선수 : {votes[self.vote_name][bet_user]['name']})", ephemeral=True)
                return
        await interaction.response.send_modal(VotingTokenInputModal(self.vote_name, button.custom_id.split("_")[1], token, False))

class VotingTaskLoop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.reload_vote.start()
        self.bot = bot

    @tasks.loop(seconds=10)
    async def reload_vote(self):
        if self.bot.is_ready():
            with open(f"{file_path}/data/event/AWC2025/vote/vote_list.json", 'r', encoding='utf-8') as f:
                vote_list = json.load(f)
            for name in vote_list:
                for i in range(votes[name]["players"]):
                    if votes[name][f"p{i+1}"]["max_token"] is not int:
                        votes[name][f"p{i+1}"]["max_token"] = max(votes[name][f"p{i+1}"]["bet_users"].values(), default=0)
                with open(f"{file_path}/data/event/AWC2025/vote/{name}.json", 'w', encoding='utf-8') as f:
                    json.dump(votes[name],f, indent="\t", ensure_ascii=False)
                if datetime.datetime.now().timestamp() >= votes[name]["end_time"]:
                    with open(f"{file_path}/data/event/AWC2025/vote/vote_list.json", 'r', encoding='utf-8') as f:
                        vote_list = json.load(f)
                    vote_list.remove(name)
                    with open(f"{file_path}/data/event/AWC2025/vote/vote_list.json", 'w', encoding='utf-8') as f:
                        json.dump(vote_list, f, indent="\t", ensure_ascii=False)
                    await self.bot.get_channel(1314462074260164680).send(f"**{name}**의 베팅이 종료되었습니다.")

class VotesMenu(ui.Select):
    def __init__(self):
        super().__init__(options=[discord.SelectOption(label=name, value=name.replace(" ", "_")) for name in votes], max_values=1)

    async def callback(self, interaction: discord.Interaction):
        vote = votes[self.values[0].replace("_", " ")]
        text=f"# {self.values[0].replace("_", " ")}\n# "
        for i in range(vote["players"]):
            text += f"{" VS " if i else ""}{vote[f"p{i+1}"]["name"]}"
        text += "\n# ⠀\n## 실시간 예측 현황\n"
        for i in range(vote["players"]):
            if vote[f"p{i+1}"]["token"] == 0:
                text += f"{vote[f'p{i+1}']['name']} : 0% (최고 베팅 토큰 수 : 0)\n"
                continue
            text += f"{vote[f"p{i+1}"]["name"]} : {round(vote[f"p{i+1}"]["token"] / vote["token_total"] * 100 if vote["token_total"] or vote[f"p{i+1}"]["token"] else 0, 2)}% (최고 베팅 토큰 수 : {vote[f"p{i+1}"]["max_token"]:,})\n"
        not_end = vote["end_time"] >= datetime.datetime.now().timestamp()
        text += "\n승리를 예상하는 선수의 이름이 적힌 버튼을 눌러주세요!" if not_end else "\n-# 해당 예측은 베팅 기간이 아닙니다."
        await interaction.response.send_message(text, ephemeral=True, view=(VotingButtonGroup(vote[f"p1"]["name"], vote[f"p2"]["name"], vote[f"p3"]["name"], vote[f"p4"]["name"] if vote["players"] >= 4 else None, self.values[0].replace("_", " ")) if vote["players"] >= 3 else VotingButtonTournament(vote["p1"]["name"], vote["p2"]["name"], self.values[0].replace("_", " "))) if not_end else None)

class Votes(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(VotesMenu())

class JoinButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="참여하기", style=ButtonStyle.blurple, custom_id="JoinButton:join_button")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        tokens = os.listdir(f"{file_path}/data/event/AWC2025/tokens")
        if f"{interaction.user.id}.json" not in tokens:
            with open(f"{file_path}/data/event/AWC2025/tokens/{interaction.user.id}.bin", 'wb') as f:
                f.write((1000).to_bytes(((1000).bit_length() + 7) // 8, byteorder="little"))
            await interaction.response.send_message(f"AWC2025 승부예측 이밴트에 참여되었습니다!\n참여 보상으로 1,000<:AWC_token:1332385291054612500>이 지급되었습니다!", ephemeral=True)

class Main(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="내 정보", style=ButtonStyle.blurple, custom_id="Main:check_token_button")
    async def check_token_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        interaction.followup
        tokens = os.listdir(f"{file_path}/data/event/AWC2025/tokens")
        if f"{interaction.user.id}.bin" not in tokens:
            await interaction.followup.send(f"{interaction.user.mention}님은 아직 AWC2025 승부예측 이벤트에 참여를 신청하지 않으셨습니다!\n참여를 원하시면 아래 `참여하기` 버튼을 클릭 해주세요!", view=JoinButton(), ephemeral=True)
            return
        with open(f"{file_path}/data/event/AWC2025/tokens/{interaction.user.id}.bin", 'rb') as f:
            token = int.from_bytes(f.read(), byteorder="little")
        text=""
        for vote in votes:
            for p in range(1, votes[vote]["players"]+1):
                if votes[vote][f"p{p}"]["bet_users"].get(str(interaction.user.id), 0) > 0:
                    text += f"{votes[vote][f'p{p}']['name']}({vote}) : {votes[vote][f'p{p}']['bet_users'][str(interaction.user.id)]:,}<:AWC_token:1332385291054612500>\n"
        text += "없음" if len(text) == 0 else ""
        await interaction.followup.send(f"보유 토큰 수\n{token:,}<:AWC_token:1332385291054612500>\n\n참여한 예측 목록\n{text}", ephemeral=True)

    @ui.button(label="예측 목록 보기", style=ButtonStyle.blurple, custom_id="Main:show_votes_button")
    async def show_votes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        interaction.followup
        try:
            tokens = os.listdir(f"{file_path}/data/event/AWC2025/tokens")
            if f"{interaction.user.id}.bin" not in tokens:
                await interaction.followup.send(f"{interaction.user.mention}님은 아직 AWC2025 승부예측 이벤트에 참여를 신청하지 않으셨습니다!\n참여를 원하시면 아래 `참여하기` 버튼을 클릭 해주세요!", view=JoinButton(), ephemeral=True)
                return
            with open(f"{file_path}/data/event/AWC2025/vote/vote_list.json", 'r', encoding='utf-8') as f:
                vote_list = json.load(f)
            if len(vote_list) == 0:
                await interaction.followup.send("현제 진행중인 베팅이 없습니다.", ephemeral=True)
                return
            await interaction.followup.send("참여할 예측을 선택 해주세요!", view=Votes(), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"예측 목록을 불러오는 중 에러가 발생하였습니다: {e}\n해당 메시지를 복사하여 관리자에게 전달 해주세요.", ephemeral=True)
            

    @ui.button(label="규칙", style=ButtonStyle.blurple, custom_id="Main:rule_button")
    async def rule_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        interaction.followup
        with open(f"{file_path}/data/event/AWC2025/rule.txt", 'r', encoding="utf-8") as f:
            rule = f.read()
        if len(rule) == 0:
            rule = "기능 준비중..."
        await interaction.followup.send(rule, ephemeral=True)

    @ui.button(label="크레딧", custom_id="Main:credit_button")
    async def credit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        interaction.followup
        await interaction.followup.send("# AWC2025 승부예측 이벤트 크레딧\n총괄 : 뮤직마크\n기획 : 뮤직마크\n개발 : 뮤직마크\n도움 : ChatGPT, 7BG를 위한 버스 운영진\n# 출처\nAWC2025 로고(AWC 토큰 이미지에 사용됨.) : ADOFAI.gg", ephemeral=True)
                
class AWC2025Commands(app_commands.Group):
    @app_commands.command(name="create_vote")
    async def create_vote(self, interaction, name: str, vote_end_time: int, p1: str, p2: str, p3: str=None, p4: str=None):
        if interaction.user.id in admin:
            if vote_end_time <= int(datetime.datetime.now().timestamp()) or vote_end_time >= int(datetime.datetime(2025,3,1).timestamp()):
                await interaction.response.send_message("시간값이 올바르지 않습니다.")
                return
            data = {"token_total": 0, "players": 2, "p1": {"name": p1, "token": 0, "max_token": 0, "bet_users": {}}, "p2": {"name": p2, "token": 0, "max_token": 0, "bet_users": {}}, "bet_users": [], "end_time": vote_end_time}
            if p3:
                data["players"] = 3
                data["p3"] = {"name": p3, "token": 0, "max_token": 0, "bet_users": {}}
            if p4:
                data["players"] = 4
                data["p4"] = {"name": p4, "token": 0, "max_token": 0, "bet_users": {}}
            with open(f"{file_path}/data/event/AWC2025/vote/{name}.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent="\t", ensure_ascii=False)
            with open(f"{file_path}/data/event/AWC2025/vote/vote_list.json", 'r', encoding='utf-8') as f:
                vote_list = json.load(f)
            vote_list.append(name)
            with open(f"{file_path}/data/event/AWC2025/vote/vote_list.json", 'w', encoding='utf-8') as f:
                json.dump(vote_list, f, indent="\t", ensure_ascii=False)
            votes[name] = data
            await interaction.response.send_message(f"{name} 예측이 성공적으로 생성되었습니다.")
        else:
            await interaction.response.send_message("you don't have command permissions")

    @app_commands.command(name="start")
    async def start(self, interaction):
        if interaction.user.id in admin:
            channel = interaction.guild.get_channel(1317911593929146509)
            await channel.send("AWC 승부예측에 참여 해보세요!", view=Main())
        else:
            await interaction.response.send_message("you don't have command permissions")

    @app_commands.command(name="vote_end")
    async def vote_end(self, interaction, name: str, p1_rank: int, p2_rank: int, p3_rank: int = None, p4_rank: int = None):
        if interaction.user.id in admin:
            await interaction.response.defer()
            interaction.followup
            vote_list = os.listdir(f"{file_path}/data/event/AWC2025/vote")
            if f"{name}.json" in vote_list:
                await asyncio.sleep(10)
                with open(f"{file_path}/data/event/AWC2025/vote/{name}.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                r=[(p1_rank,"p1"), (p2_rank,"p2")]
                if p3_rank:
                    r.append((p3_rank,"p3"))
                if p4_rank:
                    r.append((p4_rank,"p4"))
                r.sort()
                if p3_rank:
                    rank=[p[1] for p in r][0:2]
                    winer_token = sum([data[p]["token"] for p in rank])
                else:
                    rank=[[p[1] for p in r][0]]
                    winer_token = data[rank[0]]["token"]
                for player in rank:
                    if not data[player]["token"]:
                        continue
                    for user_id in data[player]["bet_users"]:
                        with open(f"{file_path}/data/event/AWC2025/tokens/{user_id}.bin", 'rb') as f:
                            token = int.from_bytes(f.read(), byteorder="little")
                        with open(f"{file_path}/data/event/AWC2025/tokens/{user_id}.bin", 'wb') as f:
                            p = int(token + (data["token_total"] * (data[player]["bet_users"][user_id] / winer_token)))
                            f.write(p.to_bytes((p.bit_length() + 7) // 8, byteorder="little"))
    
                del votes[name]
                await interaction.followup.send(f"{name} 예측이 종료되었습니다.")
            else:
                await interaction.response.send_message("Name error.")
        else:
            await interaction.response.send_message("you don't have command permissions")
            
    @app_commands.command(name="bonus")
    async def bonus(self, interaction, vote_name: str, player_num: int, token: int):
        if interaction.user.id in admin:
            await interaction.response.defer()
            interaction.followup
            vote_list = os.listdir(f"{file_path}/data/event/AWC2025/vote")
            if f"{vote_name}.json" in vote_list:
                with open(f"{file_path}/data/event/AWC2025/vote/{vote_name}.json") as f:
                    vote_data = json.load(f)
                if f"p{player_num}" in vote_data:
                    bet_users = list(vote_data[f"p{player_num}"]["bet_users"])
                    for bet_user in bet_users:
                        with open(f"{file_path}/data/event/AWC2025/tokens/{bet_user}.bin", 'rb') as f:
                            old_token = int.from_bytes(f.read(), byteorder="little")
                        with open(f"{file_path}/data/event/AWC2025/tokens/{bet_user}.bin", 'wb') as f:
                            f.write((old_token + token).to_bytes(((1000).bit_length() + 7) // 8, byteorder="little"))
                    await interaction.followup.send(f"{vote_name}의 {player_num}번 선수의 보너스 지급이 완료되었습니다.")
                else:
                    await interaction.followup.send("선수 번호가 올바르지 않습니다.")
            else:
                await interaction.followup.send("존재하지 않는 베팅입니다.")
        else:
            await interaction.response.send_message("you don't have command permissions.")

    @app_commands.command(name="add_token")
    async def add_token(self, interaction, user: discord.Member, token: int):
        if interaction.user.id in admin:
            with open(f"{file_path}/data/event/AWC2025/tokens/{user.id}.bin", 'rb') as f:
                old_token = int.from_bytes(f.read(), byteorder="little")
            with open(f"{file_path}/data/event/AWC2025/tokens/{user.id}.bin", 'wb') as f:
                f.write((old_token + token).to_bytes(((1000).bit_length() + 7) // 8, byteorder="little"))
            await interaction.response.send_message(f"{user.mention}에게 {token} 토큰이 추가되었습니다.")
        else:
            await interaction.response.send_message("You don't have command permissions.")
    
    @app_commands.command(name="remove_token")
    async def remove_token(self, interaction, user: discord.Member, token: int):
        if interaction.user.id in admin:
            with open(f"{file_path}/data/event/AWC2025/tokens/{user.id}.bin", 'rb') as f:
                old_token = int.from_bytes(f.read(), byteorder="little")
            if old_token >= token:
                with open(f"{file_path}/data/event/AWC2025/tokens/{user.id}.bin", 'wb') as f:
                    f.write((old_token - token).to_bytes(((1000).bit_length() + 7) // 8, byteorder="little"))
                await interaction.response.send_message(f"{user.mention}에게 {token} 토큰이 제거되었습니다.")
            else:
                await interaction.response.send_message(f"{user.mention}님의 토큰 보유량이 {token}보다 적습니다.")
        else:
            await interaction.response.send_message("you don't have command permissions.")

    @app_commands.command(name="rank")
    async def rank(self, interaction, channel: discord.TextChannel):
        message = None
        if interaction.user.id in admin:
            error = 0
            while True:
                try:
                    tokens = {}
                    for file in os.listdir(f"{file_path}/data/event/AWC2025/tokens"):
                        if file.endswith(".bin"):
                            user_id = int(file.split(".")[0])
                            with open(f"{file_path}/data/event/AWC2025/tokens/{file}", 'rb') as f:
                                tokens[user_id] = int.from_bytes(f.read(), byteorder="little")
                    sorted_tokens = sorted(tokens.items(), key=lambda x: x[1], reverse=True)
                    text=""
                    for i, (user_id, token) in enumerate(sorted_tokens, 1):
                        text += f"{i}. <@{user_id}> ({token:,}<:AWC_token:1332385291054612500>)\n"
                        if i == 10:
                            break
                    embed=discord.Embed(title="<:AWC_token:1332385291054612500> AWC 토큰 보유 수 랭킹", description=text, colour=discord.Colour.blurple())
                    embed.add_field(name="", value=f"-# 동기화 시각 : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    if not message:
                        message = await channel.send(embed=embed)
                    else:
                        await message.edit(embed=embed)
                    error = 0
                    await asyncio.sleep(10)
                except:
                    error += 1
                    if error >= 5:
                        raise "rank command is not working"
                    await asyncio.sleep(30)

    @app_commands.command(name="eval")
    async def run_exec(self, interaction: discord.Interaction, code: str):
        if interaction.user.id in admin:  # Replace with your ID
            await interaction.response.defer()
            try:
                result = eval(code, globals())  # ✅ eval 사용하여 코드 실행
    
                if len(str(result)) >= 1999:  # ✅ 실행 결과만 고려
                    with io.StringIO() as f:
                        f.write(str(result))  # ✅ result 값만 저장
                        f.seek(0)
                        file = discord.File(f, filename="exec_output.txt")
                        await interaction.followup.send("Output is too long. Here is the file:", file=file)
                        return  # ✅ 두 번째 send() 실행 방지
    
                await interaction.followup.send(f"Execution Result: {result}")
            except Exception as e:
                await interaction.followup.send(f"Error: {e}")
        else:
            await interaction.response.send_message("You don't have command permissions.")




async def setup(bot: commands.Bot):
    await bot.add_cog(VotingTaskLoop(bot))
    bot.tree.add_command(AWC2025Commands(name="awc2025"))
    with open(f"{file_path}/data/event/AWC2025/vote/vote_list.json", 'r', encoding='utf-8') as f:
        vote_list = json.load(f)
    for name in vote_list:
        with open(f"{file_path}/data/event/AWC2025/vote/{name}.json", 'r', encoding='utf-8') as f:
            votes[name] = json.load(f)
        print(f"{name} is loaded")
    print("AWC2025 is now available")
