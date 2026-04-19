import pandas as pd

def generate_text_file(csv_file="dataS3.csv", output_txt_file="bert_input.txt"):
    
    df = pd.read_csv(csv_file)
    element_cols = [
        'Ti (wt%)', 'Fe (wt%)', 'Zr (wt%)', 'Nb (wt%)', 'Sn (wt%)', 'Ta (wt%)', 
        'Mo (wt%)', 'Al (wt%)', 'V (wt%)', 'Cr (wt%)', 'Hf (wt%)', 'Mn (wt%)', 
        'W (wt%)', 'Si (wt%)', 'Cu (wt%)'
    ]

    def create_text_input(row):
        """
        将一行数据转换为一个描述性文本。
        """
        # 只包括含量 > 0 的元素
        composition_parts = []
        for col in element_cols:
            if row[col] > 0:
                element_name = col.replace(' (wt%)', '')
                composition_parts.append(f"{element_name} {row[col]}%")
        
        composition_str = ", ".join(composition_parts)
        
        # 文本
        text = (
            f"Titanium alloy composition: {composition_str}. "
            f"Condition: {row['condition']}"
        )
        return text

    df['text_input'] = df.apply(create_text_input, axis=1)
    text_lines = df['text_input'].tolist()

    # 将文本写入 .txt 文件
    try:
        with open(output_txt_file, 'w', encoding='utf-8') as f:
            for line in text_lines:
                f.write(line + '\n') # 每行文本占一行，并换行
    except IOError as e:
        print(f"写入文件时出错: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    generate_text_file(csv_file="dataS3.csv", output_txt_file="bert_input.txt")