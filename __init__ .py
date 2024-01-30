import json
from nonebot import get_driver
from nonebot.plugin import PluginMetadata
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from .config import Config
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot,Event,GroupMessageEvent
from nonebot.permission import SUPERUSER


__plugin_meta__ = PluginMetadata(
    name="godownsystem",
    description="实现maimai上下机排队功能",
    usage="",
    config=Config,
)

global_config = get_driver().config
config = Config.parse_obj(global_config)


data_json={}
data_path=r""



def init_data():
    global data_json
    with open(data_path , encoding='utf-8') as f:
        data_json=json.load(f)

# 初始化和加载数据
init_data()

go_on=on_command("上机")#将当前第一位排队的移至最后
get_in=on_command("排卡")#加入排队队列
get_run=on_command("退勤")#退出排队队列
show_list=on_command("排卡现状")#展示排队队列
add_group=on_command("添加群聊")#添加群聊到json
shut_down=on_command("闭店")#清空排队队列
add_arcade=on_command("添加机厅")#添加机厅到群聊
show_arcade=on_command("机厅列表")#展示机厅列表
put_off=on_command("延后")#将自己延后一位

@go_on.handle()
async def handle_function(bot:Bot,event:GroupMessageEvent):
    global data_json
    group_id=str(event.group_id)
    user_id = str(event.get_user_id())
    nickname = event.sender.nickname
    if group_id in data_json:
        for n in data_json[group_id]:
            if nickname in data_json[group_id][n]['list']:
                group_list=data_json[group_id][n]['list']
                if (len(group_list)>1 and nickname == group_list[0]) :
                    msg="收到，已将"+str(n)+"机厅中"+group_list[0]+"移至最后一位,下一位上机的是"+group_list[1]+",当前一共有"+str(len(group_list))+"人。"
                    tmp_name=[nickname]
                    data_json[group_id][n]['list']=data_json[group_id][n]['list'][1:]+tmp_name
                    await re_write_json()
                    await go_on.finish(MessageSegment.text(msg))
                elif (len(group_list)==1 and nickname == group_list[0]):
                    msg="收到,"+str(n)+"机厅人数1人,您可以爽霸啦。"
                    await go_on.finish(MessageSegment.text(msg))
                else:
                    await go_on.finish(f"暂时未到您,请耐心等待。")
        await go_on.finish(f"您尚未排卡。")
    else:
        await go_on.finish(f"本群尚未开通排卡功能,请联系群主或管理员")

@get_in.handle()
async def handle_function(bot:Bot,event:GroupMessageEvent,name_: Message = CommandArg()):
    global data_json
    name=str(name_)
    group_id=str(event.group_id)
    user_id = str(event.get_user_id())
    nickname = event.sender.nickname
    if group_id in data_json:
        for n in data_json[group_id]:
            if nickname in data_json[group_id][n]['list']:
                await go_on.finish(f"您已加入或正在其他机厅排卡")
        if (name in data_json[group_id]) and name:
            tmp_name=[nickname]
            data_json[group_id][name]['list']=data_json[group_id][name]['list']+tmp_name
            await re_write_json()
            msg="收到,您已加入排卡。当前您位于第"+str(len(data_json[group_id][name]['list']))+"位。"
            await go_on.finish(MessageSegment.text(msg))
        elif not name:
            await go_on.finish(f"请输入机厅名称。")
        else:
            await go_on.finish(f"没有该机厅，若需要可使用添加机厅功能。")
    else:
        await go_on.finish(f"本群尚未开通排卡功能,请联系群主或管理员")

@get_run.handle()
async def handle_function(bot:Bot,event:GroupMessageEvent):
    global data_json
    group_id=str(event.group_id)
    user_id = str(event.get_user_id())
    nickname = event.sender.nickname
    if group_id in data_json:
        if data_json[group_id] == {}:
            await get_run.finish('本群没有机厅')
        for n in data_json[group_id]:
            if nickname in data_json[group_id][n]['list']:
                msg=nickname+"从"+str(n)+"退勤成功"
                data_json[group_id][n]['list'].remove(nickname)
                await re_write_json()
                await go_on.finish(MessageSegment.text(msg))
        await go_on.finish(f"今晚被白丝小萝莉魅魔榨精（您未加入排卡）")
    else:
        await go_on.finish(f"本群尚未开通排卡功能,请联系群主或管理员")

