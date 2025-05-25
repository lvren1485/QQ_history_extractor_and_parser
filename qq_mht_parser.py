import re
from bs4 import BeautifulSoup
import sys

def parse_mht_file(input_path, output_path):
    # 读取整个文件内容
    with open(input_path, 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
    
    # 建立GUID到扩展名的映射表
    image_ext_map = {}
    
    # 新的精确匹配方法
    image_sections = re.split(r'------=_NextPart_\w+', content)
    
    for section in image_sections:
        if 'Content-Type:image/' in section:
            # 提取扩展名
            ext_match = re.search(r'Content-Type:image/(\w+)', section)
            ext = ext_match.group(1).lower() if ext_match else 'dat'
            
            # 提取GUID
            guid_match = re.search(r'Content-Location:\s*({[^}]+}\.dat)', section)
            if guid_match:
                guid = guid_match.group(1)
                clean_guid = guid.replace('{', '').replace('}.dat', '')
                image_ext_map[guid] = (clean_guid, ext)
                print(f"DEBUG: 映射建立 {guid} → {clean_guid}.{ext}")

    print(f"DEBUG: 共找到 {len(image_ext_map)} 个图片映射")
    
    # 解析HTML消息部分
    html_start = content.find('<html')
    if html_start == -1:
        print("未找到HTML内容")
        return

    html_content = content[html_start:]
    soup = BeautifulSoup(html_content, 'html.parser')

    with open(output_path, 'w', encoding='utf-8') as out_file:
        message_rows = soup.find_all('tr')
        
        for row in message_rows:
            # 提取发送者信息
            sender_div = row.find('div', style=re.compile(r'color:#006EFE;padding-left:10px;'))
            if not sender_div:
                continue
            
            sender_info = sender_div.find('div', style=re.compile(r'float:left;margin-right:6px;'))
            sender = sender_info.get_text(strip=True) if sender_info else "未知发送者"
            
            # 提取消息内容
            content_div = row.find('div', style='padding-left:20px;')
            if not content_div:
                continue
            
            # 提取文字消息
            text_content = []
            for font in content_div.find_all('font'):
                text_content.append(font.get_text(strip=True))
            text_content = ' '.join(text_content).strip()
            
            # 处理图片
            images = []
            for img in content_div.find_all('img'):
                src = img.get('src', '')
                if src:
                    # 查找并替换扩展名
                    if src in image_ext_map:
                        clean_guid, ext = image_ext_map[src]
                        src = f"{clean_guid}.{ext}"
                    else:
                        # 如果没有匹配到，至少去掉大括号
                        src = src.replace('{', '').replace('}', '')
                    images.append(src)
            
            # 构建输出行
            output = f"[{len(images)}][{sender}][{text_content}]"
            for img in images:
                output += f"[{img}]"
            output += "\n"
            
            out_file.write(output)
            print(output.strip())

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("使用方法: python qq_mht_parser.py 输入文件.mht 输出文件.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    parse_mht_file(input_file, output_file)
    print(f"\n解析完成！结果已保存到 {output_file}")