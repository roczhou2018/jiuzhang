
import os
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

# 定义 df_shuji 和 df_banben
# df_mulu = pd.DataFrame(columns=['书目', 'mi'])
df_shuji = pd.DataFrame(columns=['书名', 'bi', '作者', '书目路径'])
df_banben = pd.DataFrame(columns=['版本', 'bi', 'bbi', '修改者', '修改类型', '录入来源', '来源类型', '来源细节', '录入状态', '录入人'])
_db_name = "./shuku.sqlite"

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
                path = '·］'.join([n.attrib['name'] for n in node_list[1:]] + [node.attrib['name']])
                df_shuji.loc[bi] = [simplified_name,  bi, '', path]
                node.attrib['bi'] = str(bi)
                # node_list.pop()
                # 将信息存入 df_banben
                df_banben.loc[len(df_banben)] = [original_name, int(bi), 1, '', '', '', '', '', False, '']
            else:
                path = '··>'.join([n.attrib['name'] for n in node_list[1:]] + [node.attrib['name']])
                _xj = (df_shuji['书名'] == simplified_name) & (df_shuji['书目路径'] == path)
                if _xj.sum() > 1:
                    raise Exception("书目中已经出现重复书名，应改为不同版本存放", simplified_name, original_name)
                bi = df_shuji['bi'][_xj].iloc[0]
                _xj = (df_banben['bi'] == bi)
                max_bbi = df_banben[_xj]['bbi'].max()
                df_banben.loc[len(df_banben)] = [original_name, int(bi), max_bbi+1, '', '', '', '', '', False, '']
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
                # 将节点和层级从列表中删除
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

# 将文本文件转换为树状结构
tree = txt_to_tree('shumu_test.txt')

# 将树状结构保存为 xml 文件
tree_to_xml(tree, 'shumu_test.xml')

# print(df_mulu)
print(df_shuji)
print(df_banben)

# df_shuji.style.set_properties(**{'text-align': 'left'})
# df_banben = df_banben.style.set_properties(**{'text-align': 'left'})

# _xj = (df_banben['bbi'] > 1)
# print(df_banben[_xj])
# print(df_banben[df_banben['版本'] == '大唐西域记'])

# ---------------------

from peewee import SqliteDatabase, Model, CharField, IntegerField, BooleanField, IntegrityError

db = SqliteDatabase(_db_name)

# df_shuji = pd.DataFrame(columns=['书名', 'bi', '作者', '书目路径'])
# df_banben = pd.DataFrame(columns=['版本', 'bi', 'bbi', '修改者', '修改类型', '内容来源', '来源类型', '来源细节', '录入状态', '录入人'])

class ShujiTable(Model):
    id = IntegerField(primary_key=True)
    book_name = CharField()
    bi = IntegerField(unique=True)
    author = CharField()
    biblio_path = CharField()
    class Meta:
        database = db
        
class BanbenTable(Model):
    id = IntegerField(primary_key=True)
    pub = CharField()
    bi = IntegerField(unique=True)
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

db.create_tables([ShujiTable, BanbenTable])

# 将 df_shuji 中的数据写入数据库
for row in df_shuji.itertuples(index=False):
    record = ShujiTable(book_name=row['书名'], bi=row.bi, author=row['作者'], biblio_path=row['书目路径'])
    try:
        record.save(force_insert=True)  # 使用 save() 方法并将 force_insert 参数设置为 True，以便在主键冲突时执行 INSERT OR IGNORE
    except IntegrityError:
        pass

# 将 df_banben 中的数据写入数据库
for row in df_banben.itertuples(index=False):
    record = BanbenTable(
        pub=row['版本'], bi=row.bi, bbi=row.bbi, 
        modifier=row['修改者'], modify_type=row['修改类型'], 
        content_source=row['内容来源'], source_type=row['来源类型'], source_detail=row['来源细节'], 
        record_status=row['录入状态'], recorder=row['录入人']
    )
    try:
        record.save(force_insert=True)  # 使用 save() 方法并将 force_insert 参数设置为 True，以便在主键冲突时执行 INSERT OR IGNORE
    except IntegrityError:
        pass
