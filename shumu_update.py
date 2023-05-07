import os
import sys
import argparse
import numpy as np
import pandas as pd
from lxml import etree
from hanziconv import HanziConv

import re

pd.set_option('expand_frame_repr', False) # 当列太多时显示不清楚
pd.set_option('display.max_columns', None)  # 显示所有列
# pd.set_option('display.max_rows', 1000)  # 显示所有行
pd.set_option('display.max_colwidth', 60)  # 显示所有行
# pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180) # 设置打印宽度(**重要**)

# 定义一个函数，用于将文本文件转换为树状结构
def txt_to_tree(file_path):
    # 读取文本文件
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    pattern = r"(\d+[n]{0,1})\s*([+]*\s*)\s*(.*)"
    results = [(r[0], r[-1]) for r in re.findall(pattern, text)]
    # 初始化根节点
    root = etree.Element('root')
    # 初始化节点列表和层级列表
    node_list = [root]
    level_list = [0]
    # 遍历每一行
    for line in results:
        # 获取层级和节点名称
        level, original_name = line
        # 将繁体字转换为简体字
        simplified_name = HanziConv.toSimplified(original_name)
        # 创建节点
        node = etree.Element('node', name=simplified_name)
        # 判断是否为末端节点
        if level.endswith('n'):
            level = int(level[:-1])
            # if simplified_name not in df_shuji['书名'].tolist():
            _xi = (df_shuji['书名'] == simplified_name)
            if _xi.sum() == 0:
                # 将信息存入 df_shuji
                node.attrib['type'] = 'shuji'
                node_list[-1].append(node)
                # node_list.append(node)
                # print([n.attrib['name'] for n in node_list[1:]])
                # 获取编号和路径
                bi = len(df_shuji) + 1
                path = '>'.join([n.attrib['name'] for n in node_list[1:]] + [node.attrib['name']])
                df_shuji.loc[bi] = [simplified_name,  bi, '', path]
                node.attrib['bi'] = str(bi)
                # node_list.pop()
                # 将信息存入 df_banben
                # df_banben.loc[len(df_banben)] = [original_name, int(bi), 1, np.nan, np.nan, np.nan, np.nan, np.nan, False, np.nan]
                df_banben.loc[len(df_banben)] = [original_name, int(bi), 1, '', '', '', '', '', False, '']
            else:
                path = '>'.join([n.attrib['name'] for n in node_list[1:]] + [node.attrib['name']])
                _xj = (df_shuji['书名'] == simplified_name) & (df_shuji['书目路径'] == path)
                if _xj.sum() > 1:
                    raise Exception("书目中已经出现重复书名，应改为不同版本存放", simplified_name, original_name)
                bi = df_shuji['bi'][_xj].iloc[0]
                _xj = (df_banben['bi'] == bi)
                max_bbi = df_banben[_xj]['bbi'].max()
                # df_banben.loc[len(df_banben)] = [original_name+f'_v{max_bbi+1}', int(bi), max_bbi+1, np.nan, np.nan, np.nan, np.nan, np.nan, False, np.nan]
                df_banben.loc[len(df_banben)] = [original_name+f'_v{max_bbi+1}', int(bi), max_bbi+1, '', '', '', '', '', False, '']
        else:
            level = int(level)
            # print(level, level_list)
            if level > level_list[-1]:
                # 添加 type="mulu" 属性
                node.attrib['type'] = 'mulu'
                # 将节点添加到父节点的子节点列表中
                node_list[-1].append(node)
                # 将节点和层级添加到列表中
                node_list.append(node)
                level_list.append(level)
            else:
                #-- # 将节点添加到父节点的父节点的子节点列表中
                #-- node_list[-2].append(node)
                # 将节点和层级从列表中删除
                # print(node_list)
                node_list.pop()
                level_list.pop()
                # 添加 type="mulu" 属性
                node.attrib['type'] = 'mulu'
                # 将节点添加到父节点的子节点列表中
                node_list[-1].append(node)
                # 将节点和层级添加到列表中
                node_list.append(node)
                level_list.append(level)
    return root

# 定义一个函数，用于将树状结构保存为 xml 文件
def tree_to_xml(tree, file_path):
    # 创建 ElementTree 对象
    et = etree.ElementTree(tree)
    # 将 ElementTree 对象写入文件
    et.write(file_path, encoding='utf-8', xml_declaration=True, pretty_print=True)    

# ---------------------

from peewee import SqliteDatabase, Model, CharField, IntegerField, BooleanField, IntegrityError
_db_name = "./shuku.sqlite"
db = SqliteDatabase(_db_name)

