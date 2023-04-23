# 测试基座模型的能力

_QUANTIZE = 0
_TOP_PERCENT = 0.7
_TEMPERATURE = 0.9

import os
import csv
import psutil
import pandas as pd
import asyncio
from hanziconv import HanziConv

_cpu_cols = ['timestamp', 'load_1m', 'load_5m', 'load_15m', 'cpu', 'mem', 'swap']
_gpu_cols = ['timestamp', 'gpu_id', 'gpu', 'gpu_mem', 'gpu_mem_used', 'gpu_mem_total', 'pci']
_bgn_time = pd.Timestamp.now()
_terminal = 0
global _j
_j = 0
_text_dir = "./chatglm_test/text"
_model_name = "THUM/chatglm"

df_cpu = pd.DataFrame(columns=_cpu_cols)
df_gpu = pd.DataFrame(columns=_gpu_cols)
df_test_item = pd.DataFrame(columns=['id', 'timestamp', 'test_name', 'test_item'])

async def resource_monitor():
    while not _terminal:
        t = (pd.Timestamp.now() - _bgn_time).total_seconds()
        # 获取系统负载情况
        load = psutil.getloadavg()
        # 获取CPU使用率
        # cpu = psutil.cpu_percent(interval=1, percpu=True)
        cpu = psutil.cpu_percent(interval=None)
        # 获取内存使用情况
        mem = psutil.virtual_memory() 
        # 获取交换空间使用情况
        swap = psutil.swap_memory()
        # 获取GPU使用情况（所有显卡）
        gpu_info = os.popen('nvidia-smi --query-gpu=index,utilization.gpu,utilization.memory,memory.used,memory.total,pci --format=csv')
        gpu_info = list(csv.reader(gpu_info))
        # 获取所有显卡的使用情况
        # gpu_mem = [int(i[1].strip().split()[0]) for i in gpu_info[1:]]
        df_tmp = pd.DataFrame(gpu_info[1:], colunms=_gpu_cols[1:])
        df_tmp['timestamp'] = t
        df_gpu = df_gpu.append(df_tmp)
        print(f"记录系统开销于第{t}秒...")
        asyncio.sleep(2)

async def chat_test(robot, prompts, test_name, test_item):
    _j += 1
    t = (pd.Timestamp.now() - _bgn_time).total_seconds()
    print(f"\n{t}, {test_name}, {test_item}")
    df_test_item.loc[_j] = [_j, t, test_name, test_item]
    history = []
    tokenizer = robot[0]
    model = robot[1]
    for prompt in prompts:
        print(f"提问: {prompt}")
        response, history = model.chat(tokenizer, prompt, history=history, max_length=20480, top_p=_TOP_PERCENT, temperature=_TEMPERATURE)
        print(f"回答: {response}")
    asyncio.sleep(10)
    print('\n' + '-'*24 + '>\n')    

