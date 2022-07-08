import datetime

from zhdate import ZhDate


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
    return week_day_dict[date.weekday()]


def __get_closing_time(opening_time: str = "09:00:00", closing_time: str = "17:00:00"):
    now = datetime.datetime.now()
    opening = datetime.datetime.strptime(
        f"{now.year}-{now.month}-{now.day} {opening_time}", "%Y-%m-%d %H:%M:%S"
    )
    closing = datetime.datetime.strptime(
        f"{now.year}-{now.month}-{now.day} {closing_time}", "%Y-%m-%d %H:%M:%S"
    )
    if not (opening < now < closing):
        return
    time_delta_ = closing - now
    secs = time_delta_.seconds
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    return f"{hours} 小时 {minutes} 分钟"


def __time_parse(today):
    def __get_distance_lunar_month_day(month: int, day: int) -> int:
        __distance = (ZhDate(today.year, month, day).to_datetime().date() - today).days
        return (
            __distance
            if __distance > 0
            else (ZhDate(today.year + 1, month, day).to_datetime().date() - today).days
        )

    def __get_distance_month_day(month: int, day: int) -> int:
        __distance = (
            datetime.datetime.strptime(
                f"{today.year}-{month:02d}-{day:02d}", "%Y-%m-%d"
            ).date()
            - today
        ).days
        return (
            __distance
            if __distance > 0
            else (
                datetime.datetime.strptime(
                    f"{today.year + 1}-{month:02d}-{day:02d}", "%Y-%m-%d"
                ).date()
                - today
            ).days
        )

    time = [
        {"v": max(5 - 1 - today.weekday(), 0), "title": "周末"},
        {"v": __get_distance_month_day(1, 1), "title": "元旦"},
        {"v": __get_distance_lunar_month_day(1, 1), "title": "过年"},
        {"v": __get_distance_month_day(4, 5), "title": "清明节"},
        {"v": __get_distance_month_day(5, 1), "title": "劳动节"},
        {"v": __get_distance_lunar_month_day(5, 5), "title": "端午节"},
        {"v": __get_distance_lunar_month_day(8, 15), "title": "中秋节"},
        {"v": __get_distance_month_day(10, 1), "title": "国庆节"},
    ]

    return sorted(time, key=lambda x: x["v"], reverse=False)


def get_text():
    """你好，摸鱼人，工作再累，一定不要忘记摸鱼哦 !"""

    today = datetime.date.today()
    now_ = f"{today.year}年{today.month}月{today.day}日"
    week_day_ = __get_week_day(today)

    if datetime.date.today().weekday() in (5, 6):
        return f"{now_} {week_day_}\n不会有人周末还上班吧！\n\n摸鱼办"

    output = (
        f"{now_} {week_day_}"
        "\n\n你好，摸鱼人，工作再累，一定不要忘记摸鱼哦! "
        "\n有事没事起身去茶水间去廊道去天台走走，别老在工位上坐着。"
        "\n多喝点水，钱是老板的，但命是自己的 !\n"
    )

    for t_ in __time_parse(today):
        output += f'\n距离{t_.get("title")}还有: {t_.get("v")}天'

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
