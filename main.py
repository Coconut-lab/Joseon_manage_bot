"""
구현할 기능
로블록스 자동 그룹 관리 기능 - 완성
금지어 - 완성
"""
from datetime import datetime
import disnake
from disnake.ext import commands
from disnake import ButtonStyle
from roblox import Client
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import asyncio
import re
import os

load_dotenv()

client = AsyncIOMotorClient(os.getenv("TESTDBCLIENT"))
db = client["discord_bot_db"]  # DB이름
banned_words_collection = db["banned_words"]
restricted_users_collection = db['restricted_users']
user_roles_collection = db['user_roles']
mute_logs_collection = db['mute_logs']

roblox_client = Client(os.getenv("ROBLOXTOKEN"))
BOT_TOKEN = os.getenv("BOTTOKEN")

intents = disnake.Intents.all()
bot = commands.InteractionBot(intents=intents)

TARGET_GUILD_ID = None
# TARGET_GUILD_ID = 874913710777466891 # 테스트


MUTE_ROLE_ID = 795147706237714433
# MUTE_ROLE_ID = 1272135394669891621  # 테스트
ADMIN_ROLE_ID = [789359681776648202, 1185934968636067921, 1101725365342306415]
# ADMIN_ROLE_ID = [1101725365342306415]  # 테스트
MTA_RGO_MND = [597769848256200717, 1270777112982323274, 1270777180921528391, 1185934968636067921]
MND_MTA = [597769848256200717, 1270777112982323274, 1185934968636067921]
MND_RGO = [597769848256200717, 1270777180921528391]

joseon_group_id = "4654286"
MTA_group_id = "4654485"
RGO_group_id = "4654514"
hanyang_group_id = "4766967"
Justice_group_id = "5815247"
Bandit_group_id = "8147242"

RANK_ROLES = {
    96: "대장",
    92: "중군",
    88: "천총",
    84: "별장",
    80: "파총",
    76: "종사관",
    72: "초관",
    64: "기총",
    60: "대총",
    38: "별무사",
    34: "뇌자",
    30: "표하군",
    26: "마병/기사",
    22: "별파진",
    20: "사수",
    18: "살수(등패)",
    14: "살수(창)",
    10: "포수",
    1: "무소속",
    # 여기에 새로운 랭크와 역할을 쉽게 추가할 수 있습니다.
}

MTA_ROLES = {
    100: "참상관",
    80: "참하관",
    70: "잡직",
    50: "표하군",
    10: "고참병",
    7: "일등졸",
    5: "이등졸",
    2: "삼등졸",
    1: "대년군",
}

RGO_ROLES = {
    80: "참상관",
    65: "참하관",
    50: "장교",
    45: "잡직",
    20: "표하군",
    17: "별무사",
    15: "가전별초",
    14: "경기사",
    11: "천보초",
    7: "포수초",
    1: "보충병"
}

BANDIT_ROLES = {
    1: "시정 무뢰배",
    2: "산자락 들개",
    4: "범바위 늑대",
    30: "영은문 불한당",
    38: "좌촌리 무쇠주먹",
    40: "치마바위 올빼미",
    50: "중앙군 변절자"
}

JUSTICE_ROLES = {
    1: "[兵卒] 나장",
    2: "[參下] 명률",
    3: "[參下] 녹사",
    4: "[參下] 서리",
    7: "[參上] 좌랑",
    11: "[參上] 정랑"
}

async def load_banned_words_from_db():
    banned_words = []
    async for word in banned_words_collection.find():
        banned_words.append({
            'word': word['word'],
            'added_by': word['added_by'],
            'added_at': word['added_at'],
        })
    return banned_words


async def load_restricted_users_from_db():
    return [user['user_id'] async for user in restricted_users_collection.find()]


async def load_user_roles_from_db():
    return {str(user['user_id']): user['roles'] async for user in user_roles_collection.find()}


async def save_banned_word_to_db(word, info):
    await banned_words_collection.update_one(
        {'word': word},
        {'$set': {
            'added_by': info['added_by'],
            'added_at': info['added_at']
        }},
        upsert=True
    )


def remove_banned_word_from_db(word):
    banned_words_collection.delete_one({'word': word})


def save_restricted_user_to_db(user_id):
    restricted_users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'user_id': user_id}},
        upsert=True
    )


def remove_restricted_user_from_db(user_id):
    restricted_users_collection.delete_one({'user_id': user_id})


def save_user_roles_to_db(user_id, roles):
    user_roles_collection.update_one(
        {'user_id': user_id},
        {'$set': {'roles': roles}},
        upsert=True
    )


def remove_user_roles_from_db(user_id):
    user_roles_collection.delete_one({'user_id': user_id})


# 초기 데이터 로드
banned_words_data = {
    "words": load_banned_words_from_db(),
    "restricted_users": load_restricted_users_from_db(),
    "user_roles": load_user_roles_from_db()
}


# 기존의 save_banned_words 함수 대체
def save_banned_words(data):
    for word, info in data['words'].items():
        save_banned_word_to_db(word, info)

    for user_id in data['restricted_users']:
        save_restricted_user_to_db(user_id)

    for user_id, roles in data['user_roles'].items():
        save_user_roles_to_db(int(user_id), roles)


@bot.event
async def on_ready():
    print("Bot is Ready!")