async def main():
    def read_file(path):
        return '\n'.join([line for line in open(path).readlines() if not line.strip().startswith('#')])
        
    from transformers import AutoTokenizer, AutoModel
    tokenizer = AutoTokenizer.from_pretrained(_model_name, trust_remote_code=True)
    if not _QUANTIZE:
        model = AutoModel.from_pretrained(_model_name, trust_remote_code=True).half().cuda()
    else:
        model = AutoModel.from_pretrained(_model_name, trust_remote_code=True).quantize(_QUANTIZE).half().cuda()
    model = model.eval()
    robot = (tokenizer, model)
    
    df_test_item.set_index('id')
    df_test_item.loc[_j] = [_j, 0, f"开始测试...(TOP_P={_TOP_PERCENT}, TEMPERATURE={_TEMPERATURE}, QUANTIZE={_QUANTIZE})"]
    _bgn_time = pd.Timestamp.now()
    # asyncio.run(resource_monitor())
    monitor = asyncio.ensure_future(resource_monitor())
    asyncio.sleep(5)
    
    test_name = "00.基本测试"
    prompts = [
        "你好",
        "你知道中国古代史中的西域大秦国吗？",
        "鱼豢在什么著作中描述过这个大秦国？",
        "能否全文背诵唐代王勃的《滕王阁序》？"
    ]
    await asyncio.ensure_future(chat_test(test_name, "Test: 测试基本的历史知识和古文能力", robot, prompts))

    test_name = "01.模糊搜索"
    test_item = "Test: 测试模糊搜索能力"
    text = open(os.path.join(_text_dir, f"{test_name}.txt")).read()
    prompts = [
        text,
        "上文中有提到班固做了些什么？",  # 实际没有班固的内容
        "请把其中提到“大月氏”的段落中最前面两段找出来并原封不动的打印出来"
    ]
    await asyncio.ensure_future(chat_test(test_name, test_item, robot, prompts))
  
    test_name = "02.格式识别"
    test_item = "Test: 测试文本格式识别能力"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    prompts = [text]
    await asyncio.ensure_future(chat_test(robot, prompts, test_name, test_item))
   
    test_name = "03.繁简转换-1"
    test_item = "Test: 测试繁简转换能力（一般指令）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "03.繁简转换-2"
    test_item = "Test: 测试繁简转换能力（详细指令）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    # 这种繁简转换其实用专门的转换模块更好，这里只是测试AI的能力边界和提示词的规则
    
    test_name = "04.段落复原-1"
    test_item = "Test: 测试段落复原（告知段数）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "04.段落复原-2"
    test_item = "Test: 测试段落复原（不告知段数）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "04.段落复原-3"
    test_item = "Test: 测试段落复原（前后带不完整段落多余文字）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "04.段落复原-4"
    test_item = "Test: 测试段落复原，挤成一团的大片文字分段（现代汉语）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "04.段落复原-5"
    test_item = "Test: 测试段落复原，挤成一团的大片文字分段（古文带标点）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "04.段落复原-6"
    test_item = "Test: 测试段落复原，挤成一团的大片文字分段（古文不带标点）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "05.文本对齐-1"
    test_item = "Test: 测试文本对齐，按略微修改的乙本片段找出甲本中的对应片段"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    # 完全按照乙本的首尾字截断，但采用原来甲本段落格式不变，甲本被截断前后部分用省略号标识

    test_name = "05.文本对齐-2"
    test_item = "Test: 测试文本对齐，找出无标点古籍（乙本）片段在甲本中的对应片段（简体）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "05.文本对齐-3"
    test_item = "Test: 测试文本对齐，找出无标点古籍（乙本）片段在甲本中的对应片段（繁体）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "05.文本对齐-4"
    test_item = "Test: 测试文本对齐，无标点且按扫描分段的古籍乙本片段在甲本中的对应段落"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    text = HanziConv.toSimplified(text)
    await asyncio.ensure_future(chat_test(robot, [text], test_name+'S', test_item))
    
    test_name = "05.文本对齐-5"
    test_item = "Test: 测试文本对齐，无标点且前后带多余文字的古籍乙本片段在甲本中的对应段落"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    text = HanziConv.toSimplified(text)
    await asyncio.ensure_future(chat_test(robot, [text], test_name+'S', test_item))

    test_name = "05.文本对齐-6"
    test_item = "Test: 测试文本对齐，无标点且按扫描分段并带有前后多余文字的古籍乙本片段在甲本中的对应段落"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    text = HanziConv.toSimplified(text)
    await asyncio.ensure_future(chat_test(robot, [text], test_name+'S', test_item))
    # new_prompt = "以下有两段文本，称为[甲本]、[乙本]，请根据意思找出两本中重叠的片段"
    
    # test_name = "05.文本对齐-7"
    # test_item = "Test: 测试两段文字完全不相干的情况"
    # text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    # await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    
    # 文本对齐 重叠状态：上叠、下叠、中间重叠（如摘录和原本的情况）、乙本大于甲本、乱序重叠 等情况
    # 文本对齐 完全不对应的状态

    test_name = "06.自动标点-1"
    test_item = "Test: 测试自动标点，扫描古籍段落在无对齐情况下自理解恢复段落加标点"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    text = HanziConv.toSimplified(text)
    await asyncio.ensure_future(chat_test(robot, [text], test_name+'S', test_item))

    #test_name = "06.自动标点-2"
    #test_item = "Test: 测试自动标点，扫描古籍段落且前后带多余文字在无对齐情况下自理解恢复段落加标点"
    #text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    #await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    #test_name = "06.自动标点-3"
    #test_item = "Test: 测试自动标点，根据标准的甲本将扫描的古籍段落乙本加标点"
    #text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    #await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    #test_name = "06.自动标点-4"
    #test_item = "Test: 测试自动标点，根据标准的甲本将扫描的古籍段落且前后带多余文字的乙本加标点"
    #text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    #await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    test_name = "07.自动校对-1"
    test_item = "Test: 测试自动校对，两段完全无关文字（应报告不匹配错误）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    
    test_name = "07.自动校对-2"
    test_item = "Test: 测试自动校对，两段对齐文本标记差异的字"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    
    test_name = "07.自动校对-2n"
    test_item = "Test: 测试自动校对，两段对齐文本标记差异的字（忽略标点）"
    text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    
    #test_name = "07.自动校对-3"
    #test_item = "Test: 测试自动校对，两段未对齐文本标记差异的字（要先自动对齐）" 
    #text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    #await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    #test_name = "07.自动校对-4"
    #test_item = "Test: 测试自动校对，两段未对齐文本标记差异的字（要先自动对齐，并忽略标点）"
    #text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    #await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))

    #test_name = "07.自动校对-5"
    #test_item = "Test: 测试自动校对，两段未对齐文本且前后带多余文字，标记差异的字（先自动对齐）" 
    #text = read_file(os.path.join(_text_dir, f"{test_name}.txt"))
    #await asyncio.ensure_future(chat_test(robot, [text], test_name, test_item))
    
    # 测试查重、去重：在搜索结果中去重（去除意思基本一致仅文字略有出入的内容，仅列出其他文献名及章节等即可）

    # 通知监控子任务并等待其结束
    _terminal = 1
    await monitor
    
    df_temp = pd.merge(df_cpu, df_gpu, on='timestamp')
    df_timeline = pd.merge(df_test_item, df_temp, on='timestamp')
    m_name = _model_name.replace('/', '-')
    df_timeline.to_csv(f"~/{m_name}.{_QUANTIZE}-{_TOP_PERCENT*100}-{_TEMPERATURE*100}.csv")

asyncio.run(main())
