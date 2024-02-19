import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Загрузка данных",
    page_icon="📥",
)


@st.cache_data
def load_data(url):
    if uploadedFile.name.endswith('.xlsx'):
        df = pd.read_excel(uploadedFile)
    else:
        df = pd.read_csv(uploadedFile)
    return df


uploadedFile = st.file_uploader("Загрузите файл csv или xlsx формата",
                                type=['csv', 'xlsx'],
                                accept_multiple_files=False,
                                key="fileUploader")

if uploadedFile:
    st.write(uploadedFile)
    df = load_data(uploadedFile)
    info = dict()
    info['name'] = st.selectbox("Выберите колонку с названиями номенклатур: ", df.columns)
    info['unit'] = st.selectbox("Выберите колонку с единицами измерений: ", df.columns)
    info['cost'] = st.selectbox("Выберите колонку с ценами номенклатур: ", df.columns)
    info['from'] = st.selectbox("Выберите колонку с названиями поставщиков: ", df.columns)
    submit = st.button("Выбрать")
    if submit:
        st.table(df[[info[x] for x in info]].head(5))
    load = st.button("Начать загрузку")
    if load:
        from datetime import datetime

        load_progress = st.progress(0, 'Загрузка данных в базу')
        conn = psycopg2.connect(dbname='eutech_vi6y',
                                user='root',
                                password='VREpVVk1we7kNlUhgepcyQp5Im5Jtho2',
                                host='dpg-clg3mpur45ec739aghkg-a.frankfurt-postgres.render.com')
        df = df[[info[x] for x in info]]
        df[info['from']] = df[info['from']].str.replace('\"', '\"\"').str.replace('\'', '\'\'')
        df[info['name']] = df[info['name']].str.replace('\"', '\"\"').str.replace('\'', '\'\'')
        df[info['unit']] = df[info['unit']].str.replace('\"', '\"\"').str.replace('\'', '\'\'')
        cur = conn.cursor()
        cur.execute(
            f"insert into file (file_name, file_upload_date) values('{uploadedFile.name}', '{str(datetime.now())}')")
        length_of_df = len(set(df[info['from']]))
        s = 'insert into provider (provider_name) values'
        for i, x in enumerate(set(df[info['from']])):
            s += f"('{x}'),"
            if i % 100 == 0 and i != 0:
                cur.execute(s[:-1])
                s = 'insert into provider (provider_name) values'
                conn.commit()
            load_progress.progress((i + 1) / length_of_df,
                                   f'Загрузка поставщиков в базу {i + 1}/{length_of_df}')  # : {x[0]} ({x[3]})
        cur.execute(s[:-1])
        conn.commit()
        s = 'insert into nomenclature (nomenclature_name, nomenclature_properties) values'
        length_of_df = len(set(df[info['name']]))
        for i, x in enumerate(set(df[info['name']])):
            s += f"('{x}',''),"
            if i % 100 == 0 and i != 0:
                cur.execute(s[:-1])
                s = 'insert into nomenclature (nomenclature_name, nomenclature_properties) values'
                conn.commit()
            load_progress.progress((i + 1) / length_of_df,
                                   f'Загрузка номенклатур в базу {i + 1}/{length_of_df}')  # : {x[0]} ({x[3]})
        cur.execute(s[:-1])
        conn.commit()
        length_of_df = len(df)
        s = '''insert into product (nomenclature_id, provider_id, product_cost, product_unit, file_id) values '''
        for i, x in enumerate(df.iloc):
            s += f'''((select nomenclature_id from nomenclature where nomenclature_name = '{x[0]}' ORDER BY nomenclature_id DESC limit 1),
                      (select provider_id from provider where provider_name = '{x[3]}' ORDER BY provider_id DESC limit 1),
                      {x[2]},
                      '{x[1]}',
                      (select file_id from file where file_name = '{uploadedFile.name}' ORDER BY file_id DESC limit 1)),'''
            if i % 100 == 0 and i != 0:
                cur.execute(s[:-1])
                s = '''insert into product (nomenclature_id, provider_id, product_cost, product_unit, file_id) values '''
                conn.commit()
            progress = i / length_of_df
            load_progress.progress(1 if progress > 1 else progress,
                                   f'Загрузка основных данных в базу {i + 1}/{length_of_df}')  # : {x[0]} ({x[3]})
        cur.execute(s[:-1])
        conn.commit()
        conn.close()
        st.success(
            "Все данные были загружены. Все номенклатуры должны пройти верификацию через ChatGPT статус которого вы можете проверить во вкладке Статусы загрузок, после чего вам обязательно нужно верифицировать все номенклатуры самостоятельно")
else:
    st.write("Примечание: файл загруженный в формате csv должна быть в кодировке utf-8")