@bot.event
async def on_message(message):
    try:
        if message.author == bot.user:
            return

        if TARGET_GUILD_ID and message.guild.id != TARGET_GUILD_ID:
            return

        if not message.content:
            return

        content = message.content
        restricted_users = await load_restricted_users_from_db()
        banned_words = await load_banned_words_from_db()

        if message.author.id in restricted_users:
            for word_info in banned_words:
                if word_info['word'] in content:
                    await message.channel.send(f"{message.author.mention}, 입을 잘못 놀리셔서 꼬메버렸슈다")
                    await message.delete()
                    await mute_user(message.author, message.guild, content, word_info['word'])
                    return

    except Exception as e:
        await message.channel.send(f"메시지 처리 중 오류 발생: {str(e)}")


class MuteLogsPaginator(disnake.ui.View):
    def __init__(self, logs, author):
        super().__init__(timeout=60)
        self.logs = logs
        self.author = author
        self.current_page = 0
        self.logs_per_page = 5

    @disnake.ui.button(label="이전", style=ButtonStyle.primary, disabled=True)
    async def previous_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.user != self.author:
            await inter.response.send_message("다른 사람의 버튼은 누를 수 없습니다유", ephemeral=True)
            return
        self.current_page -= 1
        await self.update_message(inter)

    @disnake.ui.button(label="다음", style=ButtonStyle.primary)
    async def next_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.user != self.author:
            await inter.response.send_message("다른 사람의 버튼은 누를 수 없습니다유", ephemeral=True)
            return
        self.current_page += 1
        await self.update_message(inter)

    @disnake.ui.button(label="삭제", style=ButtonStyle.danger)
    async def delete_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.user != self.author:
            await inter.response.send_message("다른 사람의 버튼은 누를 수 없습니다유", ephemeral=True)
            return
        await inter.message.delete()

    async def update_message(self, inter: disnake.MessageInteraction):
        embed = self.create_embed()
        self.update_buttons()
        await inter.response.edit_message(embed=embed, view=self)

    def create_embed(self):
        start = self.current_page * self.logs_per_page
        end = start + self.logs_per_page
        current_logs = self.logs[start:end]

        embed = disnake.Embed(title=f"{self.logs[0]['username']}의 뮤트 기록 (페이지 {self.current_page + 1}/{self.max_pages})",
                              color=disnake.Color.red())

        for log in current_logs:
            muted_at = log['muted_at'].strftime('%Y-%m-%d %H:%M:%S')

            if 'banned_word' in log:
                mute_type = "금지어 뮤트"
                reason = f"금지어 사용: {log['banned_word']}"
                muted_by = "자동 시스템 (금지어)"
            else:
                mute_type = "일반 뮤트"
                reason = log.get('reason', '알 수 없음')
                end_time = log.get('end_time', None)
                if end_time:
                    end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
                    duration = log.get('duration', None)
                    if duration is not None:
                        duration = timedelta(seconds=duration)
                        duration_str = format_duration(duration)
                    else:
                        duration_str = "알 수 없음"
                else:
                    end_time = "알 수 없음"
                    duration_str = "알 수 없음"

                muted_by = log.get('muted_by', {}).get('name', '알 수 없음')

            embed.add_field(
                name=f"뮤트 일시: {muted_at} ({mute_type})",
                value=f"{'종료 시간: ' + end_time if 'end_time' in log else ''}\n"
                      f"{'지속 시간: ' + duration_str if 'duration' in log else ''}\n"
                      f"사유: {reason}\n"
                      f"처리자: {muted_by}",
                inline=False
            )

        return embed

    def update_buttons(self):
        self.previous_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == self.max_pages - 1)

    @property
    def max_pages(self):
        return (len(self.logs) - 1) // self.logs_per_page + 1


@bot.slash_command()
async def test(inter):
    await inter.response.send_message("저 정신 꽈악 붙잡고 있어유👨🏿‍🌾")


@bot.slash_command(name="그룹명령어", description="그룹 관리 명령어 리스트")
async def list(inter):
    try:
        # 임베드 헤더
        embed = disnake.Embed(
            title="명령어 리스트",
            color=disnake.Color.dark_blue()
        )

        # 임베드 필드
        embed.add_field(name="test", value="봇 작동 유무 확인용 명령어 입니다.", inline=False)
        embed.add_field(name="설명서", value="기본적인 그룹 관리 명령어 설명서 입니다.", inline=False)
        embed.add_field(name="조선군관리", value="다수 혹은 한명의 조선군 랭크를 관리하는 명령어 입니다.", inline=False)
        embed.add_field(name="도감군관리", value="다수 혹은 한명의 도감군 랭크를 관리하는 명령어 입니다.", inline=False)
        embed.add_field(name="어영군관리", value="다수 혹은 한명의 어영군 랭크를 관리하는 명령어 입니다.", inline=False)
        embed.add_field(name="조선군랭크", value="조선군 그룹 랭크 번호 리스트 입니다.", inline=False)
        embed.add_field(name="도감군랭크", value="도감군 그룹 랭크 번호 리스트 입니다.", inline=False)
        embed.add_field(name="어영군랭크", value="어영군 그룹 랭크 번호 리스트 입니다.", inline=False)
        embed.add_field(name="형조랭크", value="형조 그룹 랭크 번호 리스트 입니다.", inline=False)
        embed.add_field(name="산적랭크", value="산적 그룹 랭크 번호 리스트 입니다.", inline=False)
        embed.add_field(name="호적승인", value="천민에서 상민으로 그룹 랭크 조정 **호조 권한**", inline=False)

        await inter.response.send_message(embed=embed)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")


