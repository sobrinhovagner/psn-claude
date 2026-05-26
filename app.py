from flask import Flask, jsonify, render_template
from psnawp_api import PSNAWP
from dotenv import load_dotenv
import os
import time

load_dotenv()

app = Flask(__name__)

psnawp = PSNAWP(os.getenv("NPSSO"))
client = psnawp.me()

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r

# Rota principal para carregar o HTML
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/profile")
def profile():
    try:
        p = client.get_profile_legacy()["profile"]
        avatar = ""
        if p.get("personalDetail") and p["personalDetail"].get("profilePictureUrls"):
            avatar = p["personalDetail"]["profilePictureUrls"][0]["profilePictureUrl"]
        elif p.get("avatarUrls"):
            avatar = p["avatarUrls"][-1]["avatarUrl"]
        return jsonify({
            "onlineId": client.online_id,
            "accountId": str(client.account_id),
            "isPlus": p.get("plus", 0) == 1,
            "avatarUrl": avatar,
            "aboutMe": p.get("aboutMe", ""),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/trophies")
def trophies():
    summary = client.trophy_summary()
    t = summary.earned_trophies
    return jsonify({
        "platinum": t.platinum,
        "gold": t.gold,
        "silver": t.silver,
        "bronze": t.bronze,
        "total": t.platinum + t.gold + t.silver + t.bronze,
        "level": summary.trophy_level,
        "progress": summary.progress,
        "tier": summary.tier,
    })

@app.route("/trophy-titles")
def trophy_titles():
    titles = []
    for t in client.trophy_titles(limit=50):
        titles.append({
            "name": t.title_name,
            "np_communication_id": t.np_communication_id,
            "earned_platinum": t.earned_trophies.platinum,
            "earned_gold": t.earned_trophies.gold,
            "earned_silver": t.earned_trophies.silver,
            "earned_bronze": t.earned_trophies.bronze,
            "defined_platinum": t.defined_trophies.platinum,
            "defined_gold": t.defined_trophies.gold,
            "defined_silver": t.defined_trophies.silver,
            "defined_bronze": t.defined_trophies.bronze,
            "last_updated": str(t.last_updated_date_time) if t.last_updated_date_time else None,
            "iconUrl": t.title_icon_url,
        })
    return jsonify(titles)

@app.route("/trophy-titles-all")
def trophy_titles_all():
    titles = []
    for t in client.trophy_titles():
        titles.append({
            "name": t.title_name,
            "np_communication_id": t.np_communication_id,
            "earned_platinum": t.earned_trophies.platinum,
            "earned_gold": t.earned_trophies.gold,
            "earned_silver": t.earned_trophies.silver,
            "earned_bronze": t.earned_trophies.bronze,
            "last_updated": str(t.last_updated_date_time) if t.last_updated_date_time else None,
            "iconUrl": t.title_icon_url,
        })
    return jsonify(titles)

@app.route("/game-trophies/<np_communication_id>")
def game_trophies(np_communication_id):
    try:
        title = psnawp.game_title(
            np_communication_id=np_communication_id,
            account_id=str(client.account_id),
            platform=None
        )
        trophies = []
        for t in title.trophies(platform=None, trophy_group_id="all"):
            trophies.append({
                "id": t.trophy_id,
                "name": t.trophy_name,
                "detail": t.trophy_detail,
                "type": t.trophy_type.value if t.trophy_type else "bronze",
                "iconUrl": t.trophy_icon_url,
                "hidden": t.trophy_hidden,
            })
        earned = []
        for t in title.earned_trophies(platform=None, trophy_group_id="all"):
            earned.append({
                "id": t.trophy_id,
                "earned": t.earned,
                "earned_date": str(t.earned_date_time) if t.earned_date_time else None,
            })
        return jsonify({"trophies": trophies, "earned": earned})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/friends")
def friends():
    result = []
    try:
        for f in client.friends_list():
            try:
                p = f.get_profile_legacy()["profile"]
                avatar = ""
                if p.get("personalDetail") and p["personalDetail"].get("profilePictureUrls"):
                    avatar = p["personalDetail"]["profilePictureUrls"][0]["profilePictureUrl"]
                elif p.get("avatarUrls"):
                    avatar = p["avatarUrls"][-1]["avatarUrl"]
                presences = p.get("presences", [])
                is_online = False
                game = None
                if presences:
                    pr = presences[0]
                    is_online = pr.get("onlineStatus") == "online"
                    game = pr.get("titleName", None) if is_online else None
                trophy_summary = p.get("trophySummary", {})
                earned = trophy_summary.get("earnedTrophies", {})
                result.append({
                    "onlineId": f.online_id,
                    "isOnline": is_online,
                    "gameName": game,
                    "avatarUrl": avatar,
                    "platinum": earned.get("platinum", 0),
                    "gold": earned.get("gold", 0),
                    "silver": earned.get("silver", 0),
                    "bronze": earned.get("bronze", 0),
                    "level": trophy_summary.get("level", 0),
                })
                time.sleep(0.5)
            except Exception as e:
                print(f"Erro no amigo {f.online_id}: {e}")
                result.append({
                    "onlineId": f.online_id,
                    "isOnline": False,
                    "gameName": None,
                    "avatarUrl": "",
                    "platinum": 0,
                    "gold": 0,
                    "silver": 0,
                    "bronze": 0,
                    "level": 0,
                })
                time.sleep(2)
    except Exception as e:
        print("Erro friends:", e)

    result.sort(key=lambda x: not x["isOnline"])
    return jsonify(result)

@app.route("/earned-trophies")
def earned_trophies():
    try:
        result = []
        for t in client.trophy_titles():
            title = psnawp.game_title(
                np_communication_id=t.np_communication_id,
                account_id=str(client.account_id),
                platform=None
            )
            for trofeu in title.earned_trophies(platform=None, trophy_group_id="all"):
                if trofeu.earned and trofeu.earned_date_time:
                    result.append({
                        "game": t.title_name,
                        "type": trofeu.trophy_type.value if trofeu.trophy_type else "bronze",
                        "earned_date": str(trofeu.earned_date_time)
                    })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Servidor PSN rodando em http://localhost:5000")
    app.run(port=5000, debug=True)
