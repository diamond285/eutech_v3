import streamlit as st
import psycopg2

st.set_page_config(
    page_title="Статусы загрузок",
    page_icon="📊",
)

st.header("Статусы номенклатур по файлам")

with st.spinner('Waiting'):
    query = '''select t1.file_name, t1.file_upload_date, count_done, count_all
from (select file_name, file_upload_date, count(distinct nomenclature_name) count_done
      from product p
               join file f
                    on f.file_id = p.file_id
               join nomenclature n
                    on n.nomenclature_id = p.nomenclature_id
               join reference_nomenclature rn
                    on rn.reference_nomenclature_properties = n.nomenclature_name
      group by file_name, file_upload_date) t1
         join

     (select file_name, file_upload_date, count(distinct nomenclature_name) count_all
      from product p
               join file f
                    on f.file_id = p.file_id
               join nomenclature n
                    on n.nomenclature_id = p.nomenclature_id
      group by file_name, file_upload_date) t2
     on t1.file_upload_date = t2.file_upload_date and t1.file_name = t2.file_name'''

    conn = psycopg2.connect(dbname='eutech_vi6y',
                            user='root',
                            password='VREpVVk1we7kNlUhgepcyQp5Im5Jtho2',
                            host='dpg-clg3mpur45ec739aghkg-a.frankfurt-postgres.render.com')
    cursor = conn.cursor()
    cursor.execute(query)

    result = cursor.fetchall()
    for name, date, count_done, count_all in result:
        my_bar = st.progress(count_done / count_all, text=f"{name}, [{date}], {count_done}/{count_all}")