@bot.slash_command(name="금지어명령어", description="그룹 관리 명령어 리스트")
async def list(inter):
    try:
        # 임베드 헤더
        embed = disnake.Embed(
            title="명령어 리스트",
            color=disnake.Color.brand_red()
        )

        # 임베드 필드
        embed.add_field(name="금지어추가", value="금지어 단어를 추가합니다.", inline=False)
        embed.add_field(name="금지어제거", value="금지어 목록 중에 있는 단어를 제거합니다.", inline=False)
        embed.add_field(name="금지어목록", value="금지어 목록을 확인합니다.", inline=False)
        embed.add_field(name="제한사용자추가", value="금지어 규칙이 적용될 사용자를 추가합니다.", inline=False)
        embed.add_field(name="제한사용자제거", value="금지어 규칙이 적용될 사용자를 제거합니다.", inline=False)
        embed.add_field(name="제한사용자목록", value="금지어 규칙이 적용된 사용자 목록을 확인합니다.", inline=False)
        embed.add_field(name="뮤트해제", value="오직 **금지어**로 뮤트된 사람을 풀어줍니다.", inline=False)

        await inter.response.send_message(embed=embed)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")


@bot.slash_command(name="설명서", description="기본적인 그룹 관리 명령어 설명서")
async def manual(inter):
    try:
        # 임베드 헤더
        embed = disnake.Embed(
            title="설명서",
            description="기본적인 그룹 관리 명령어를 알려드립니다.",
            color=disnake.Color.yellow(),
        )

        # 임베드 필드
        embed.add_field(name="조선(도감,어영)군관리 명령어", value="/조선(도감,어영)군관리 이름 랭크번호 / 이름2 랭크번호 ...", inline=False)
        embed.add_field(name="조선(도감,어영)군랭크 명령어", value="각 그룹의 랭크 번호를 알려주는 명령어 입니다. 먼저 확인 후에 관리 명령어를 사용하세요.",
                        inline=False)
        embed.add_field(name="호적신고 명령어", value="호조만 사용할 수 있는 명령어로 로블록스 이름을 입력하면 해당 사람을 천민에서 상민으로 조정합니다.", inline=False)

        # 임베드 풋터
        embed.set_footer(
            text="더 자세한 문의는 병조참판 차지철에게 DM",
        )

        await inter.response.send_message(embed=embed)


    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")


@bot.slash_command(name="조선군랭크", description="조선군 그룹 랭크 번호 리스트")
async def list(inter):
    try:
        if not any(role.id in MTA_RGO_MND for role in inter.author.roles):
            await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
            return

        # 임베드 헤더
        embed = disnake.Embed(
            title="랭크 번호 리스트",
            color=disnake.Color.dark_gray()
        )

        for num, rank in sorted(RANK_ROLES.items(), reverse=True):
            embed.add_field(name=num, value=rank, inline=True)

        await inter.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")


@bot.slash_command(name="도감군랭크", description="도감군 그룹 랭크 번호 리스트")
async def list(inter):
    try:
        if not any(role.id in MND_MTA for role in inter.author.roles):
            await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
            return

        # 임베드 헤더
        embed = disnake.Embed(
            title="랭크 번호 리스트",
            color=disnake.Color.dark_gray()
        )

        for num, rank in sorted(MTA_ROLES.items(), reverse=True):
            embed.add_field(name=num, value=rank, inline=True)

        await inter.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")


@bot.slash_command(name="어영군랭크", description="어영군 그룹 랭크 번호 리스트")
async def list(inter):
    try:
        if not any(role.id in MND_RGO for role in inter.author.roles):
            await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
            return

        # 임베드 헤더
        embed = disnake.Embed(
            title="랭크 번호 리스트",
            color=disnake.Color.dark_gray()
        )

        for num, rank in sorted(RGO_ROLES.items(), reverse=True):
            embed.add_field(name=num, value=rank, inline=True)

        await inter.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")


@bot.slash_command(name="조선군관리", description="다수 혹은 한명의 조선군 랭크를 관리하는 명령어")
async def ranks(inter: disnake.ApplicationCommandInteraction, *, 이름_랭크번호: str):
    await inter.response.defer()
    try:
        if not any(role.id in MTA_RGO_MND for role in inter.author.roles):
            await inter.followup.send("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
            return

        lines = 이름_랭크번호.split("/")
        usernames = []
        rank_numbers = []

        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2:
                usernames.append(parts[0])
                rank_numbers.append(int(parts[1]))

        results = []
        for username, rank in zip(usernames, rank_numbers):
            try:
                user = await roblox_client.get_user_by_username(username)
                if user is None:
                    results.append(f"{username}은(는) 효도 없는 사용자명이여유")
                    continue

                group = await roblox_client.get_group(joseon_group_id)
                group_member = group.get_member(user.id)

                if group_member is None:
                    results.append(f"{username}님은 그룹에 안 끼어 있구먼유")
                    continue

                if rank in RANK_ROLES:
                    role = RANK_ROLES[rank]
                    try:
                        await group.set_rank(user.id, rank)
                        results.append(f"{username}님의 랭크를 {role}({rank})로 바꿨구먼유")
                    except Exception as e:
                        error_message = str(e)
                        if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                            results.append(f"{username}님은 벌써 {role}({rank}) 랭크여유")
                        else:
                            raise  # 다른 종류의 오류라면 상위 예외 처리로 전달
                else:
                    results.append(f"{username}님한테 없는 랭크({rank})를 지정해 놨구먼유")

            except Exception as e:
                results.append(f"{username}님 처리 중 오류 발생: {str(e)}")

            await asyncio.sleep(0.5)  # API 요청 사이에 짧은 대기 시간 추가

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))
    except Exception as e:
        await inter.followup.send(f"{inter.user.mention} 전체 처리 중 에러가 발생했습니다: {e}")


