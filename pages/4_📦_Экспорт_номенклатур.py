import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Экспорт номенклатур",
    page_icon="📦️",
)


@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


conn = psycopg2.connect(dbname='eutech_vi6y',
                        user='root',
                        password='VREpVVk1we7kNlUhgepcyQp5Im5Jtho2',
                        host='dpg-clg3mpur45ec739aghkg-a.frankfurt-postgres.render.com')
cursor = conn.cursor()
cursor.execute('select * from reference_nomenclature')

result = cursor.fetchall()
df = pd.DataFrame(result)
df.columns = ['ID', 'Эталонная номенклатура', "Название номенклатуры"]
st.write(df)
csv = convert_df(df)

st.download_button(
    "Press to Download",
    csv,
    "file.csv",
    mime='text/csv'
)
