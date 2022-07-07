import datetime

from zhdate import ZhDate as lunar_date

from module.build_image.aworda_text_to_image.text2image import create_image


def __get_week_day(date):
    week_day_dict = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期天",
    }
    day = date.weekday()
    return week_day_dict[day]


def __get_closing_time(closing_time: str = "18:00:00"):
    now_ = datetime.datetime.now()
    target_ = datetime.datetime.strptime(
        f"{now_.year}-{now_.month}-{now_.day} {closing_time}", "%Y-%m-%d %H:%M:%S"
    )
    if now_ < target_:
        time_delta_ = target_ - now_
        secs = time_delta_.seconds
        hours = secs // 3600
        mins = (secs % 3600) // 60
        return f"{hours} 小时 {mins} 分钟"
    return False


def __time_parse(today):
    distance_big_year = (lunar_date(today.year, 1, 1).to_datetime().date() - today).days
    distance_big_year = (
        distance_big_year
        if distance_big_year > 0
        else (lunar_date(today.year + 1, 1, 1).to_datetime().date() - today).days
    )

    distance_5_5 = (lunar_date(today.year, 5, 5).to_datetime().date() - today).days
    distance_5_5 = (
        distance_5_5
        if distance_5_5 > 0
        else (lunar_date(today.year + 1, 5, 5).to_datetime().date() - today).days
    )

    distance_8_15 = (lunar_date(today.year, 8, 15).to_datetime().date() - today).days
    distance_8_15 = (
        distance_8_15
        if distance_8_15 > 0
        else (lunar_date(today.year + 1, 8, 15).to_datetime().date() - today).days
    )

    distance_year = (
        datetime.datetime.strptime(f"{today.year}-01-01", "%Y-%m-%d").date() - today
    ).days
    distance_year = (
        distance_year
        if distance_year > 0
        else (
            datetime.datetime.strptime(f"{today.year + 1}-01-01", "%Y-%m-%d").date()
            - today
        ).days
    )

    distance_4_5 = (
        datetime.datetime.strptime(f"{today.year}-04-05", "%Y-%m-%d").date() - today
    ).days
    distance_4_5 = (
        distance_4_5
        if distance_4_5 > 0
        else (
            datetime.datetime.strptime(f"{today.year + 1}-04-05", "%Y-%m-%d").date()
            - today
        ).days
    )

    distance_5_1 = (
        datetime.datetime.strptime(f"{today.year}-05-01", "%Y-%m-%d").date() - today
    ).days
    distance_5_1 = (
        distance_5_1
        if distance_5_1 > 0
        else (
            datetime.datetime.strptime(f"{today.year + 1}-05-01", "%Y-%m-%d").date()
            - today
        ).days
    )

    distance_10_1 = (
        datetime.datetime.strptime(f"{today.year}-10-01", "%Y-%m-%d").date() - today
    ).days
    distance_10_1 = (
        distance_10_1
        if distance_10_1 > 0
        else (
            datetime.datetime.strptime(f"{today.year + 1}-10-01", "%Y-%m-%d").date()
            - today
        ).days
    )

    distance_week_ = 5 - 1 - today.weekday()

    time_ = [
        {"v_": max(distance_week_, 0), "title": "周末"},
        {"v_": distance_year, "title": "元旦"},
        {"v_": distance_big_year, "title": "过年"},
        {"v_": distance_4_5, "title": "清明节"},
        {"v_": distance_5_1, "title": "劳动节"},
        {"v_": distance_5_5, "title": "端午节"},
        {"v_": distance_8_15, "title": "中秋节"},
        {"v_": distance_10_1, "title": "国庆节"},
    ]

    time_ = sorted(time_, key=lambda x: x["v_"], reverse=False)
    return time_


def get_text():
    """你好，摸鱼人，工作再累，一定不要忘记摸鱼哦 !"""

    output = ""
    today = datetime.date.today()
    now_ = f"{today.year}年{today.month}月{today.day}日"
    week_day_ = __get_week_day(today)
    output += (
        f"{now_} {week_day_}"
        "\n你好，摸鱼人，工作再累，一定不要忘记摸鱼哦! "
        "\n有事没事起身去茶水间去廊道去天台走走，别老在工位上坐着。"
        "\n多喝点水，钱是老板的，但命是自己的 !"
    )

    time_ = __time_parse(today)
    for t_ in time_:
        output += f'\n距离{t_.get("title")}还有: {t_.get("v_")}天'

    if today.weekday() in range(5) and __get_closing_time():
        output += f"\n此时距离下班时间还有 {__get_closing_time()}。"
        output += f"\n请提前整理好自己的桌面, 到点下班。\n"

    output += (
        "\n\n"
        "[友情提示]\n"
        "三甲医院 ICU 躺一天平均费用大概一万块。"
        "你晚一天进 ICU，就等于为你的家庭多赚一万块。"
        "\n少上班，多摸鱼。"
        "\n\n摸鱼办"
    )

    return output
