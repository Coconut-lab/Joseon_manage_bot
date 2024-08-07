"""
구현할 기능
로블록스 자동 그룹 관리 기능 - 완성
특정 채널에 올라오는 메세지를 Airtable에 기록하는 기능
게임 오류 제보 기능
"""

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


bot = commands.Bot(command_prefix=None)
intents = disnake.Intents.default()

joseon_group_id = "4654286"
MTA_group_id = "4654485"
RGO_group_id = "4654514"

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



@bot.event
async def on_ready():
    print("Bot is ready!")

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
        embed.add_field(name="조선군관리", value="다수 혹은 한명의 조선군 랭크를 관리하는 명령어 입니다.", inline=False)
        embed.add_field(name="도감군관리", value="다수 혹은 한명의 도감군 랭크를 관리하는 명령어 입니다.", inline=False)
        embed.add_field(name="어영군관리", value="다수 혹은 한명의 어영군 랭크를 관리하는 명령어 입니다.", inline=False)
        embed.add_field(name="조선군랭크", value="조선군 그룹 랭크 번호 리스트 입니다.", inline=False)
        embed.add_field(name="도감군랭크", value="도감군 그룹 랭크 번호 리스트 입니다.", inline=False)
        embed.add_field(name="어영군랭크", value="어영군 그룹 랭크 번호 리스트 입니다.", inline=False)

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
async def ranks(inter: disnake.ApplicationCommandInteraction, *, text: str):
    await inter.response.defer()
    try:
        lines = text.split("/")
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
async def ranks(inter: disnake.ApplicationCommandInteraction, *, text: str):
    await inter.response.defer()
    try:
        lines = text.split("/")
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
async def ranks(inter: disnake.ApplicationCommandInteraction, *, text: str):
    await inter.response.defer()
    try:
        lines = text.split("/")
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
async def rank(inter: disnake.ApplicationCommandInteraction, text: str):
    await inter.response.defer()
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

@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error: Exception):
    if isinstance(error, commands.MissingAnyRole):
        await inter.response.send_message("이 명령어를 사용하려면 권한이 필요합니다.", ephemeral=True)
    else:
        await inter.response.send_message(f"오류가 발생했습니다: {str(error)}", ephemeral=True)


bot.run(BOT_TOKEN)