@bot.slash_command(name="도감군관리", description="다수 혹은 한명의 도감군 랭크를 관리하는 명령어")
async def ranks(inter: disnake.ApplicationCommandInteraction, *, 이름_랭크번호: str):
    await inter.response.defer()
    try:
        if not any(role.id in MND_MTA for role in inter.author.roles):
            await inter.followup.send("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
            return

        lines = 이름_랭크번호.split("/")
        usernames = []
        rank_numbers = []

        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2:
                usernames.append(parts[0])
                rank_numbers.append(int(parts[1]))

        results = []
        for username, rank in zip(usernames, rank_numbers):
            try:
                user = await roblox_client.get_user_by_username(username)
                if user is None:
                    results.append(f"{username}은(는) 효도 없는 사용자명이여유")
                    continue

                group = await roblox_client.get_group(MTA_group_id)
                group_member = group.get_member(user.id)

                if group_member is None:
                    results.append(f"{username}님은 그룹에 안 끼어 있구먼유")
                    continue

                if rank in MTA_ROLES:
                    role = MTA_ROLES[rank]
                    try:
                        await group.set_rank(user.id, rank)
                        results.append(f"{username}님의 랭크를 {role}({rank})로 바꿨구먼유")
                    except Exception as e:
                        error_message = str(e)
                        if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                            results.append(f"{username}님은 벌써 {role}({rank}) 랭크여유")
                        else:
                            raise  # 다른 종류의 오류라면 상위 예외 처리로 전달
                else:
                    results.append(f"{username}님한테 없는 랭크({rank})를 지정해 놨구먼유")

            except Exception as e:
                results.append(f"{username}님 처리 중 오류 발생: {str(e)}")

            await asyncio.sleep(0.5)  # API 요청 사이에 짧은 대기 시간 추가

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))
    except Exception as e:
        await inter.followup.send(f"{inter.user.mention} 전체 처리 중 에러가 발생했습니다: {e}")


@bot.slash_command(name="어영군관리", description="다수 혹은 한명의 어영군 랭크를 관리하는 명령어")
async def ranks(inter: disnake.ApplicationCommandInteraction, *, 이름_랭크번호: str):
    await inter.response.defer()
    try:
        if not any(role.id in MND_RGO for role in inter.author.roles):
            await inter.followup.send("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
            return

        lines = 이름_랭크번호.split("/")
        usernames = []
        rank_numbers = []

        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2:
                usernames.append(parts[0])
                rank_numbers.append(int(parts[1]))

        results = []
        for username, rank in zip(usernames, rank_numbers):
            try:
                user = await roblox_client.get_user_by_username(username)
                if user is None:
                    results.append(f"{username}은(는) 효도 없는 사용자명이여유")
                    continue

                group = await roblox_client.get_group(RGO_group_id)
                group_member = group.get_member(user.id)

                if group_member is None:
                    results.append(f"{username}님은 그룹에 안 끼어 있구먼유")
                    continue

                if rank in RGO_ROLES:
                    role = RGO_ROLES[rank]
                    try:
                        await group.set_rank(user.id, rank)
                        results.append(f"{username}님의 랭크를 {role}({rank})로 바꿨구먼유")
                    except Exception as e:
                        error_message = str(e)
                        if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                            results.append(f"{username}님은 벌써 {role}({rank}) 랭크여유")
                        else:
                            raise  # 다른 종류의 오류라면 상위 예외 처리로 전달
                else:
                    results.append(f"{username}님한테 없는 랭크({rank})를 지정해 놨구먼유")

            except Exception as e:
                results.append(f"{username}님 처리 중 오류 발생: {str(e)}")

            await asyncio.sleep(0.5)  # API 요청 사이에 짧은 대기 시간 추가

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))
    except Exception as e:
        await inter.followup.send(f"{inter.user.mention} 전체 처리 중 에러가 발생했습니다: {e}")


@bot.slash_command(name="호적승인", description="천민에서 상민으로 그룹 랭크 조정")
@commands.has_role(695978137196036163)
async def rank(inter: disnake.ApplicationCommandInteraction, 이름들: str):
    await inter.response.defer()

    names = re.split(r'[/,\s]+', 이름들.strip())
    names = [name for name in names if name]  # 빈 문자열 제거

    results = []

    for name in names:
        try:
            user = await roblox_client.get_user_by_username(name)

            if user is None:
                results.append(f"{name}은(는) 효도 없는 사용자명이여유")
                continue

            group = await roblox_client.get_group(hanyang_group_id)
            group_member = group.get_member(user.id)

            if group_member is None:
                results.append(f"{name}님은 그룹에 안 끼어 있구먼유")
                continue

            try:
                await group.set_rank(user.id, 20)
                results.append(f"{name}님 랭크를 상민으로 바꿨구먼유")
            except Exception as e:
                error_message = str(e)
                if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                    results.append(f"{name}님은 벌써 상민이여유")
                elif "401 Unauthorized" in error_message:
                    results.append(f"{name}님은 벌써 상민 이상 랭크라서 바꿀 수 없구먼유")
                else:
                    results.append(f"{name}님 처리 중 오류 발생: {str(e)}")

        except Exception as e:
            results.append(f"{name}님 처리 중 오류 발생: {str(e)}")

    await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))


