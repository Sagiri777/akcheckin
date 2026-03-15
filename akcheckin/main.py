import argparse
import json
from pathlib import Path
from typing import Any

import requests

from akcheckin.utils import (
    decrypt_battle_replay,
    encrypt_battle_data,
    encrypt_is_cheat,
    get_battle_data_access,
    get_md5,
    get_random_devices,
    merge_dict,
    now,
    select_tags,
    sleep,
    u8_sign,
)

ROOT = Path(__file__).resolve().parent.parent


class Player:
    def __init__(self, phone: str, server: str = "cn") -> None:
        self.uid = ""
        self.seqnum = 0
        self.secret = ""
        self.server = server
        self.data: dict[str, Any] = {}
        config = json.loads((ROOT / "config.json").read_text())
        self.config = config.get(get_md5(phone), {})

    def print_status(self) -> None:
        status = self.data.get("status", {})
        print(f"{status.get('nickName')}#{status.get('nickNumber')}")
        print(f"uid：{status.get('uid')}")
        print(f"等级：{status.get('level')}({status.get('exp')})/120")
        print(f"理智：{status.get('ap')}/{status.get('maxAp')}")
        print(f"源石：{status.get('androidDiamond')}")
        print(f"赤金：{status.get('gold')}")
        print(f"信用点：{status.get('socialPoint')}")

    def init(self, phone: str, pwd: str) -> None:
        res_version = get_res_version()
        print(
            f"assetsVersion:{res_version['resVersion']}, "
            f"clientVersion:{res_version['clientVersion']}"
        )
        devices = get_random_devices()
        token_data = get_token(devices, phone, pwd)
        self.uid = token_data["uid"]
        print(f"uid:{self.uid}, access_token:{token_data['token']}")
        login_data = self.post(
            "/account/login",
            {
                "networkVersion": "5",
                "uid": self.uid,
                "token": token_data["token"],
                "assetsVersion": res_version["resVersion"],
                "clientVersion": res_version["clientVersion"],
                "platform": 1,
                **devices,
            },
        )
        self.secret = login_data.get("secret", "")
        self.sync_data()

    def auto_checkin(self) -> None:
        if self.data.get("checkIn", {}).get("canCheckIn"):
            self.post("/user/checkIn", {})
            print("[活动]已完成签到")

        activity = self.data.get("activity", {})
        for activity_id, value in activity.get("LOGIN_ONLY", {}).items():
            if value.get("reward"):
                self.post("/activity/loginOnly/getReward", {"activityId": activity_id})

        for activity_id, value in activity.get("CHECKIN_ACCESS", {}).items():
            if value.get("currentStatus"):
                self.post(
                    "/activity/actCheckinAccess/getCheckInReward", {"activityId": activity_id}
                )

        for activity_id, value in activity.get("GRID_GACHA_V2", {}).items():
            if not value.get("today", {}).get("done"):
                self.post("/activity/gridGachaV2/doTodayGacha", {"activityId": activity_id})

    def auto_mail(self) -> None:
        res = self.post("/mail/getMetaInfoList", {"from": now()})
        mail_meta_list = [m for m in res.get("result", []) if (m.get("state") or m.get("hasItem"))]
        mail_id_list = [m.get("mailId") for m in mail_meta_list if not m.get("type")]
        sys_mail_id_list = [m.get("mailId") for m in mail_meta_list if m.get("type")]
        if mail_id_list or sys_mail_id_list:
            self.post(
                "/mail/receiveAllMail",
                {"mailIdList": mail_id_list, "sysMailIdList": sys_mail_id_list},
            )

    def auto_social(self) -> None:
        meeting = self.data["building"]["rooms"]["MEETING"]["slot_36"]
        if meeting.get("dailyReward"):
            self.post("/building/getDailyClue", {})
        if meeting.get("socialReward", {}).get("daily"):
            self.post("/building/getMeetingroomReward", {"type": [0]})
        if meeting.get("socialReward", {}).get("search"):
            self.post("/building/getMeetingroomReward", {"type": [1]})

        id_list = self.post("/building/getClueFriendList", {}).get("result", [])
        for idx, friend in enumerate(id_list[:10]):
            if idx < 10:
                self.post("/building/visitBuilding", {"friendId": friend["uid"]})

        board = meeting.get("board", {})
        for stock in meeting.get("ownStock", []):
            if stock["type"] not in board:
                self.post("/building/putClueToTheBoard", {"clueId": stock["id"]})

        if len(board) == 7:
            self.post("/building/startInfoShare", {})

        if self.data.get("social", {}).get("yesterdayReward", {}).get("canReceive"):
            self.post("/social/receiveSocialPoint", {})

    def auto_confirm_missions(self) -> None:
        self.post("/mission/autoConfirmMissions", {"type": "DAILY"})
        self.post("/mission/autoConfirmMissions", {"type": "WEEKLY"})

    def auto_recruit(self) -> None:
        slots = self.data.get("recruit", {}).get("normal", {}).get("slots", {})
        for slot_id, slot in slots.items():
            if self.data["status"]["recruitLicense"] == 0:
                break
            if not slot.get("state") or slot.get("maxFinishTs", 0) > now():
                continue
            if slot.get("state") == 2:
                self.post("/gacha/finishNormalGacha", {"slotId": slot_id})

            tag_list, special_tag_id, duration = select_tags(slot.get("tags", []))
            can_refresh = self.data["building"]["rooms"]["HIRE"]["slot_23"].get("refreshCount")
            if not tag_list and can_refresh and 11 not in slot.get("tags", []):
                self.post("/gacha/refreshTags", {"slotId": slot_id})
                updated_slot = self.data["recruit"]["normal"]["slots"][slot_id]
                tag_list, special_tag_id, duration = select_tags(updated_slot.get("tags", []))

            if special_tag_id != 11:
                self.post(
                    "/gacha/normalGacha",
                    {
                        "slotId": slot_id,
                        "tagList": tag_list,
                        "specialTagId": special_tag_id,
                        "duration": duration,
                    },
                )

    def auto_replay(self, stage_id: str, ap_cost: int, times: int) -> None:
        rounds = min(times, 6)
        if rounds <= 1 or self.data["status"]["ap"] < ap_cost * rounds:
            return

        replay = self.post("/quest/getBattleReplay", {"stageId": stage_id}).get("battleReplay")
        if not replay:
            return
        battle_log = decrypt_battle_replay(replay)
        squad = []
        for idx in range(12):
            if idx >= len(battle_log["journal"]["squad"]):
                squad.append(None)
                continue
            member = battle_log["journal"]["squad"][idx]
            squad.append(
                {
                    "charInstId": member["charInstId"],
                    "skillIndex": member["skillIndex"],
                    "currentEquip": member.get("uniequipId") or None,
                }
            )

        battle_id = self.post(
            "/quest/battleStart",
            {
                "isRetro": 0,
                "pry": 0,
                "battleType": 2,
                "multiple": {"battleTimes": rounds},
                "usePracticeTicket": 0,
                "stageId": stage_id,
                "squad": {"squadId": "0", "name": None, "slots": squad},
                "assistFriend": None,
                "isReplay": 1,
                "startTs": now(),
            },
        ).get("battleId")
        if not battle_id:
            return

        battle_stats = self.config["battleLog"][stage_id]
        battle_stats["stats"]["access"] = get_battle_data_access(self.data["pushFlags"]["status"])
        battle_stats["isCheat"] = encrypt_is_cheat(battle_id)
        battle_stats["stats"]["beginTs"] = now()
        battle_stats["stats"]["endTs"] = now() + battle_stats["completeTime"]

        battle_data = {
            "battleId": battle_id,
            "interrupt": 0,
            "giveUp": 0,
            "percent": 100,
            "completeState": 3,
            "killCnt": battle_stats["stats"]["killedEnemiesCnt"],
            "validKillCnt": battle_stats["stats"]["killedEnemiesCnt"],
            "battleData": battle_stats,
            "currentIndex": 0,
            "platform": 1,
        }
        sleep(battle_stats["completeTime"])
        self.post(
            "/quest/battleFinish",
            {
                "data": encrypt_battle_data(battle_data, self.data["pushFlags"]["status"]),
                "battleData": {
                    "stats": {},
                    "isCheat": encrypt_is_cheat(battle_id),
                    "completeTime": battle_stats["completeTime"],
                },
            },
        )

    def auto_building(self) -> None:
        self.post("/building/gainAllIntimacy", {})
        self.post(
            "/building/settleManufacture",
            {
                "roomSlotIdList": list(self.data["building"]["rooms"]["MANUFACTURE"].keys()),
                "supplement": 1,
            },
        )
        self.post(
            "/building/deliveryBatchOrder",
            {"slotList": list(self.data["building"]["rooms"]["TRADING"].keys())},
        )
        if self.config.get("enableBatchBuilding"):
            self.post("/building/batchChangeWorkChar", {})
            self.post("/building/batchRestChar", {})

    def auto_gacha(self) -> None:
        for pool_id, value in self.data.get("gacha", {}).get("limit", {}).items():
            if value.get("leastFree"):
                self.post("/gacha/advancedGacha", {"poolId": pool_id, "useTkt": 3, "itemId": None})

    def auto_buy(self) -> None:
        goods = self.post("/shop/getSocialGoodList", {}).get("goodList", [])
        goods = sorted(goods, key=lambda item: item["price"])
        purchased = {item["id"] for item in self.data["shop"]["SOCIAL"]["info"]}
        for good in goods:
            if good["goodId"] in purchased:
                continue
            if good["price"] <= self.data["status"]["socialPoint"] and good["availCount"]:
                self.post("/shop/buySocialGood", {"goodId": good["goodId"], "count": 1})
            else:
                break

    def auto_campaign(self) -> None:
        if self.data["status"]["ap"] < 25:
            return
        stage_id = self.data["campaignsV2"]["open"]["rotate"]
        if self.data["campaignsV2"]["sweepMaxKills"][stage_id] != 400:
            return
        if (
            self.data["campaignsV2"]["campaignCurrentFee"]
            >= self.data["campaignsV2"]["campaignTotalFee"]
        ):
            return
        agents = self.data["consumable"].get("EXTERMINATION_AGENT", {})
        entry = next(((k, v) for k, v in agents.items() if v.get("count", 0) > 0), None)
        if not entry:
            return
        self.post(
            "/campaignV2/battleSweep",
            {"stageId": stage_id, "itemId": "EXTERMINATION_AGENT", "instId": entry[0]},
        )

    def sync_data(self) -> None:
        self.post("/account/syncData", {"platform": 1})
        status = self.data["status"]
        status["ap"] += (now() - status["lastApAddTime"]) // 360
        status["ap"] = min(status["ap"], status["maxAp"])

    def merge(self, delta: dict[str, Any]) -> None:
        merge_dict(self.data, delta.get("modified", {}), "modify")

    def post(self, cgi: str, data: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "uid": self.uid,
            "secret": self.secret,
            "seqnum": str(self.seqnum),
            "Content-Type": "application/json",
            "X-Unity-Version": "2017.4.39f1",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0.1; X Build/V417IR)",
            "Connection": "Keep-Alive",
        }
        url = f"https://ak-gs-gf.hypergryph.com{cgi}"
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        body = response.json()

        seq_header = response.headers.get("seqnum")
        self.seqnum = int(seq_header) if seq_header and seq_header.isdigit() else self.seqnum + 1

        if "user" in body:
            self.data = body["user"]
        if "playerDataDelta" in body:
            self.merge(body["playerDataDelta"])
        return body


