import streamlit as st
import pandas as pd
import datetime as dt
import pandas as pd
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb


st.set_page_config(layout="wide")

dataHoje = dt.date.today().strftime('%Y%m%d')

def process_txt(uploaded_file):
    
    # Lendo o conteúdo do arquivo de texto
    txt_contents = uploaded_file.getvalue().decode("utf-8")

    # Dividindo o conteúdo do arquivo em linhas
    lines = txt_contents.split("\n")

    # Criando um DataFrame a partir das linhas do arquivo
    df_txt = pd.DataFrame(lines, columns=["Texto"])
    
    # selecionando apenas os ativos
    lista_ativos = df_txt[df_txt['Texto'].str.startswith(('CRI', 'CRA', 'DEB', 'CDB', 'LCI', 'LCA'))]

     # selecionando as linhas, transformando em coluna e empilhando ------

    # df que vai receber a informação
    df_Bruto = pd.DataFrame()

    for ativo in range(len(lista_ativos)-1):

    # seleciona as linhas o ativo atual e o proxímo, reseta o índice e transforma linha em coluna
        df_temp = df_txt.loc[lista_ativos.index[ativo]:lista_ativos.index[ativo+1]-1].reset_index(drop=True).transpose()

    # concatena as informações anteriores com a nova
        df_Bruto = pd.concat([df_Bruto, df_temp], sort=False)

    # selecionando as linhas com dados importantes, como a tabela tem tamnho de informações iguais, preciso selecionar elas

    # backup
    df = df_Bruto

    # substituindo o NaN por _
    df.fillna('_', inplace=True)

    # qual é a quantidade de informações por linhas que não são _
    df['Qtd colunas'] = df.shape[1]

    df['Qtd _'] = df.apply(lambda x: x.str.count('_'), axis=1).sum(axis=1)

    df['Qtd info'] = df['Qtd colunas'] - df['Qtd _']

    # pegando a quantidade de informação que mais se repete, já que a tabela é a que tem mais linhas
    df = df[df['Qtd info'] == df['Qtd info'].value_counts().index[0]]

    # organizando a tabela

    # resetando o indice
    df = df.reset_index(drop=True)

    # selecionando as colunas importantes
    df = df.iloc[:, :int(df['Qtd info'].value_counts().index[0])]

    # classificando o IR de acordo com o nome

    df['IR'] = df.iloc[:, 0].apply(lambda x: 'Isento' if x.startswith(('LCI', 'LCA', 'CRI', 'CRA')) else '')

    return df

# Função para verificar se os três arquivos foram enviados
def verificar_arquivos_enviados(uploaded_file1, uploaded_file2, uploaded_file3):
    if uploaded_file1 is None or uploaded_file2 is None or uploaded_file3 is None:
        return False
    else:
        return True

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def main():
    
    st.title("Planilha de Renda Fixa")
    
    st.subheader("Instruções")
    st.text('1. Copie as informações do site na visão do assessor')
    st.text('2. As colunas devem estar nesse formato:')
    st.image('colunas.png')
    st.text('Se houver outras colunas, clique em "Personalizar Colunas" no HUB para removê-las')
    st.text('3. No HUB, copie os dados e cole-os em um arquivo .txt separado para cada tipo de investimento')
    st.text('Exemplo: bancarios.txt, privados.txt e debenturesIsentas.txt')
    st.text('4. Importe cada arquivo para a sua área correspondente em "1. Dados em .txt"')
    st.text('5. Confira se está tudo ok em "2. Planilha"')
    st.text('6. Exporte clicando no botão de donwload em "3.Download"')
    
    
    st.subheader("1. Dados em .txt")
    # Componente para upload de arquivo
    uploaded_file1 = st.file_uploader("1.1 Crédito Bancário", type="txt")
    uploaded_file2 = st.file_uploader("1.2 Crédito Privado", type="txt")
    uploaded_file3 = st.file_uploader("1.3 Debêntures Incentivadas", type="txt")

    if verificar_arquivos_enviados(uploaded_file1, uploaded_file2, uploaded_file3):
        st.success("Todos os arquivos foram enviados com sucesso!")
        
        # Processamento do arquivo e conversão para DataFrame
        if uploaded_file1 is not None:
        # bancario    
            df1 = process_txt(uploaded_file1)
            df1.drop([1], axis=1, inplace=True)
            df1.columns = ['Ativo', 'Vencimento', 'Carência', 'TaxaMin', 'TaxaMax', 'PU', 'Qtd Min', 'Qtd Disp', 'Rating', 'ROA', 'Risco XP', 'IR']
        
        if uploaded_file2 is not None:
            # privado incompleto
            df2 = process_txt(uploaded_file2)
            df2.drop([1], axis=1, inplace=True)
            df2.columns = ['Ativo', 'Vencimento', 'Carência', 'TaxaMin', 'TaxaMax', 'PU', 'Qtd Min', 'Qtd Disp', 'Rating', 'ROA', 'Risco XP', 'IR']
        
        if uploaded_file3 is not None:
        # debentures
            df3 = process_txt(uploaded_file3)
            df3.drop([1], axis=1, inplace=True)
            df3.columns = ['Ativo', 'Vencimento', 'Carência', 'TaxaMin', 'TaxaMax', 'PU', 'Qtd Min', 'Qtd Disp', 'Rating', 'ROA', 'Risco XP', 'IR']
            df3['IR'] = 'Isento'
            
        # privado completo
        df4 = pd.concat([df3, df2], axis=0)
        df4 = df4.drop_duplicates(['Ativo', 'Vencimento', 'Carência', 'TaxaMin', 'TaxaMax'],keep='first')

        # RF
        rf = pd.concat([df1, df4], axis=0) 
        
        # Exibindo o DataFrame
        st.subheader("2. Planilha")
        st.dataframe(rf)
        
        # Botão de download
        st.subheader("3. Download")
        df_xlsx = to_excel(rf)
        st.download_button(label='📥 Clique aqui para fazer o download 📥',
                                data=df_xlsx ,
                                file_name= f'RF {dataHoje}.xlsx')
        

    else:
    # Mensagem para o usuário enviar os arquivos restantes
        st.warning("Por favor, envie os três arquivos.")


if __name__ == "__main__":
    main()
