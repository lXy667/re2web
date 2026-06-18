import fitz

def extract_text(pdf_path):

    text = ""

    pdf = fitz.open(pdf_path)   # 打开这个pdf

    for page in pdf:            # 遍历每一页
        text += page.get_text() # 获取每一页的文本内容，并将其添加到text变量中

    pdf.close()

    return text