# encoding:utf-8
# @date:
# @author: vicky
# @environment:
# @brief: 文本抽取1.1 基本版本仍然采用结巴, 后去考虑上bert模型
import jieba, jieba.analyse
import os,  pathlib, re
import pymongo
import pymysql
root_path = pathlib.Path(os.path.abspath(__file__)).parent
from config import Config

config = Config()


class TxtExtract():
    '''txt extraction'''

    @staticmethod
    def stop_words(internet_stop):
        # 停用此表放在测试简历地址
        with open(internet_stop, encoding="UTF-8") as file:
            return [w.strip() for w in file]

    @staticmethod
    def get_work_exp(resume):
        # 基本情况中没有找到工作经验时间，在简历工作经历中获取
        try:
            info1 = re.sub(r'\s+', '', resume)
        except TypeError:
            info1 = resume
        work_list = ['工作经历', '工作资历', '职业履历', '任职经历', '职业经历', '事業内容']
        study_list = ['教育背景', '教育经历', '資格', '教育经验', '培训经历']
        base_str, work_str, final_work_str, aaa3 = 0, 0, 0, 0
        for i in work_list:
            if i in info1:
                work_str = info1.split(i)[1]  # 找到工作经历字段其后字符串
                base_str = info1.split(i)[0]  # 字段前部分字符串(基本信息)
                break
        # print(aaa0,aaa1)
        # 各简历标定工作经历的方式差异较大，为了提升准确度，此处需要进行准确的切割
        if work_str == 0 and '工作经验' in info1 and '年工作经验' not in info1:
            gzjy_list = info1.split('工作经验')  # 从工作经验位置分开
            work_str = gzjy_list[1]  # 工作经验之后
            base_str = gzjy_list[0]  # 工作经验之前
            if len(gzjy_list) >= 3:  # 如果gzjy_list是长度>3的列表
                base_str = base_str + work_str
                work_str = gzjy_list[2]
        elif work_str == 0 and '年工作经验' in info1:
            base_str = info1.split('年工作经验')[0]
            aaa3 = info1.split('年工作经验')[1]
            if '工作经验' in aaa3:
                base_str = base_str + aaa3.split('工作经验')[0]
                work_str = aaa3.split('工作经验')[1]
            else:
                work_str = aaa3
        if work_str != 0 and base_str != 0 and re.search(r'[^：a-zA-Z]20[0,1][\d]', base_str) and not re.search(
                r'[^：a-zA-Z]20[0,1][\d]', work_str):
            # work_str = base_str#work_list前后字段都不为0 且在base_str基本信息中切出时间段而在work_str工作经历中切不出时间段，就把时间段的赋值给aaa1
            # 20200423moidfy对于工作经历以形式2016年至今这种形式需要考虑
            if '至今' not in work_str:  # 有至今不好确定工作经验需要借助教育经历切
                work_str = base_str

        if work_str == 0:  # 工作经验之后没有时间段
            return '应届'
        for j in study_list:
            if j in work_str:
                final_work_str = work_str.split(j)[0]  # 如果有study_list中的词就切出教育背景之前的时间段
                break
            else:
                pass
            final_work_str = work_str
            # final_work_str = re.sub(r'\d+', '', work_str)
        return base_str, final_work_str  # base_str是基本信息文本，final_work_str是工作经历段文本(如果有教育背景教育背景时间段去掉)

    @staticmethod
    def tech2list(tech_words):

        double_word_dict = {
            'spring boot': 'springboot',
            'spring mvc': 'springmvc',
            'spring cloud': 'springcloud',
            'sql server': 'sqlserver',
            'java script': 'javascript',
            'visual studio': 'visualstudio',
            'entity framework': 'entityframework'
        }
        if tech_words:
            tech_str_list = tech_words.lower()
            # 统一 成英文逗号
            tech_str_list = re.sub(r'\d+$', '', tech_str_list)#匹配结尾
            tech_str_list = re.sub(r'，', ',', tech_str_list)# 替换英文逗号
            tech_str_list = tech_str_list.replace('+', ',') # +替换成逗号
            tech_str_list = tech_str_list.split(',')  # 根据逗号切分词
            for i in double_word_dict.keys():
                if i in tech_str_list:
                    tech_str_list[tech_str_list.index(i)] = double_word_dict[i]
        else:
            tech_str_list = []
        return tech_str_list

    @staticmethod
    def jd_english_techwords(job_req):
        '''
        解析新格式的JD，直接输出各级别关键词列表
        '''

        master_list = TxtExtract.tech2list(job_req['job_master'])
        skilled_list = TxtExtract.tech2list(job_req['job_skilled'])
        necessary_list = TxtExtract.tech2list(job_req['job_necessary'])

        return master_list, skilled_list, necessary_list

    @staticmethod
    def req_deal(job_req):
        '''jd岗位职责+任职要求文本预处理'''
        '''split the words in new cv'''
        if not job_req['job_threshold']:
            job_req['job_threshold'] = ''

        # work_original 岗位职责
        if not job_req['job_original']:
            job_req['job_original'] = ''

        req = job_req['job_threshold'] + job_req['job_original']

        comp = re.compile('[^A-Z^a-z^0-9^\u4e00-\u9fa5]')
        req_content = re.sub(r'\d+', '', comp.sub('', req))

        # if len(req_content)
        jd_key_cut = TxtExtract.get_key_words(req_content, config.tech_word)
        master_k, skilled_k, necessary_k = TxtExtract.jd_english_techwords(job_req)

        high_weight_words = master_k + skilled_k + necessary_k

        jd_key_cut_update = set(high_weight_words).union(set(jd_key_cut))  # union 只能是两个集合去重
        req_content = "".join(jd_key_cut_update)
        if len(req_content) <= 20:
            return -1
        return req_content

    @staticmethod
    def resume_deal(resume):
        '''工作经历段文本预处理'''
        # keep English, digital and Chinese
        base_info, work_exp = TxtExtract.get_work_exp(resume)
        work_exp = re.sub(r'\d+', '', work_exp)
        if len(work_exp) <= 1:
            work_exp = resume
            work_exp = re.sub(r'\d+', '', work_exp)  # 数去掉数
        comp = re.compile('[^A-Z^a-z^0-9^\u4e00-\u9fa5]')# 去除标点空格等
        work_exp = comp.sub('', work_exp).lower()
        # print(work_exp)
        final_work_exp = TxtExtract.get_key_words(work_exp, config.tech_word)
        final_work_exp = "".join(final_work_exp)
        if len(final_work_exp) <= 20:
            return -1
        return final_work_exp

    @staticmethod
    def get_key_words(word_str, tech_path, num=100):
        '''
        :param word_str: 要提取关键词的文本
        :param num: 提取多少关键词
        :return: topk个词组成的短文本
        '''
        # 从词典里提取技术名词
        tech_word_list = []
        with open(tech_path, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                tech_word_list.append(i.strip())
                jieba.add_word(i.strip())# 向结巴的词典里边添加技术词汇

        #
        word_dict = {}
        # 使用自定义停用词集合
        jieba.analyse.set_stop_words(config.vocal_txt)

        for x, w in jieba.analyse.extract_tags(word_str.lower(), withWeight=True, topK=num):
            word_dict[x] = round(w, 2)
        split_w = list(word_dict.keys())
        return split_w
        # print(split_w)
        # return "".join(split_w)

    @staticmethod
    def save_csv(save_path, content):
        """
        文件内容保存到制定路径
        :param save_path:
        :param content:
        :return:
        """
        with open(save_path, 'a+', encoding='UTF-8') as fw:  # 写入文件
            fw.write(content + '\n')

def get_jd(job_id):
    #连接数据库
    params_list = {
              'host': '192.168.122.186',
              'port': 3306,#MySQL默认端口
              'user': '',#mysql默认用户名
              'password': '',
              'db': '',#数据库
              'charset': 'utf8',
              'cursorclass': pymysql.cursors.DictCursor,
             }

    conn = pymysql.connect(**params_list)
    cursor = conn.cursor()  # 创建游标
    job_id = int(job_id)
    cursor.execute("select * from job_manager where job_id = {}".format(job_id))  # 20200401modify
    # fetchall()获取查询结果
    jd_result = cursor.fetchall()  # 数据库中得到列表类型

    if jd_result:
        job_req = jd_result[0]
        # print(job_req)
    else:
        job_req = 'empty'
    conn.close()
    return job_req


def get_resume(cv_title):
    client = pymongo.MongoClient('')

    find_style = {'title': cv_title}
    # 测试时把登录信息注了
    client.test.authenticate("", "", mechanism='SCRAM-SHA-1')

    cur_resume = ''
    for x in client['test']['test4'].find(find_style):
        # print(x['info'])
        cur_resume = x['info']
    return cur_resume


def main(job_req, resume):
    """
    jd ,resume 抽取及保存为csv文件
    :param resume: 简历内容,mongo 库中"info":对应内容
    :param job_req:  字典形式
    :return: 本文件夹目录下 数据保存为名称为data的csv文件
    """
    #1. jd content

    jd_words, cv_words = TxtExtract.req_deal(job_req), TxtExtract.resume_deal(resume)
    cur_save_path = os.path.join(root_path, "data" + '.csv')
    try:
        content = ','.join(("0", jd_words, cv_words))
    except Exception:
        print("jd content is too short for algorithm!!!")
        # print(e)
    else:
        """label初始化默认全部先给0,后期根据实际修改1"""
        TxtExtract.save_csv(cur_save_path, content)


if __name__ == "__main__":
    # 1.test
    jd_req = get_jd('')# 输入"job_id"
    resume_content = get_resume('*.docx')# 简历名称
    # print(jd_req)
    # print(resume_content)
    # 2.function
    main(jd_req, resume_content)

