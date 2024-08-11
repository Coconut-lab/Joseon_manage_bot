"""
구현할 기능
로블록스 자동 그룹 관리 기능 - 완성
금지어 - 완성
특정 채널에 올라오는 메세지를 Airtable에 기록하는 기능
게임 오류 제보 기능
"""
from datetime import datetime
import disnake
from disnake.ext import commands
from roblox import Client
from dotenv import load_dotenv
import asyncio
import json
import os


load_dotenv()

roblox_client = Client(os.getenv("ROBLOXTOKEN"))
BOT_TOKEN = os.getenv("BOTTOKEN")


intents = disnake.Intents.all()
bot = commands.InteractionBot(intents=intents)

TARGET_GUILD_ID = 612989092443062278
BANNED_WORDS_FILE = "badwords.json"

joseon_group_id = "4654286"
MTA_group_id = "4654485"
RGO_group_id = "4654514"
hanyang_group_id = "4766967"

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

def load_banned_words():
    try:
        with open(BANNED_WORDS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return {
                "words": data.get("words", {}),
                "restricted_users": data.get("restricted_users", []),
            }
    except FileNotFoundError:
        return {"words": {}, "restricted_users": []}

def save_banned_words(words):
    with open(BANNED_WORDS_FILE, "w", encoding="utf-8") as file:
        json.dump(words, file, ensure_ascii=False, indent=4)

banned_words_data = load_banned_words()

@bot.event
async def on_ready():
    print("Bot is ready!")

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

        if message.author.id in banned_words_data["restricted_users"]:
            for word in banned_words_data["words"]:
                if word in content.split():
                    await message.channel.send(f"{message.author.mention}님, 부적절한 단어 사용으로 뮤트되었습니다.")
                    await message.delete()
                    await mute_user(message.author, message.guild)
                    return

    except Exception as e:
        await message.channel.send(f"메시지 처리 중 오류 발생: {str(e)}")

@bot.slash_command()
async def test(inter):
    await inter.response.send_message("Hello World!")

@bot.slash_command(name="명령어", description="그룹 관리 명령어 리스트")
async def list(inter):
    try:
        # 임베드 헤더
        embed = disnake.Embed(
            title = "명령어 리스트",
            color = disnake.Color.dark_blue()
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
        embed.add_field(name="호적승인", value="천민에서 상민으로 그룹 랭크 조정 **호조 권한**", inline=False)


        await inter.response.send_message(embed=embed)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")

@bot.slash_command(name="설명서", description="기본적인 그룹 관리 명령어 설명서")
async def manual(inter):
    try:
        # 임베드 헤더
        embed = disnake.Embed(
            title = "설명서",
            description="기본적인 그룹 관리 명령어를 알려드립니다.",
            color = disnake.Color.yellow(),
        )

        # 임베드 필드
        embed.add_field(name="조선(도감,어영)군관리 명령어", value="/조선(도감,어영)군관리 이름 랭크번호 / 이름2 랭크번호 ...", inline=False)
        embed.add_field(name="조선(도감,어영)군랭크 명령어", value="각 그룹의 랭크 번호를 알려주는 명령어 입니다. 먼저 확인 후에 관리 명령어를 사용하세요.", inline=False)
        embed.add_field(name="호적신고 명령어", value="호조만 사용할 수 있는 명령어로 로블록스 이름을 입력하면 해당 사람을 천민에서 상민으로 조정합니다.", inline=False)

        # 임베드 풋터
        embed.set_footer(
            text="더 자세한 문의는 병조참판 차지철에게 DM",
        )

        await inter.response.send_message(embed=embed)


    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")

@bot.slash_command(name="조선군랭크", description="조선군 그룹 랭크 번호 리스트")
@commands.has_any_role(597769848256200717, 1270777112982323274, 1270777180921528391)
async def list(inter):
    try:
        # 임베드 헤더
        embed = disnake.Embed(
            title = "랭크 번호 리스트",
            color = disnake.Color.dark_gray()
        )

        for num, rank in sorted(RANK_ROLES.items(), reverse=True):
            embed.add_field(name = num, value = rank, inline=True)


        await inter.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")

@bot.slash_command(name="도감군랭크", description="도감군 그룹 랭크 번호 리스트")
@commands.has_any_role(597769848256200717, 1270777112982323274)
async def list(inter):
    try:
        # 임베드 헤더
        embed = disnake.Embed(
            title = "랭크 번호 리스트",
            color = disnake.Color.dark_gray()
        )

        for num, rank in sorted(MTA_ROLES.items(), reverse=True):
            embed.add_field(name = num, value = rank, inline=True)


        await inter.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")

@bot.slash_command(name="어영군랭크", description="어영군 그룹 랭크 번호 리스트")
@commands.has_any_role(597769848256200717, 1270777180921528391)
async def list(inter):
    try:
        # 임베드 헤더
        embed = disnake.Embed(
            title = "랭크 번호 리스트",
            color = disnake.Color.dark_gray()
        )

        for num, rank in sorted(RGO_ROLES.items(), reverse=True):
            embed.add_field(name = num, value = rank, inline=True)


        await inter.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")

@bot.slash_command(name="조선군관리", description="다수 혹은 한명의 조선군 랭크를 관리하는 명령어")
@commands.has_any_role(597769848256200717, 1270777112982323274, 1270777180921528391)
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
                    results.append(f"{username}은(는) 유효하지 않은 사용자명입니다.")
                    continue

                group = await roblox_client.get_group(joseon_group_id)
                group_member = group.get_member(user.id)

                if group_member is None:
                    results.append(f"{username}님은 그룹에 속해 있지 않습니다.")
                    continue

                if rank in RANK_ROLES:
                    role = RANK_ROLES[rank]
                    try:
                        await group.set_rank(user.id, rank)
                        results.append(f"{username}님의 랭크를 {role}({rank})로 변경했습니다.")
                    except Exception as e:
                        error_message = str(e)
                        if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                            results.append(f"{username}님은 이미 {role}({rank}) 랭크입니다.")
                        else:
                            raise  # 다른 종류의 오류라면 상위 예외 처리로 전달
                else:
                    results.append(f"{username}님에 대해 없는 랭크({rank})가 지정되었습니다.")

            except Exception as e:
                results.append(f"{username}님 처리 중 오류 발생: {str(e)}")

            await asyncio.sleep(0.5)  # API 요청 사이에 짧은 대기 시간 추가

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))
    except Exception as e:
        await inter.followup.send(f"{inter.user.mention} 전체 처리 중 에러가 발생했습니다: {e}")