def get_res_version() -> dict[str, Any]:
    response = requests.get(
        "https://ak-conf.hypergryph.com/config/prod/official/Android/version", timeout=30
    )
    response.raise_for_status()
    return response.json()


def get_token(devices: dict[str, str], phone: str, pwd: str) -> dict[str, Any]:
    res1 = requests.post(
        "https://as.hypergryph.com/user/auth/v1/token_by_phone_password",
        json={"phone": phone, "password": pwd},
        timeout=30,
    )
    res1.raise_for_status()
    token1 = res1.json()["data"]["token"]

    res2 = requests.post(
        "https://as.hypergryph.com/user/oauth2/v2/grant",
        json={"token": token1, "appCode": "7318def77669979d", "type": 1},
        timeout=30,
    )
    res2.raise_for_status()
    token2 = res2.json()["data"]["token"]

    payload = {
        "appId": "1",
        "channelId": "1",
        "extension": json.dumps({"code": token2, "isSuc": True, "type": 2}),
        "worldId": "1",
        "platform": 1,
        "subChannel": "1",
        **devices,
    }
    payload["sign"] = u8_sign(payload)

    res3 = requests.post("https://as.hypergryph.com/u8/user/v1/getToken", json=payload, timeout=30)
    res3.raise_for_status()
    return res3.json().get("data", {})


def main() -> None:
    parser = argparse.ArgumentParser(description="akcheckin Python version")
    parser.add_argument("phone")
    parser.add_argument("password")
    args = parser.parse_args()

    player = Player(phone=args.phone)
    player.init(args.phone, args.password)
    player.auto_checkin()
    player.auto_mail()
    player.auto_gacha()
    player.auto_building()
    player.auto_social()
    player.auto_buy()
    if player.config.get("enableRecruit"):
        player.auto_recruit()
    player.auto_campaign()
    while player.config.get("enableBattle") and player.data.get("status", {}).get("ap", 0) >= 12:
        times = player.data["status"]["ap"] // 6
        player.auto_replay(player.config["battleStage"], 6, times)
    player.auto_confirm_missions()
    player.print_status()
    print("[main] 已完成")


if __name__ == "__main__":
    main()