class ShujiTable(Model):
    id = IntegerField(primary_key=True)
    book_name = CharField()
    bi = IntegerField(unique=True)
    author = CharField()
    biblio_path = CharField()
    class Meta:
        database = db
        table_name = 'tb_shuji'

class BanbenTable(Model):
    id = IntegerField(primary_key=True)
    pub_name = CharField()
    # bi = IntegerField(unique=True)
    bi = IntegerField()
    bbi = IntegerField()
    modifier = CharField()
    modify_type = CharField()
    content_source = CharField()
    source_type = CharField()
    source_detail = CharField()
    record_status = BooleanField(default=False)
    recorder = CharField()
    class Meta:
        database = db
        table_name = 'tb_banben'
        indexes = (('bi', 'bbi'), True), 
        # 定义了 bi 和 bbi 的联合唯一索引

ap = argparse.ArgumentParser()
ap.add_argument('-a', '--append', action='store_true', default=False)
ap.add_argument('date', nargs='?', default='')
args = ap.parse_args()

if db.table_exists('tb_shuji') and db.table_exists('tb_banben'):
    # 定义 df_shuji 和 df_banben
    # df_mulu = pd.DataFrame(columns=['书目', 'mi'])
    # print(ShujiTable.select().dicts())
    # df_shuji = pd.DataFrame(list(ShujiTable.select().dicts()), columns=['书名', 'bi', '作者', '书目路径'])
    if args.append:
        df_shuji = pd.DataFrame(list(ShujiTable.select(
            ShujiTable.book_name.alias('书名'),
            ShujiTable.bi,
            ShujiTable.author.alias('作者'),
            ShujiTable.biblio_path.alias('书目路径')    
        ).dicts()))
        df_banben = pd.DataFrame(list(BanbenTable.select(
            BanbenTable.pub_name.alias('版本名'),
            BanbenTable.bi,
            BanbenTable.bbi,
            BanbenTable.modifier.alias('编辑人'),
            BanbenTable.modify_type.alias('编辑类型'),
            BanbenTable.content_source.alias('录入来源'),
            BanbenTable.source_type.alias('来源类型'),
            BanbenTable.source_detail.alias('来源细节'),
            BanbenTable.record_status.alias('录入状态'),
            BanbenTable.recorder.alias('录入人')
        ).dicts()))
    else:
        pass   
    # db.connect()
else:
    db.create_tables([ShujiTable, BanbenTable])

if not args.append:
    df_shuji = pd.DataFrame(columns=['书名', 'bi', '作者', '书目路径'])
    df_banben = pd.DataFrame(columns=['版本名', 'bi', 'bbi', '编辑人', '编辑类型', '录入来源', '来源类型', '来源细节', '录入状态', '录入人'])

print("操作之前")
print(df_shuji)
print(df_banben)

print("转换")
# 将文本文件转换为树状结构
tree = txt_to_tree('shumu_test.txt')
# 将树状结构保存为 xml 文件
tree_to_xml(tree, 'shumu_test.xml')

print("转换后")
# print(df_mulu)
print(df_shuji)
print(df_banben)

_xj = (df_banben['bbi'] > 1)
print(df_banben[_xj])
# print(df_banben[df_banben['版本名'] == '大唐西域记'])
print(df_banben[df_banben['版本名'].str.contains('大唐西域记')])

# 将 df_shuji 中的数据写入数据库
for row in df_shuji.itertuples(index=False):
    row = row._asdict()
    record = ShujiTable(book_name=row['书名'], bi=row['bi'], author=row['作者'], biblio_path=row['书目路径'])
    try:
        record.save(force_insert=True)  # 使用 save() 方法并将 force_insert 参数设置为 True，以便在主键冲突时执行 INSERT OR IGNORE
    except IntegrityError:
        pass

# 将 df_banben 中的数据写入数据库
for row in df_banben.itertuples(index=False):
    row = row._asdict()
    record = BanbenTable(
        pub_name=row['版本名'], bi=row['bi'], bbi=row['bbi'], 
        modifier=row['编辑人'], modify_type=row['编辑类型'], 
        content_source=row['录入来源'], source_type=row['来源类型'], source_detail=row['来源细节'], 
        record_status=row['录入状态'], recorder=row['录入人']
    )
    try:
        record.save(force_insert=True)  # 使用 save() 方法并将 force_insert 参数设置为 True，以便在主键冲突时执行 INSERT OR IGNORE
    except IntegrityError:
        pass