@bot.slash_command(name="형조관리", description="다수 혹은 한명의 형조 랭크를 관리하는 명령어")
@commands.has_role(1285848601997742214)
async def ranks(inter: disnake.ApplicationCommandInteraction, *, 이름_랭크번호: str):
    await inter.response.defer()
    try:
        lines = 이름_랭크번호.split("/")
        usernames = []
        rank_numbers = []

        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2:
                usernames.append(parts[0])
                rank_numbers.append(int(parts[1]))

        results = []
        for username, rank in zip(usernames, rank_numbers):
            try:
                user = await roblox_client.get_user_by_username(username)
                if user is None:
                    results.append(f"{username}은(는) 효도 없는 사용자명이여유")
                    continue

                group = await roblox_client.get_group(Justice_group_id)
                group_member = group.get_member(user.id)

                if group_member is None:
                    results.append(f"{username}님은 그룹에 안 끼어 있구먼유")
                    continue

                if rank in JUSTICE_ROLES:
                    role = JUSTICE_ROLES[rank]
                    try:
                        await group.set_rank(user.id, rank)
                        results.append(f"{username}님의 랭크를 {role}({rank})로 바꿨구먼유")
                    except Exception as e:
                        error_message = str(e)
                        if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                            results.append(f"{username}님은 벌써 {role}({rank}) 랭크여유")
                        else:
                            raise  # 다른 종류의 오류라면 상위 예외 처리로 전달
                else:
                    results.append(f"{username}님한테 없는 랭크({rank})를 지정해 놨구먼유")

            except Exception as e:
                results.append(f"{username}님 처리 중 오류 발생: {str(e)}")

            await asyncio.sleep(0.5)  # API 요청 사이에 짧은 대기 시간 추가

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))
    except Exception as e:
        await inter.followup.send(f"{inter.user.mention} 전체 처리 중 에러가 발생했습니다: {e}")


@bot.slash_command(name="산적관리", description="다수 혹은 한명의 산적 랭크를 관리하는 명령어")
@commands.has_role(1273999512070783027)
async def ranks(inter: disnake.ApplicationCommandInteraction, *, 이름_랭크번호: str):
    await inter.response.defer()
    try:
        lines = 이름_랭크번호.split("/")
        usernames = []
        rank_numbers = []

        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2:
                usernames.append(parts[0])
                rank_numbers.append(int(parts[1]))

        results = []
        for username, rank in zip(usernames, rank_numbers):
            try:
                user = await roblox_client.get_user_by_username(username)
                if user is None:
                    results.append(f"{username}은(는) 효도 없는 사용자명이여유")
                    continue

                group = await roblox_client.get_group(Bandit_group_id)
                group_member = group.get_member(user.id)

                if group_member is None:
                    results.append(f"{username}님은 그룹에 안 끼어 있구먼유")
                    continue

                if rank in BANDIT_ROLES:
                    role = BANDIT_ROLES[rank]
                    try:
                        await group.set_rank(user.id, rank)
                        results.append(f"{username}님의 랭크를 {role}({rank})로 바꿨구먼유")
                    except Exception as e:
                        error_message = str(e)
                        if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                            results.append(f"{username}님은 벌써 {role}({rank}) 랭크여유")
                        else:
                            raise  # 다른 종류의 오류라면 상위 예외 처리로 전달
                else:
                    results.append(f"{username}님한테 없는 랭크({rank})를 지정해 놨구먼유")

            except Exception as e:
                results.append(f"{username}님 처리 중 오류 발생: {str(e)}")

            await asyncio.sleep(0.5)  # API 요청 사이에 짧은 대기 시간 추가

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))
    except Exception as e:
        await inter.followup.send(f"{inter.user.mention} 전체 처리 중 에러가 발생했습니다: {e}")


@bot.slash_command(name="금지어추가", description="하나 이상의 금지어를 추가합니다. 여러 단어는 띄어쓰기로 구분합니다.")
async def add_banned_words(inter: disnake.ApplicationCommandInteraction, 단어들: str):
    if not any(role.id in ADMIN_ROLE_ID for role in inter.author.roles):
        await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
        return

    words = 단어들.split()
    added_words = []
    already_exists = []

    for word in words:
        # 데이터베이스에서 단어 검색
        existing_word = await banned_words_collection.find_one({'word': word})
        if not existing_word:
            info = {
                "word": word,
                "added_by": str(inter.author.id),
                "added_at": datetime.now().isoformat(),
            }
            # MongoDB에 저장
            await banned_words_collection.update_one(
                {'word': word},
                {'$set': info},
                upsert=True
            )
            added_words.append(word)
        else:
            already_exists.append(word)

    response = ""
    if added_words:
        response += f"댕 금지어가 더 붙었어유: {', '.join(added_words)}\n"
    if already_exists:
        response += f"댕 단어는 벌써 금지어 목록에 있어유: {', '.join(already_exists)}"
    if not response:
        response = "더 붙은 금지어가 읎습니다유"

    await inter.response.send_message(response)


