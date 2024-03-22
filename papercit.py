import re
import json
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def query_doi_by_title_from_crossref(title:str):

    print('Querying DOI for title:', title)

    # 创建一个Session对象
    session = requests.Session()
    
    # 设置重试机制
    retries = Retry(total=3,  # 设置最大重试次数
                    backoff_factor=0.1,  # 设置重试间隔时间
                    status_forcelist=[500, 502, 503, 504],  # 设置要重试的HTTP状态码
                    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"])  # 设置要重试的HTTP方法
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    base_url = 'https://api.crossref.org/works'
    headers = {'User-Agent': 'PaperCit (846031278@qq.com)'}
    params = {
        'select': 'DOI,title,subtitle',
        'query.title': title
    }

    response = session.get(base_url, headers=headers, params=params)

    # json.dump(response.json(), open('crossref.json', 'w'), indent=2)

    if response.status_code == 200:
        for item in response.json()['message']['items']:

            item_title = str(item['title'][0]) + ('' if item.get('subtitle', None) is None else (' ' + str(item['subtitle'][0]).strip()))

            # 去掉 title 中的标记符，如 <i>...</i>
            title = title.replace('<i>', '').replace('</i>', '').replace(':', '')
            item_title = item_title.replace('<i>', '').replace('</i>', '').replace(':', '')
            
            if item_title.lower() == title.lower():
                print(f'Matched DOI found for title: {item["DOI"]}')
                return item['DOI']
        
        print(f'No matched DOI found for title: {title}\n')
        return None
    else:
        print(f'Failed to query DOI for title: {title}\n')
        return None

def query_bibtex_by_doi_from_crossref(doi:str):
    # 使用 CrossRef 官方的 bibtex API（字段可能不全）
    if not doi:
        return None

    # 将 DOI 转换为 URL 编码
    doi = doi.replace('/', '%2F')
    base_url = f'https://api.crossref.org/works/{doi}/transform?mailto=846031278@qq.com'
    headers = {'User-Agent': 'PaperCit (846031278@qq.com)', 'Accept': 'application/x-bibtex'}
    
    response = requests.get(base_url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return None

def get_field_by_re(bibtex:str, field:str, warn:bool=True):

    matches = re.findall(field + r'={([^}]+)}', bibtex)
    if matches:
        return matches[0]
    else:
        if warn:
            print(f'\t Warning: No matched field found for {field}')
        return None

def bibtex_require_fields(article_type:str):
    if article_type == 'journal':
        return ['title', 'author', 'year', 'journal', 'volume', 'pages', 'publisher', 'doi']
    elif article_type == 'conference':
        return ['title', 'author', 'year', 'booktitle', 'pages', 'publisher', 'doi', 'address']
    else:
        raise ValueError('Unsupported article type')

def parse_bibtex(bibtex:str=None):
    # 解析 bibtex 字符串，提取字段
    if not bibtex:
        return None
    
    print('Parsing bibtex:', bibtex[:20], '...')

    bibtex = bibtex.replace('\n', ' ').replace('\r', ' ').strip()

    # 判断期刊或会议
    if bibtex.startswith('@article'):
        article_type = 'journal'
        prefix = '@article'
        bibname = re.findall(r'@article{([^,]+),', bibtex)[0]
    elif bibtex.startswith('@inproceedings'):
        article_type = 'conference'
        prefix = '@inproceedings'
        bibname = re.findall(r'@inproceedings{([^,]+),', bibtex)[0]
    else:
        raise ValueError('Unsupported article type')

    paper_info = dict()
    paper_info['title'] = get_field_by_re(bibtex, 'title')
    paper_info['author'] = get_field_by_re(bibtex, 'author')
    paper_info['year'] = get_field_by_re(bibtex, 'year')
    paper_info['pages'] = get_field_by_re(bibtex, 'pages')
    paper_info['publisher'] = get_field_by_re(bibtex, 'publisher')
    paper_info['doi'] = get_field_by_re(bibtex, 'DOI')
    if article_type == 'journal':
        paper_info['journal'] = get_field_by_re(bibtex, 'journal', warn = True if article_type == 'journal' else False)
        paper_info['volume'] = get_field_by_re(bibtex, 'volume', warn = True if article_type == 'journal' else False)
    elif article_type == 'conference':
        paper_info['booktitle'] = get_field_by_re(bibtex, 'booktitle', warn = True if article_type == 'conference' else False)

    # 每种文章类型必需的字段
    require_fields = bibtex_require_fields(article_type)

    # 检查是否有缺失字段
    missing_fields = [field for field in require_fields if paper_info.get(field, None) is None]
    if len(missing_fields) > 0:
        print(f'Warning: Some fields are missing: {missing_fields}')
    
    return bibname, article_type, paper_info, missing_fields


def bibtex_format(bibname:str, article_type:str, fmt:str, **kwargs):
    
    if fmt == 'bibtex':

        if article_type == 'journal':
            bibstr = '@article{' + f'{bibname}'
        elif article_type == 'conference':
            bibstr = '@inproceedings{' + f'{bibname}'
        else:
            raise ValueError('Unsupported article type')
        for field in kwargs:
            bibstr += f',\n\t{field}=' + '{' + f'{kwargs[field]}' + '}'
        bibstr += '\n}'
        return bibstr
    
    elif fmt == 'cjc':
        # 期刊论文格式:
        # 作者(外国人姓在前，名在后可缩写, 后同). 题目(英文题目第一字母大写，其它均小写)：副标题(如果有). 刊名(全称), 年, 卷(期): 页码

        # 会议论文集论文格式:
        # 作者. 文章题目(英文题目第1字母大写，其它均小写)：副标题(如果有)//Proceedings of the (会议名称). 会议召开城市, 会议召开城市所在国家, 年: 页码

        bibstr = '\\bibitem[]{}'
        authors = str(kwargs['author']).split('and')
        for i, author in enumerate(authors[:3]):
            names = author.split(',')
            if i != 0:
                bibstr += ', '
            bibstr += names[0].strip() + ' ' + ' '.join([name.strip()[0].upper() for name in names[1:]])

        bibstr += ', et al.' if len(authors) > 3 else '.'
        
        title = str(kwargs['title']).strip().lower()
        title = title[0].upper() + title[1:]
        bibstr += ' ' + title + '.'

        if article_type == 'journal':
            bibstr += f" {kwargs['journal']}, {kwargs['year']}, {kwargs['volume']}: {kwargs['pages']}"
        elif article_type == 'conference':
            bibstr += f"//{kwargs['booktitle']}. {kwargs['address']}, {kwargs['year']}: {kwargs['pages']}"
        else:
            raise ValueError('Unsupported article type')
        
        return bibstr


def query_paper_by_doi_from_crossref(doi:str="10.1109/tifs.2020.2991876", fields:list=[]):
    # 查询论文详细信息
    base_url = f'https://api.crossref.org/works/{doi}'
    headers = {'User-Agent': 'PaperCit (846031278@qq.com)'}

    print(f'Re-querying paper info "{fields}" for DOI: {doi}')

    response = requests.get(base_url, headers=headers)

    data = response.json()
    json.dump(response.json(), open('crossref1.json', 'w'), indent=2)

    doi = doi
    paper_info = dict()
    for field in fields:
        if field == 'title':
            paper_info['title'] = data.get('message', dict()).get('title', [''])[0]
        elif field == 'author':
            paper_info['author'] = data.get('message', dict()).get('author', [])
        elif field == 'year':
            paper_info['year'] = data.get('message', dict()).get('created', dict()).get('date-time', '')
        elif field == 'publisher':
            paper_info['publisher'] = data.get('message', dict()).get('publisher', '')
        elif field == 'address':
            paper_info['address'] = data.get('message', dict()).get('event', dict()).get('location', '')
        elif field == 'pages':
            paper_info['pages'] = data.get('message', dict()).get('page', '')

    return paper_info

if __name__ == '__main__':

    # 示例
    article_list = [
        "A Method of Few-Shot Network Intrusion Detection Based on Meta-Learning Framework",
        "Deep fingerprinting: undermining website fingerprinting defenses with deep learning",
        "Attention is all you need"
    ]

    output_file = 'ref.bib'
    out_fp = open(output_file, 'a')

    for article in article_list:
        doi = query_doi_by_title_from_crossref(article)
        if doi is None:
            continue

        bibtex = query_bibtex_by_doi_from_crossref(doi)

        bibname, article_type, paper_info, missing_fields = parse_bibtex(bibtex)

        if len(missing_fields) > 0:
            missing_fields_value = query_paper_by_doi_from_crossref(doi, fields=missing_fields)
            paper_info.update(missing_fields_value)

        bibstr = bibtex_format(bibname, article_type, 'cjc', **paper_info)

        out_fp.write(bibstr + '\n')

        print('RESULT:', bibstr, '\n')

    out_fp.close()

