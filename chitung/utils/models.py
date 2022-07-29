from enum import Enum
from typing import List, Literal, Union

from graia.ariadne import Ariadne
from graia.ariadne.model import Group, Member
from pydantic import BaseModel, Field


class FunctionControl(BaseModel):
    fish: bool = True
    casino: bool = True
    responder: bool = True
    lottery: bool = True
    game: bool = True


class CustomizationConfig(BaseModel):
    joinGroupText: str = "很高兴为您服务。在使用本 bot 之前，请仔细阅读下方的免责协议。"
    onlineText: str = "机器人已经上线。"
    welcomeText: str = "欢迎。"
    permissionChangedText: str = "谢谢，各位将获得更多的乐趣。"
    groupNameChangedText: str = "好名字。"
    nudgeText: str = "啥事？"


class Config(BaseModel):
    botName: str = ""
    devGroupID: List[int] = []
    adminID: List[int] = []
    minimumMembers: int = 7
    friendFC: FunctionControl = FunctionControl()
    groupFC: FunctionControl = FunctionControl()
    cc: CustomizationConfig = CustomizationConfig()


class GroupSwitch(Enum):
    globalControl = "globalControl"
    fish = "fish"
    casino = "casino"
    responder = "responder"
    lottery = "lottery"
    game = "game"


class GroupConfig(BaseModel):
    groupID: int
    globalControl: bool = Field(True, alias="global")
    fish: bool = True
    casino: bool = True
    responder: bool = True
    lottery: bool = True
    game: bool = True
    blockedUser: List[int] = []


class GroupConfigList(BaseModel):
    groupConfigList: List[GroupConfig] = []

    async def check(self):
        if group_list := await Ariadne.current().get_group_list():
            for group in group_list:
                assert isinstance(group, Group)
                if _ := self.get(group.id, create_if_none=False):
                    continue
                self.groupConfigList.append(GroupConfig(groupID=group.id))

    def get(self, group_id: int, *, create_if_none: bool = True):
        if group_config := list(
            filter(lambda cfg: cfg.groupID == group_id, self.groupConfigList)
        ):
            return group_config[0]
        elif create_if_none:
            self.groupConfigList.append(GroupConfig(groupID=group_id))
            return self.get(group_id, create_if_none=False)

    def block_member(self, group: Union[Group, int], target: Union[Member, int]):
        group = group.id if isinstance(group, Group) else group
        target = target.id if isinstance(target, Member) else target
        if cfg := self.get(group):
            cfg.blockedUser.append(target)

    def unblock_member(self, group: Union[Group, int], target: Union[Member, int]):
        group = group.id if isinstance(group, Group) else group
        target = target.id if isinstance(target, Member) else target
        if cfg := self.get(group):
            if target in cfg.blockedUser:
                cfg.blockedUser.remove(target)
                return True
            return False

    def alt_setting(
        self, group: Union[Group, int], setting: GroupSwitch, new_value: bool
    ):
        group = group.id if isinstance(group, Group) else group
        if cfg := self.get(group):
            setattr(cfg, setting.value, new_value)


class UniversalRespond(BaseModel):
    messageKind: Literal["Friend", "Group", "Any"]
    listResponseKind: Literal["Friend", "Group"]
    listKind: Literal["Black", "White"]
    userList: List[int]
    triggerKind: Literal["Equal", "Contain"]
    pattern: List[str]
    answer: List[str]


class UniversalRespondList(BaseModel):
    universalRespondList: List[UniversalRespond]


class UniversalImageResponder(BaseModel):
    keyword: List[str]
    directoryName: str
    text: str
    triggerType: Literal["Equal", "Contain"]
    responseType: Literal["Friend", "Group", "Any"]


class UniversalImageResponderList(BaseModel):
    dataList: List[UniversalImageResponder]