@bot.slash_command(name="금지어제거", description="금지어를 제거합니다.")
async def remove_banned_word(inter: disnake.ApplicationCommandInteraction, 단어들: str):
    if not any(role.id in ADMIN_ROLE_ID for role in inter.author.roles):
        await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
        return

    words = 단어들.split()
    removed_words = []
    not_found_words = []

    for word in words:
        result = await banned_words_collection.delete_one({'word': word})
        if result.deleted_count > 0:
            removed_words.append(word)
        else:
            not_found_words.append(word)

    response = ""
    if removed_words:
        response += f"댕 금지어가 빠졌습니다유: {', '.join(removed_words)}\n"
    if not_found_words:
        response += f"댕 말씀은 금지어 목록에 읎습니다유: {', '.join(not_found_words)}\n"
    if not response:
        response = "빠진 금지어가 읎습니다유"

    await inter.response.send_message(response)


@bot.slash_command(name="금지어목록", description="현재 금지어를 확인합니다.")
async def list_banned_words(inter: disnake.ApplicationCommandInteraction):
    if not any(role.id in ADMIN_ROLE_ID for role in inter.author.roles):
        await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
        return

    await inter.response.defer()

    try:
        banned_words = await load_banned_words_from_db()

        if banned_words:
            embeds = []
            for i in range(0, len(banned_words), 5):  # 10개씩 표시
                embed = disnake.Embed(title="현재 금지어 목록", color=disnake.Color.red())
                embed.set_footer(text=f"페이지 {i // 5 + 1}/{-(-len(banned_words) // 5)}")

                for j, word_info in enumerate(banned_words[i:i + 5], 1):
                    added_by = await bot.fetch_user(int(word_info['added_by']))
                    added_at = datetime.fromisoformat(word_info['added_at']).strftime('%Y-%m-%d %H:%M:%S')
                    field_value = f"추가자: {added_by.name}\n추가일: {added_at}"
                    embed.add_field(name=f"{i + j}. {word_info['word']}", value=field_value, inline=False)

                embeds.append(embed)

            class BannedWordsPaginator(disnake.ui.View):
                def __init__(self, embeds, author):
                    super().__init__(timeout=60)
                    self.embeds = embeds
                    self.index = 0
                    self.author = author

                @disnake.ui.button(label="이전", style=disnake.ButtonStyle.blurple)
                async def previous(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                    if interaction.user.id != self.author.id:
                        await interaction.response.send_message("이 버튼은 명령어를 사용한 사람만 누를 수 있습니다.", ephemeral=True)
                        return
                    if self.index > 0:
                        self.index -= 1
                        await interaction.response.edit_message(embed=self.embeds[self.index])

                @disnake.ui.button(label="다음", style=disnake.ButtonStyle.blurple)
                async def next(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                    if interaction.user.id != self.author.id:
                        await interaction.response.send_message("이 버튼은 명령어를 사용한 사람만 누를 수 있습니다.", ephemeral=True)
                        return
                    if self.index < len(self.embeds) - 1:
                        self.index += 1
                        await interaction.response.edit_message(embed=self.embeds[self.index])

                @disnake.ui.button(label="삭제", style=disnake.ButtonStyle.red)
                async def delete(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                    if interaction.user.id != self.author.id:
                        await interaction.response.send_message("이 버튼은 명령어를 사용한 사람만 누를 수 있습니다.", ephemeral=True)
                        return
                    await interaction.message.delete()

            paginator = BannedWordsPaginator(embeds, inter.author)
            await inter.followup.send(embed=embeds[0], view=paginator)
        else:
            await inter.followup.send("지금 금지어 목록이 텅 비었습니다유")
    except Exception as e:
        await inter.followup.send(f"오류가 발생했습니다: {str(e)}")


@bot.slash_command(name="제한사용자추가", description="금지어 규칙이 적용될 사용자를 추가합니다.")
async def add_restricted_user(inter: disnake.ApplicationCommandInteraction, 사용자: disnake.User):
    if not any(role.id in ADMIN_ROLE_ID for role in inter.author.roles):
        await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
        return

    user_id = 사용자.id
    try:
        existing_user = await restricted_users_collection.find_one({'user_id': user_id})

        if not existing_user:
            # 사용자 추가
            result = await restricted_users_collection.insert_one({'user_id': user_id})

            if result.inserted_id:
                await inter.response.send_message(f"사용자 {사용자}이(가) 제한 목록에 들어갔습니다유")
            else:
                await inter.response.send_message(f"사용자 {사용자} 추가 중 오류가 발생했습니다유")
        else:
            await inter.response.send_message(f"사용자 {사용자}은(는) 벌써 제한 목록에 들어 있습니다유")
    except Exception as e:
        await inter.response.send_message(f"오류가 발생했습니다: {str(e)}")


@bot.slash_command(name="제한사용자제거", description="금지어 규칙이 적용되는 사용자를 제거합니다.")
async def remove_restricted_user(inter: disnake.ApplicationCommandInteraction, 사용자: disnake.User):
    if not any(role.id in ADMIN_ROLE_ID for role in inter.author.roles):
        await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
        return

    user_id = 사용자.id

    result = await restricted_users_collection.delete_one({'user_id': user_id})
    if result.deleted_count > 0:
        await inter.response.send_message(f"사용자 {사용자}이(가) 제한 목록에서 빠졌습니다유")
    else:
        await inter.response.send_message(f"사용자 {사용자}은(는) 제한 목록에 읎습니다유")


@bot.slash_command(name="제한사용자목록", description="금지어 규칙이 적용되는 사용자 목록을 확인합니다.")
async def list_restricted_users(inter: disnake.ApplicationCommandInteraction):
    if not any(role.id in ADMIN_ROLE_ID for role in inter.author.roles):
        await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
        return

    await inter.response.defer()

    try:
        restricted_users = await load_restricted_users_from_db()

        if restricted_users:
            embeds = []
            for i in range(0, len(restricted_users), 10):  # 10명씩 표시
                embed = disnake.Embed(title="제한된 사용자 목록", color=disnake.Color.red())
                embed.set_footer(text=f"페이지 {i // 10 + 1}/{-(-len(restricted_users) // 10)}")

                for j, user_id in enumerate(restricted_users[i:i + 10], 1):
                    user = await bot.fetch_user(user_id)
                    embed.add_field(name=f"{i + j}. {user.name}", value=f"ID: {user_id}", inline=False)

                embeds.append(embed)

            class RestrictedUsersPaginator(disnake.ui.View):
                def __init__(self, embeds, author):
                    super().__init__(timeout=60)
                    self.embeds = embeds
                    self.index = 0
                    self.author = author

                @disnake.ui.button(label="이전", style=disnake.ButtonStyle.gray)
                async def previous(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                    if interaction.user.id != self.author.id:
                        await interaction.response.send_message("이 버튼은 명령어를 사용한 사람만 누를 수 있습니다.", ephemeral=True)
                        return
                    if self.index > 0:
                        self.index -= 1
                        await interaction.response.edit_message(embed=self.embeds[self.index])

                @disnake.ui.button(label="다음", style=disnake.ButtonStyle.gray)
                async def next(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                    if interaction.user.id != self.author.id:
                        await interaction.response.send_message("이 버튼은 명령어를 사용한 사람만 누를 수 있습니다.", ephemeral=True)
                        return
                    if self.index < len(self.embeds) - 1:
                        self.index += 1
                        await interaction.response.edit_message(embed=self.embeds[self.index])

                @disnake.ui.button(label="삭제", style=disnake.ButtonStyle.red)
                async def delete(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                    if interaction.user.id != self.author.id:
                        await interaction.response.send_message("이 버튼은 명령어를 사용한 사람만 누를 수 있습니다.", ephemeral=True)
                        return
                    await interaction.message.delete()

            paginator = RestrictedUsersPaginator(embeds, inter.author)
            await inter.followup.send(embed=embeds[0], view=paginator)
        else:
            await inter.followup.send("지금 막아놓은 사람이 한 명도 읎습니다유")
    except Exception as e:
        await inter.followup.send(f"오류가 발생했습니다: {str(e)}")


@bot.slash_command(name="뮤트", description="특정 사용자를 뮤트합니다.")
async def mute(
        inter: disnake.ApplicationCommandInteraction,
        멤버: disnake.Member,
        뮤트시간: str,
        사유: str
):
    await inter.response.defer()

    if not any(role.id in ADMIN_ROLE_ID for role in inter.author.roles):
        await inter.followup.send("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
        return

    try:
        duration = parse_duration(뮤트시간)
        if duration is None:
            await inter.followup.send("뮤트 시간 형식이 올바르지 않습니다. 예: 1h30m, 2d, 45m", ephemeral=True)
            return

        end_time = datetime.now() + duration
        await mute_user_with_reason(멤버, inter.guild, 사유, end_time, inter.author)
        await inter.followup.send(f"{멤버.mention}님을 {format_duration(duration)} 동안 뮤트했습니다. 사유: {사유}")

    except Exception as e:
        await inter.followup.send(f"뮤트 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

@bot.slash_command(name="뮤트해제", description="특정 사용자의 뮤트를 해제합니다.")
async def unmute(inter: disnake.ApplicationCommandInteraction, 멤버: disnake.Member):
    await inter.response.defer()

    if not any(role.id in ADMIN_ROLE_ID for role in inter.author.roles):
        await inter.followup.send("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
        return

    await unmute_user(멤버, inter.guild)
    await inter.followup.send(f"{멤버.mention}의 입막음이 풀렸습니다유")


@bot.slash_command(name="뮤트로그", description="특정 사용자의 뮤트 로그를 확인합니다.")
async def mute_logs(inter: disnake.ApplicationCommandInteraction, 멤버: disnake.Member):
    if not any(role.id in ADMIN_ROLE_ID for role in inter.author.roles):
        await inter.response.send_message("이런 심부름은 저의 주인님만 시킬 수 있어유", ephemeral=True)
        return

    logs = await mute_logs_collection.find({'user_id': 멤버.id}).sort('muted_at', -1).to_list(length=None)

    if logs:
        paginator = MuteLogsPaginator(logs, inter.author)
        embed = paginator.create_embed()
        await inter.response.send_message(embed=embed, view=paginator)
    else:
        await inter.response.send_message(f"{멤버.name}의 뮤트 기록이 없습니다유.")


@unmute.error
async def unmute_error(inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
    if isinstance(error, commands.MissingRole):
        await inter.response.send_message("저의 주인님이 아니네유", ephemeral=True)
    else:
        await inter.response.send_message(f"오류가 발생했습니다: {str(error)}", ephemeral=True)


@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error: Exception):
    if isinstance(error, commands.MissingAnyRole):
        message = "이런 심부름은 저의 주인님만 시킬 수 있어유"
    else:
        message = f"오류가 발생했습니다: {str(error)}"

    if not inter.response.is_done():
        await inter.response.send_message(message, ephemeral=True)
    else:
        await inter.followup.send(message, ephemeral=True)


@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error: Exception):
    if isinstance(error, commands.MissingRole):
        message = "이런 심부름은 저의 주인님만 시킬 수 있어유"
    else:
        message = f"오류가 발생했습니다: {str(error)}"

    if not inter.response.is_done():
        await inter.response.send_message(message, ephemeral=True)
    else:
        await inter.followup.send(message, ephemeral=True)


async def mute_user(member: disnake.Member, guild: disnake.Guild, content: str, banned_word: str):
    try:
        mute_role = guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            return

        if mute_role in member.roles:
            return

        # 사용자의 현재 역할 저장
        current_roles = [role.id for role in member.roles if role.id != guild.id and role.id != MUTE_ROLE_ID]
        await user_roles_collection.update_one(
            {'user_id': member.id},
            {'$set': {'roles': current_roles}},
            upsert=True
        )

        # 모든 역할 제거 후 뮤트 역할 추가
        roles_to_remove = [role for role in member.roles if role.id != guild.id and role.id != MUTE_ROLE_ID]
        await member.remove_roles(*roles_to_remove, reason="Mute")
        await member.add_roles(mute_role)

        await mute_logs_collection.insert_one({
            'user_id': member.id,
            'username': member.name,
            'muted_at': datetime.now(),
            'content': content,
            'banned_word': banned_word
        })

        # 2시간(7200초) 후에 자동으로 언뮤트
        await asyncio.sleep(7200)

        # 멤버가 여전히 서버에 있고, 여전히 뮤트 상태인지 확인
        updated_member = guild.get_member(member.id)
        if updated_member and mute_role in updated_member.roles:
            await unmute_user(updated_member, guild)

    except disnake.Forbidden:
        print(f"봇에게 {member}를 뮤트할 권한이 없습니다.")
    except Exception as e:
        print(f"{member} 뮤트 중 오류 발생: {str(e)}")


async def unmute_user(member: disnake.Member, guild: disnake.Guild):
    try:
        mute_role = guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            return

        if mute_role not in member.roles:
            return

        # 뮤트 역할 제거
        await member.remove_roles(mute_role)

        # 저장된 역할 복원
        user_roles = await user_roles_collection.find_one({'user_id': member.id})
        if user_roles:
            roles_to_add = [guild.get_role(role_id) for role_id in user_roles['roles'] if
                            guild.get_role(role_id) is not None]
            await member.add_roles(*roles_to_add)
            await user_roles_collection.delete_one({'user_id': member.id})

    except disnake.Forbidden:
        print(f"봇에게 {member}의 뮤트를 해제할 권한이 없습니다.")
    except Exception as e:
        print(f"{member} 뮤트 해제 중 오류 발생: {str(e)}", exc_info=True)


async def schedule_unmute(member: disnake.Member, guild: disnake.Guild, end_time: datetime):
    await asyncio.sleep((end_time - datetime.now()).total_seconds())
    await unmute_user(member, guild)


def parse_duration(duration_str: str) -> timedelta:
    total_seconds = 0
    current_number = ""
    for char in duration_str:
        if char.isdigit():
            current_number += char
        elif char in ['d', 'h', 'm']:
            if not current_number:
                return None
            value = int(current_number)
            if char == 'd':
                total_seconds += value * 86400
            elif char == 'h':
                total_seconds += value * 3600
            elif char == 'm':
                total_seconds += value * 60
            current_number = ""
        else:
            return None
    return timedelta(seconds=total_seconds) if total_seconds > 0 else None


def format_duration(duration: timedelta) -> str:
    days, remainder = divmod(duration.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{int(days)}일")
    if hours > 0:
        parts.append(f"{int(hours)}시간")
    if minutes > 0:
        parts.append(f"{int(minutes)}분")

    return " ".join(parts) if parts else "1분 미만"


async def mute_user_with_reason(member: disnake.Member, guild: disnake.Guild, reason: str, end_time: datetime,
                                muted_by: disnake.Member):
    try:
        mute_role = guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            print("뮤트 역할을 찾을 수 없습니다.")
            return

        if mute_role in member.roles:
            print(f"{member}는 이미 뮤트 상태입니다.")
            return

        # 사용자의 현재 역할 저장
        current_roles = [role.id for role in member.roles if role.id != guild.id and role.id != MUTE_ROLE_ID]
        await user_roles_collection.update_one(
            {'user_id': member.id},
            {'$set': {'roles': current_roles}},
            upsert=True
        )

        # 모든 역할 제거 후 뮤트 역할 추가
        roles_to_remove = [role for role in member.roles if role.id != guild.id and role.id != MUTE_ROLE_ID]
        await member.remove_roles(*roles_to_remove, reason="Mute")
        await member.add_roles(mute_role)

        # 뮤트 로그 저장
        await mute_logs_collection.insert_one({
            'user_id': member.id,
            'username': member.name,
            'muted_at': datetime.now(),
            'end_time': end_time,
            'reason': reason,
            'muted_by': {
                'id': muted_by.id,
                'name': muted_by.name
            },
            'duration': (end_time - datetime.now()).total_seconds()
        })

        # 뮤트 해제를 위한 태스크 생성
        bot.loop.create_task(schedule_unmute(member, guild, end_time))

    except disnake.Forbidden:
        print(f"봇에게 {member}를 뮤트할 권한이 없습니다.")
    except Exception as e:
        print(f"{member} 뮤트 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
