import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Ручной поиск",
    page_icon="🔎",
)


@st.cache_data
def load_data(name):
    if not name:
        return None
    import requests
    import json
    r = requests.get(f'http://127.0.0.1:8000/find/{name}')
    d = json.loads(r.text)
    return d


records = st.text_input("Введите номенклатуру")

if len(records) == 0:
    st.success("Начните вводить")
else:
    st.header(records)

    #

    if st.button("Regenerate"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.experimental_rerun()

    d = load_data(records)
    if not d:
        st.stop()
    nomen = d['first']
    jns = d['second']
    # st.write(nomen)
    st.write(d['first'])
    s = jns.split('\n\n')
    b = True
    for x in s:
        if '* **' in x:
            s = x
            b = False
            break
    if b:
        st.cache_data.clear()
        st.cache_resource.clear()
        st.experimental_rerun()

    examples = []
    st.write('Выберите эталонные номенклатуры:')
    for x in s.split('\n'):
        if ' - ' in x:
            x = x.split(' - ')[0]
        examples.append(st.checkbox(x.replace('* ', '').replace('**', '')))
    nomen_input = st.text_input("Другое")

    fulltext = '\n\n'.join([d[x] for x in d])
    # st.write(fulltext)
    st.write(d['third'])
    params = []
    then = ''
    for x in d['third'].split('\n'):
        if '    *' in x:
            val = x.replace('\t*', '')
            params[-1][1].append(val)
        elif '* **' in x:
            val = x.replace('**', '').replace('* ', '')
            if val not in params:
                params.append([val, []])

    take_param = []

    st.write('Выберите параметры номенклатуры:')
    for val in params:
        # take_param.append(st.checkbox(val[0]))
        if len(val[1]) > 1:
            st.selectbox(val[0], ['-'] + val[1])
        else:
            st.text_input(val[0])

    gost = ''
    if len(fulltext.split('ГОСТ')) != 1:
        gost = 'ГОСТ ' + fulltext.split('ГОСТ')[1].lstrip().split(' ')[0].split('*')[0].replace(',', '')
    t_val = st.text_input('Введите ГОСТ', value=gost)

    generate_item = st.button("Создать номенклатуру")
    if generate_item:
        st.write(take_param)
        import requests
        import json

        r = requests.get(f'http://127.0.0.1:8000/create/', json=jj)
        d = json.loads(r.text)

    submit = st.button("Сохранить")
    if submit:

        conn = psycopg2.connect(dbname='eutech_vi6y',
                                user='root',
                                password='VREpVVk1we7kNlUhgepcyQp5Im5Jtho2',
                                host='dpg-clg3mpur45ec739aghkg-a.frankfurt-postgres.render.com')
        cursor = conn.cursor()
        for i, x in enumerate(examples):
            if x:
                val_name = s.split('\n')[i].replace('* ', '').replace('**', '')
                if '- ' in val_name:
                    val_name = val_name.split('- ')[0]
                st.write(val_name)
                query = f'''insert into reference_nomenclature (reference_nomenclature_name, reference_nomenclature_properties) values ('{val_name}', '{records[0]}')'''
                cursor.execute(query)

                query = f'''update nomenclature
        set reference_nomenclature_id = (select reference_nomenclature_id
                                         from reference_nomenclature
                                         where reference_nomenclature_name = '{val_name}')
        where nomenclature_name = '{records[0]}' '''
                cursor.execute(query)
        conn.close()

    if nomen_input:
        conn = psycopg2.connect(dbname='eutech_vi6y',
                                user='root',
                                password='VREpVVk1we7kNlUhgepcyQp5Im5Jtho2',
                                host='dpg-clg3mpur45ec739aghkg-a.frankfurt-postgres.render.com')
        cursor = conn.cursor()
        st.write(nomen_input)
        query = f'''insert into reference_nomenclature (reference_nomenclature_name, reference_nomenclature_properties) values ('{nomen_input}', '{records[0]}')'''
        cursor.execute(query)

        query = f'''update nomenclature
        set reference_nomenclature_id = (select reference_nomenclature_id
                                         from reference_nomenclature
                                         where reference_nomenclature_name = '{nomen_input}')
        where nomenclature_name = '{records[0]}' '''
        cursor.execute(query)

        conn.commit()
        conn.close()
        st.success('Эталонная номенклатура была создана и добавлена в базу данных!', icon="✅")
        st.experimental_rerun()
