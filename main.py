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
import os


load_dotenv()

roblox_client = Client(os.getenv("ROBLOXTOKEN"))
BOT_TOKEN = os.getenv("BOTTOKEN")


bot = commands.Bot(command_prefix=None)
intents = disnake.Intents.default()

joseon_group_id = "4654286"

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
            title = "그룹 관리 명령어 리스트",
            color = disnake.Color.dark_blue()
        )

        # 임베드 필드
        embed.add_field(name="멤버관리", value="다수 혹은 한명의 그룹 랭크를 관리하는 명령어 입니다.", inline=False)

        await inter.response.send_message(embed=embed)

    except Exception as e:
        await inter.response.send_message(f"에러가 발생했습니다. {e}")


@bot.slash_command(name="멤버관리", description="다수 혹은 한명의 그룹 랭크를 관리하는 명령어")
@commands.has_any_role("『兵曹』 병조")
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

        group = await roblox_client.get_group(joseon_group_id)

        results = []
        for username, rank in zip(usernames, rank_numbers):
            try:
                user = await roblox_client.get_user_by_username(username)
            except:
                results.append(f"{username}은(는) 유효하지 않은 사용자명입니다.")
                continue

            try:
                group_member = await group.get_member(user.id)
            except:
                results.append(f"{username}님은 그룹에 속해 있지 않습니다.")
                continue

            if rank in RANK_ROLES:
                role = RANK_ROLES[rank]
                await group.set_rank(user, rank)
                results.append(f"{username}님의 랭크를 {rank}({role})로 변경했습니다.")
            else:
                results.append(f"{username}님에 대해 없는 랭크({rank})가 지정되었습니다.")

        await inter.followup.send(f"{inter.user.mention}\n" + "\n".join(results))
    except Exception as e:
        await inter.followup.send(f"{inter.user.mention} 에러가 발생했습니다: {e}")

@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error: Exception):
    if isinstance(error, commands.MissingAnyRole):
        await inter.response.send_message("이 명령어를 사용하려면 권한이 필요합니다.", ephemeral=True)
    else:
        await inter.response.send_message(f"오류가 발생했습니다: {str(error)}", ephemeral=True)



bot.run(BOT_TOKEN)
