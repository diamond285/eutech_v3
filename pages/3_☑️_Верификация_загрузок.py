import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Верификация загрузок",
    page_icon="☑️",
)


@st.cache_data
def givefirst10(name):
    query = f'''
    select nomenclature_name
    from nomenclature
    where LOWER(nomenclature_name) like '%{name.lower()}%';
        '''

    conn = psycopg2.connect(dbname='eutech_vi6y',
                            user='root',
                            password='VREpVVk1we7kNlUhgepcyQp5Im5Jtho2',
                            host='dpg-clg3mpur45ec739aghkg-a.frankfurt-postgres.render.com')
    cursor = conn.cursor()
    cursor.execute(query)

    records = cursor.fetchall()
    conn.close()
    return [x[0] for x in records]


@st.cache_data
def load_data(name: str):
    # if name in searchings:
    #    return searchings[name]
    import google.generativeai as genai

    API_KEY = 'AIzaSyDN8avHb3uwrEhIOtPj7PhkXlpUNeAdsh8'
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat(history=[])
    q1 = f'все условные обозначения со всеми возможными параметрами по ГОСТ: {name}'
    q2 = 'выведи только примеры'
    q3 = 'СПИСОК параметров'
    q4 = 'выведи гост'
    r1 = chat.send_message(q1)
    r2 = chat.send_message(q2)
    r3 = chat.send_message(q3)
    r4 = chat.send_message(q4)
    # searchings[name] = {'first': r1.text, 'second': r2.text, 'third': r3.text, 'fourth': r4.text}
    return {'first': r1.text, 'second': r2.text, 'third': r3.text, 'fourth': r4.text}


name = st.text_input("Начните вводить")
if name:
    records = st.selectbox("Выберите номенклатуру", givefirst10(name))
else:
    records = ''

if len(records) == 0:
    st.success("Начните вводить")
else:
    st.header(records)

    # records = st.text_input("Введите номенклатуру")

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
    dupls = []
    st.write('Выберите эталонные номенклатуры:')
    for x in s.split('\n'):
        if ' - ' in x:
            x = x.split(' - ')[0]
        if x not in dupls:
            examples.append(st.checkbox(x.replace('* ', '').replace('**', '')))
            dupls.append(x)
    nomen_input = st.text_input("Другое")

    fulltext = '\n\n'.join([d[x] for x in d])
    # st.write(fulltext)
    st.write(d['third'])
    params = []
    then = ''
    for x in d['third'].split('\n\n')[1].split('\n'):
        if '    *' in x:
            val = x.replace('    * ', '')
            params[-1][1].append(val)
        elif '*' in x:
            val = x.replace('**', '').replace('* ', '')
            if val not in params:
                params.append([val, []])

    take_param = []
    st.write('Выберите параметры номенклатуры:')
    for val in params:
        if len(val[1]) > 1:
            take_param.append(st.selectbox(val[0], ['-'] + val[1]))
        else:
            take_param.append(st.text_input(val[0]))

    gost = ''
    if len(fulltext.split('ГОСТ')) != 1:
        gost = 'ГОСТ ' + fulltext.split('ГОСТ')[1].lstrip().split(' ')[0].split('*')[0].replace(',', '')
    t_val = st.text_input('Введите ГОСТ', value=gost)

    generate_item = st.button("Создать номенклатуру")
    if generate_item:
        jj = {}
        for x, y in zip(params, take_param):
            if y in ['', '-']:
                continue
            jj[x[0]] = y
        st.write(jj)
        import requests

        r = requests.get(f'http://127.0.0.1:8000/create/', json={'name': records, 'values': jj})
        st.write(r.text)

    submit = st.button("Сохранить")

    conn = psycopg2.connect(dbname='eutech_vi6y',
                            user='root',
                            password='VREpVVk1we7kNlUhgepcyQp5Im5Jtho2',
                            host='dpg-clg3mpur45ec739aghkg-a.frankfurt-postgres.render.com')
    if submit:
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

    if nomen_input:
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