@show_list.handle()
async def handle_function(bot:Bot,event:GroupMessageEvent,name_: Message = CommandArg()):
    global data_json
    name=str(name_)
    group_id=str(event.group_id)
    if group_id in data_json:
        if (name in data_json[group_id]) and name:
            msg=str(name)+"机厅排卡如下：\n"
            num=0
            for n in data_json[group_id][name]['list']:
                msg=msg+"第"+str(num+1)+"位："+data_json[group_id][name]['list'][num]+"\n"
                num=num+1
            await go_on.finish(MessageSegment.text(msg))
        elif not name:
            await go_on.finish(f"请输入机厅名")
        else:
            await go_on.finish(f"没有该机厅，若需要可使用添加机厅功能。")
    else:
        await go_on.finish(f"本群尚未开通排卡功能,请联系群主或管理员")


@shut_down.handle()
async def handle_function(bot:Bot,event:GroupMessageEvent,name_: Message = CommandArg()):
    global data_json
    group_id=str(event.group_id)
    name=str(name_)
    if group_id in data_json:
        if event.sender.role not in ["admin", "owner"]:
            await go_on.finish(f"只有管理员能够闭店")
        if (name in data_json[group_id]) and name:
            data_json[group_id][name]['list'].clear()
            await re_write_json()
            await go_on.finish(f"闭店成功，当前排卡零人。")
        elif not name:
            await go_on.finish(f"请输入机厅名称。")
        else:
            await go_on.finish(f"没有该机厅，若需要可使用添加机厅功能。")
    else:
        await go_on.finish(f"本群尚未开通排卡功能,请联系群主或管理员")    

@add_group.handle()
async def handle_function(bot:Bot,event:GroupMessageEvent):
    
    #group_members=await bot.get_group_member_list(group_id=event.group_id)
    #for m in group_members:
    #    if m['user_id'] == event.user_id:
    #        break
    #su=get_driver().config.superusers
    #if str(event.get_user_id()) != '347492847' or str(event.get_user_id()) != '1415279603':
    #   if m['role'] != 'owner' and m['role'] != 'admin' and str(m['user_id']) not in su:
    #        await add_group.finish("只有管理员对排卡功能进行设置")
    if event.sender.role not in ["admin", "owner"]:
            await go_on.finish(f"只有管理员能够添加群聊")
    
    global data_json
    group_id=str(event.group_id)
    if group_id in data_json:
        await go_on.finish(f"当前群聊已在名单中。")
    else:
        data_json[group_id]={}
        await re_write_json()
        await go_on.finish(f"已添加当前群聊到名单中")

@add_arcade.handle()
async def handle_function(bot:Bot,event:GroupMessageEvent,name_: Message = CommandArg()):
    global data_json
    name=str(name_)
    group_id = str(event.group_id)
    if group_id in data_json:
        if event.sender.role not in ["admin", "owner"]:
            await go_on.finish(f"只有管理员能够添加机厅")
        if not name:
            await add_arcade.finish(f"请输入机厅名称")
        elif name in data_json[group_id]:
            await add_arcade.finish(f"机厅已在群聊中")
        else:
            tmp = {"list": []}
            data_json[group_id][name]=tmp
            await re_write_json()
            await add_arcade.finish(f"已添加当前机厅到群聊名单中")
    else:
        await add_arcade.finish(f"本群尚未开通排卡功能,请联系群主或管理员")

@show_arcade.handle()
async def handle_function(bot:Bot,event:GroupMessageEvent):
    global data_json
    group_id=str(event.group_id)
    if group_id in data_json:
        msg="机厅列表如下：\n"
        num=0
        for n in data_json[group_id]:
            msg=msg+str(num+1)+"："+n+"\n"
            num=num+1
        await go_on.finish(MessageSegment.text(msg.rstrip('\n')))
    else:
        await go_on.finish(f"本群尚未开通排卡功能,请联系群主或管理员")

@put_off.handle()
async def handle_function(bot:Bot,event:GroupMessageEvent):
    global data_json
    group_id=str(event.group_id)
    user_id = str(event.get_user_id())
    nickname = event.sender.nickname
    if group_id in data_json:
        num=0
        for n in data_json[group_id]:
            if nickname in data_json[group_id][n]['list']:
                group_list=data_json[group_id][n]['list']
                if num+1 !=len(group_list):
                    msg="收到，已将"+str(n)+"机厅中"+group_list[num]+"与"+group_list[num+1]+"调换位置"
                    tmp_name=[nickname]
                    data_json[group_id][n]['list'][num],data_json[group_id][n]['list'][num+1]=data_json[group_id][n]['list'][num+1],data_json[group_id][n]['list'][num]
                    await re_write_json()
                    await go_on.finish(MessageSegment.text(msg))
                else:
                    await go_on.finish(f"您无需延后。")
            num = num + 1
        await go_on.finish(f"您尚未排卡。")
    else:
        await go_on.finish(f"本群尚未开通排卡功能,请联系群主或管理员")

async def re_write_json():#复写json文档
    global data_json
    with open(data_path , 'w' , encoding='utf-8') as f:
        json.dump(data_json , f , indent=4, ensure_ascii=False)
