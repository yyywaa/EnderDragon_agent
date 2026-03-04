这是一个聊天agent，至少现在只有聊天功能，以后再考虑给它开放指令，让它干点别的事情。
下面是函数介绍：
1.get_memory_str
该函数将读取储存起来的记忆，输出字符串。若无记忆，输出‘你还没有相关的记忆，去观察玩家们吧。’
参数为记忆文件名称，请带上txt后缀
我已经在模型的prompt中加入了记忆

2.dragon_eyes(content_JSON, model=default_model_1, llm_site=default_llm_site, api_key=key_yyy)
参数解释：json格式的聊天记录，只需要导出聊天室的json即可，我已做好字段名的匹配和时间戳的转换
模型名称，如deepseek-chat为默认
模型url
api_key，若设定了其他模型，请填写该参数，默认为我的账户的apikey
该函数将读取聊天记录，使模型以末影龙的身份判断是否对最后一条消息进行回复。yes/no

3.json2str(content_JSON)
将聊天室的json格式记录转化为字符串
【当前房间内的聊天记录】
【时间：[time]】  sender:text

4.dragon_speaking(content_JSON, model=default_model_1, llm_site=default_llm_site, api_key=key_yyy)
默认模型为deepseek-reasoner，其余参数同dragon_eyes
调用后将调用llm生成回复文本

5.memory_conclude(content_JSON, model=default_model_2, llm_site=default_llm_site, api_key=key_yyy, memory_filenm='dragon_memory.txt')
目前只会针对json中的所有记录在memory中的记忆文件中进行添加记忆，请自行设定触发条件。

6.memory_compress(model=default_model_2, llm_site=default_llm_site, api_key=key_yyy, memory_filenm='dragon_memory.txt')
【较危险】
会覆写记忆文件，如果不想误删记忆文件的内容，请小心使用！（因为没有足够的记忆数据，该函数还未测试）
在记忆文件占用token过大时使用，会精简文件内容

测试说明：运行mock_server.py后打开mock_ui，选择连接即可测试