@bot.slash_command(name="도감군관리", description="다수 혹은 한명의 도감군 랭크를 관리하는 명령어")
@commands.has_any_role(597769848256200717, 1270777112982323274)
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
                    results.append(f"{username}은(는) 유효하지 않은 사용자명입니다.")
                    continue

                group = await roblox_client.get_group(MTA_group_id)
                group_member = group.get_member(user.id)

                if group_member is None:
                    results.append(f"{username}님은 그룹에 속해 있지 않습니다.")
                    continue

                if rank in MTA_ROLES:
                    role = MTA_ROLES[rank]
                    try:
                        await group.set_rank(user.id, rank)
                        results.append(f"{username}님의 랭크를 {role}({rank})로 변경했습니다.")
                    except Exception as e:
                        error_message = str(e)
                        if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                            results.append(f"{username}님은 이미 {role}({rank}) 랭크입니다.")
                        else:
                            raise  # 다른 종류의 오류라면 상위 예외 처리로 전달
                else:
                    results.append(f"{username}님에 대해 없는 랭크({rank})가 지정되었습니다.")

            except Exception as e:
                results.append(f"{username}님 처리 중 오류 발생: {str(e)}")

            await asyncio.sleep(0.5)  # API 요청 사이에 짧은 대기 시간 추가

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))
    except Exception as e:
        await inter.followup.send(f"{inter.user.mention} 전체 처리 중 에러가 발생했습니다: {e}")

@bot.slash_command(name="어영군관리", description="다수 혹은 한명의 어영군 랭크를 관리하는 명령어")
@commands.has_any_role(597769848256200717, 1270777180921528391)
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
                    results.append(f"{username}은(는) 유효하지 않은 사용자명입니다.")
                    continue

                group = await roblox_client.get_group(RGO_group_id)
                group_member = group.get_member(user.id)

                if group_member is None:
                    results.append(f"{username}님은 그룹에 속해 있지 않습니다.")
                    continue

                if rank in RGO_ROLES:
                    role = RGO_ROLES[rank]
                    try:
                        await group.set_rank(user.id, rank)
                        results.append(f"{username}님의 랭크를 {role}({rank})로 변경했습니다.")
                    except Exception as e:
                        error_message = str(e)
                        if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                            results.append(f"{username}님은 이미 {role}({rank}) 랭크입니다.")
                        else:
                            raise  # 다른 종류의 오류라면 상위 예외 처리로 전달
                else:
                    results.append(f"{username}님에 대해 없는 랭크({rank})가 지정되었습니다.")

            except Exception as e:
                results.append(f"{username}님 처리 중 오류 발생: {str(e)}")

            await asyncio.sleep(0.5)  # API 요청 사이에 짧은 대기 시간 추가

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))
    except Exception as e:
        await inter.followup.send(f"{inter.user.mention} 전체 처리 중 에러가 발생했습니다: {e}")

@bot.slash_command(name="호적승인", description="천민에서 상민으로 그룹 랭크 조정")
@commands.has_role(695978137196036163)
async def rank(inter: disnake.ApplicationCommandInteraction, 이름: str):
    await inter.response.defer()
    text = 이름
    try:
        results = []
        user = await roblox_client.get_user_by_username(text)

        if user is None:
            results.append(f"{text}은(는) 유효하지 않은 사용자명입니다.")
            await inter.followup.send("\n".join(results))
            return

        group = await roblox_client.get_group(hanyang_group_id)
        group_member = group.get_member(user.id)

        if group_member is None:
            results.append(f"{text}님은 그룹에 속해 있지 않습니다.")
            await inter.followup.send("\n".join(results))
            return


        try:
            await group.set_rank(user.id, 20)
            results.append(f"{text}님의 랭크를 상민으로 변경했습니다.")
        except Exception as e:
            error_message = str(e)
            if "400 Bad Request" in error_message and "You cannot change the user's role to the same role" in error_message:
                results.append(f"{text}님은 이미 상민입니다.")
            elif "401 Unauthorized" in error_message:
                results.append(f"{text}님은 이미 상민 이상의 랭크를 가지고 있어 변경할 수 없습니다.")
            else:
                raise  # 다른 종류의 오류라면 상위 예외 처리로 전달

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))

    except Exception as e:
        await inter.followup.send(f"오류가 발생했습니다: {str(e)}")

@bot.slash_command(name="금지어추가", description="금지어를 추가합니다.")
@commands.has_role(789359681776648202)
async def add_banned_word(inter: disnake.ApplicationCommandInteraction, 단어: str):
    word = 단어
    banned_words_data["words"][word] = {
        "added_by": str(inter.author),
        "added_at": datetime.now().isoformat()
    }
    save_banned_words(banned_words_data)
    await inter.response.send_message(f"금지어 '{word}'가 추가되었습니다.")

@bot.slash_command(name="금지어제거", description="금지어를 제거합니다.")
@commands.has_role(789359681776648202)
async def remove_banned_word(inter: disnake.ApplicationCommandInteraction, 단어: str):
    word = 단어
    if word in banned_words_data["words"]:
        del banned_words_data["words"][word]
        save_banned_words(banned_words_data)
        await inter.response.send_message(f"금지어 '{word}'가 제거되었습니다.")
    else:
        await inter.response.send_message(f"'{word}'는 금지어 목록에 없습니다.")

@bot.slash_command(name="금지어목록", description="현재 금지어를 확인합니다.")
@commands.has_role(789359681776648202)
async def list_banned_words(inter: disnake.ApplicationCommandInteraction):
    if banned_words_data["words"]:
        message = "현재 금지어 목록:\n"
        for word, info in banned_words_data["words"].items():
            added_by = info.get("added_by", "Unknown")
            added_at = info.get("added_at", "Unknown")
            message += f"- {word} (추가자: {added_by}, 추가일: {added_at})\n"
        await inter.response.send_message(message)
    else:
        await inter.response.send_message("현재 금지어 목록이 비어 있습니다.")

@bot.slash_command(name="제한사용자추가", description="금지어 규칙이 적용될 사용자를 추가합니다.")
@commands.has_role(789359681776648202)
async def add_restricted_user(inter: disnake.ApplicationCommandInteraction, 사용자: disnake.User):
    user_id = 사용자.id
    if user_id not in banned_words_data["restricted_users"]:
        banned_words_data["restricted_users"].append(user_id)
        save_banned_words(banned_words_data)
        await inter.response.send_message(f"사용자 {사용자.mention}가 제한 목록에 추가되었습니다.")
    else:
        await inter.response.send_message(f"사용자 {사용자.mention}는 이미 제한 목록에 있습니다.")

@bot.slash_command(name="제한사용자제거", description="금지어 규칙이 적용되는 사용자를 제거합니다.")
@commands.has_role(789359681776648202)
async def remove_restricted_user(inter: disnake.ApplicationCommandInteraction, 사용자: disnake.User):
    user_id = 사용자.id
    if user_id in banned_words_data["restricted_users"]:
        banned_words_data["restricted_users"].remove(user_id)
        save_banned_words(banned_words_data)
        await inter.response.send_message(f"사용자 {사용자.mention}가 제한 목록에서 제거되었습니다.")
    else:
        await inter.response.send_message(f"사용자 {사용자.mention}는 제한 목록에 없습니다.")

@bot.slash_command(name="제한사용자목록", description="금지어 규칙이 적용되는 사용자 목록을 확인합니다.")
@commands.has_role(789359681776648202)
async def list_restricted_users(inter: disnake.ApplicationCommandInteraction):
    if banned_words_data["restricted_users"]:
        users = [await bot.fetch_user(user_id) for user_id in banned_words_data["restricted_users"]]
        user_list = "\n".join([f"- {user.name}#{user.discriminator} (ID: {user.id})" for user in users])
        await inter.response.send_message(f"현재 제한된 사용자 목록:\n{user_list}")
    else:
        await inter.response.send_message("현재 제한된 사용자가 없습니다.")

@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error: Exception):
    if isinstance(error, commands.MissingAnyRole):
        await inter.response.send_message("이 명령어를 사용하려면 권한이 필요합니다.", ephemeral=True)
    else:
        await inter.response.send_message(f"오류가 발생했습니다: {str(error)}", ephemeral=True)


async def mute_user(member: disnake.Member, guild: disnake.Guild):
    mute_role = guild.get_role(795147706237714433)

    if not mute_role:
        return

    if mute_role not in member.roles:
        await member.add_roles(mute_role)

        # 30분(1800초) 후에 자동으로 언뮤트
        await asyncio.sleep(1800)

        # 멤버가 여전히 서버에 있고, 여전히 뮤트 상태인지 확인
        updated_member = guild.get_member(member.id)
        if updated_member and mute_role in updated_member.roles:
            await updated_member.remove_roles(mute_role)
    else:
        print(f"{member.name} is already muted.")

bot.run(BOT_TOKEN)
