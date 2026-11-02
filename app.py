import io, json, uuid
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from engine import compute
from example import blank, example
from store import save, load, all_models

st.set_page_config(page_title='Extolla | Cost-to-Serve', page_icon='📊', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''<style>
#MainMenu,header[data-testid="stHeader"]{visibility:hidden}section[data-testid="stSidebar"]{display:none}
.block-container{padding-top:0.65rem;max-width:1550px}h1,h2,h3{color:#315445}
.extolla-bar{background:linear-gradient(90deg,#204d38 0%,#376744 74%,#d68c3c 74%,#d68c3c 100%);height:14px;margin:0 -3rem 1.1rem -3rem;border-radius:0 0 4px 4px}
div[data-testid="stMetric"]{background:#f5f8f6;border:1px solid #d8e5dd;border-radius:11px;padding:12px}
div.stButton>button[kind="primary"]{background:#c77c35;border-color:#c77c35;color:white}
[data-testid="stDataFrame"]{border-radius:10px;overflow:hidden;border:1px solid #dfe8e2}
div[data-testid="stHorizontalBlock"]{align-items:start}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="extolla-bar"></div>',unsafe_allow_html=True)
if 'model' not in st.session_state:
    st.session_state.model=blank();st.session_state.model_id=None
m=st.session_state.model
logo=Path(__file__).resolve().parent/'assets'/'extolla_logo.png'
brand, heading=st.columns([1,5],vertical_alignment='center')
with brand:
    if logo.exists():st.image(str(logo),width='stretch')
    else:st.markdown('### EXTOLLA')
with heading:
    st.title('Cost-to-Serve & Profitability')
    st.caption(f"{m['name']} · Annualised financial view · AUD")

PAGES=['Dashboard','Business Inputs','P&L Allocation','Service Rate Card','Customers','Customer Volumes','Customer Rates','Cost-to-Serve','Rate Card Analysis','New Customer Modelling','Scenarios','Reports & Exports']
page=st.radio('Navigate',PAGES,horizontal=True,label_visibility='collapsed',key='top_page')
with st.expander('My models · New / Load / Save / Import / Export', expanded=False):
    a,b,c,d=st.columns(4)
    with a:
        if st.button('New blank model',width='stretch'):
            st.session_state.model=blank();st.session_state.model_id=None;st.rerun()
        if st.button('Load fictional example',width='stretch'):
            st.session_state.model=example();st.session_state.model_id=None;st.rerun()
    with b:
        m['name']=st.text_input('Model name',value=m['name'])
        if st.button('Save model',type='primary',width='stretch'):
            st.session_state.model_id=save(m,st.session_state.model_id);st.success('Saved')
        if st.button('Save as new copy',width='stretch'):
            st.session_state.model_id=save(m);st.success('Copy saved')
    with c:
        models=all_models(); options={f"{x['name']} · {x['id'][:8]}":x['id'] for x in models}
        picked=st.selectbox('Saved models',['Select a model']+list(options))
        if st.button('Open selected model',width='stretch') and picked in options:
            st.session_state.model=load(options[picked]);st.session_state.model_id=options[picked];st.rerun()
    with d:
        incoming=st.file_uploader('Import model JSON',type='json')
        if incoming and st.button('Import JSON'):
            st.session_state.model=json.load(incoming);st.session_state.model_id=None;st.rerun()
        st.download_button('Export model JSON',json.dumps(m,indent=2),file_name='extolla_model.json',mime='application/json',width='stretch')

MONEY={'Revenue','Cost','Profit','Gross profit','Cost-to-serve','Storage cost','Activity cost','Overhead cost','Pass-through cost','Unit cost','Customer rate','Weighted rate','Target rate','Calculated rate','standard_rate','cost','amount','material','Cost per unit','Rate gap','Recommended rate'}
PERCENT={'Gross margin','Margin','markup'}
def money(v):return f'${float(v):,.2f}'
def view(df, money_cols=None, percent_cols=None, id_end=True):
    if df is None or df.empty:
        st.info('No rows available yet.');return
    df=df.copy()
    if id_end:
        ids=[x for x in ['Customer ID','id'] if x in df.columns]
        df=df[[x for x in df.columns if x not in ids]+ids]
    money_cols=set(money_cols or []).union(MONEY)
    percent_cols=set(percent_cols or []).union(PERCENT)
    styles={}
    for col in df.columns:
        if col in money_cols and pd.api.types.is_numeric_dtype(df[col]):styles[col]='${:,.2f}'
        elif col in percent_cols and pd.api.types.is_numeric_dtype(df[col]):styles[col]='{:.2%}'
        elif pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col]):styles[col]='{:,.2f}'
    sty=df.style.format(styles,na_rep='—').set_properties(**{'text-align':'center'}).set_table_styles([{'selector':'th','props':[('text-align','center'),('background-color','#eaf1ec'),('color','#244b37'),('font-weight','bold')]}])
    st.dataframe(sty,width='stretch',hide_index=True)

def editor(df,key,disabled=None,money_cols=None,percent_cols=None,num_rows='dynamic'):
    cols={}
    for col in df.columns:
        if col in (money_cols or []):cols[col]=st.column_config.NumberColumn(col,format='$%.2f')
        elif col in (percent_cols or []):cols[col]=st.column_config.NumberColumn(col,format='%.2f')
        elif pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col]):cols[col]=st.column_config.NumberColumn(col,format='%.2f')
    return st.data_editor(df,width='stretch',hide_index=True,num_rows=num_rows,disabled=disabled or [],column_config=cols,key=key)

def apply_records(key,df,disabled=None,money_cols=None):
    source=pd.DataFrame(m[key])
    for col in df.columns:
        if col not in source:source[col]=pd.Series(dtype=df[col].dtype)
    changed=editor(df,key=f'edit_{key}_{page}',disabled=disabled,money_cols=money_cols)
    if st.button('Apply changes',key=f'apply_{key}_{page}',type='primary'):
        m[key]=changed.where(pd.notna(changed),None).to_dict('records');st.rerun()

def calc():return compute(m)

def assumptions_group(title,description,names):
    st.subheader(title);st.caption(description)
    a=m['assumptions']
    rows=[{'Assumption':k,'Value':float(a.get(k,0))} for k in names]
    data=editor(pd.DataFrame(rows),f'assumptions_{title}',disabled=['Assumption'],num_rows='fixed')
    if st.button(f'Save {title}',key=f'save_{title}',type='primary'):
        for record in data.to_dict('records'):a[record['Assumption']]=float(record['Value']) if pd.notna(record['Value']) else 0.
        st.rerun()

if page=='Dashboard':
    c,d,s,x=calc()
    if c.empty:st.info('Your model is blank. Open My models above to load the fictional example, or begin in Business Inputs.')
    else:
        revenue=c['Revenue'].sum();cost=c['Cost-to-serve'].sum();profit=revenue-cost
        for col,(lab,val) in zip(st.columns(5),[('Active customers',f'{len(c):,}'),('Annual revenue',money(revenue)),('Cost-to-serve',money(cost)),('Gross profit',money(profit)),('Gross margin',f'{profit/revenue:.2%}' if revenue else '—')]):col.metric(lab,val)
        st.metric('Capacity utilisation',f"{x['utilisation']:.2%}")
        aa,bb=st.columns(2)
        with aa:st.plotly_chart(px.bar(c.sort_values('Gross profit'),x='Customer',y='Gross profit',title='Gross profit by customer',color_discrete_sequence=['#315e48']),width='stretch')
        with bb:st.plotly_chart(px.bar(c.sort_values('Gross margin'),x='Customer',y='Gross margin',title='Gross margin by customer',color_discrete_sequence=['#ca863b']),width='stretch')
        view(c)
elif page=='Business Inputs':
    st.info('Changes to business inputs flow through the cost-to-serve model when saved. Storage capacity is measured in pallet-equivalent positions.')
    a=m['assumptions']
    general=['Days operational per week','Hours operational per day','Weeks per year','Warehouse direct labour rate incl. on-costs','Supervisor / admin rate incl. on-costs','MHE operating cost','Default cost markup','Base Overhead Weighting','Transaction Overhead Weighting','Minimum monthly customer overhead']
    positions=['General pallet positions','Shelf locations','IBC locations','Super Oversize','Oversize locations','Oversize rail locations']
    space=['General pallet','Shelf','IBC','High pallet','Oversize','Oversize rail','Target chargeable occupancy']
    for group in [general,positions,space]:
        for name in group:a.setdefault(name,1.2 if name=='IBC' else 0.)
    assumptions_group('General Business','Operating days, hours, labour and commercial assumptions.',general)
    assumptions_group('Positions Available','Editable physical location counts by storage type; linked to model capacity.',positions)
    assumptions_group('Space Utilisation','Pallet-equivalent multiplier: General pallet = 1.00; IBC = 1.20 means each IBC uses 1.20 times the space of a standard pallet. Occupancy is entered as a decimal (e.g. 0.90 for 90%).',space)
    _,_,_,x=calc()
    st.metric('Practical pallet-equivalent capacity',f"{x['capacity']:,.2f}")
elif page=='P&L Allocation':
    st.subheader('Warehouse P&L')
    st.caption('Annual cost entries. Allocation factor is retained internally but hidden from the table; costs shown are not automatically changed by editing a display value.')
    records=m['pnl'];cols=['description','amount','pool','behaviour']
    df=pd.DataFrame([{col:row.get(col) for col in cols} for row in records],columns=cols)
    df=df.rename(columns={'description':'Description','amount':'Annual amount','pool':'Cost pool','behaviour':'Behaviour'})
    ed=editor(df,'pnl_table',money_cols=['Annual amount'])
    if st.button('Save P&L changes',type='primary'):
        new=[]
        for i,r in enumerate(ed.to_dict('records')):
            base=records[i].copy() if i<len(records) else {'allocation':1}
            base.update({'description':r['Description'],'amount':r['Annual amount'],'pool':r['Cost pool'],'behaviour':r['Behaviour']})
            new.append(base)
        m['pnl']=new;st.rerun()
    _,_,_,x=calc();st.subheader('Allocated annual cost pools')
    view(pd.DataFrame([{'Cost pool':k,'Annual amount':v} for k,v in x['pools'].items()]),money_cols=['Annual amount'])
elif page=='Service Rate Card':
    st.subheader('Service Rate Card')
    st.caption('Update services here. Added or removed active services automatically appear in Customer Volumes and Customer Rates.')
    df=pd.DataFrame(m['services']);apply_records('services',df,money_cols=['material','standard_rate','cost_override'])
    _,_,s,_=calc();st.subheader('Calculated service economics')
    if not s.empty:
        visible=[k for k in ['category','name','unit','minutes','mhe_minutes','material','labour','driver','cost','markup','standard_rate','active'] if k in s]
        view(s[visible])
elif page=='Customers':
    st.subheader('Customer register')
    if st.button('Add customer'):
        m['customers'].append({'id':uuid.uuid4().hex,'name':'New customer','active':True,'volumes':{},'rates':{}});st.rerun()
    df=pd.DataFrame([{'Customer':c['name'],'Active':c.get('active',True),'Customer ID':c['id']} for c in m['customers']])
    if len(df):
        ed=editor(df,'customer_register',disabled=['Customer ID'],num_rows='fixed')
        if st.button('Save customer changes',type='primary'):
            lookup={r['Customer ID']:r for r in ed.to_dict('records')}
            for c in m['customers']:
                c['name']=lookup[c['id']]['Customer'];c['active']=bool(lookup[c['id']]['Active'])
            st.rerun()
    else:st.info('Add your first customer.')
elif page in ('Customer Volumes','Customer Rates'):
    st.subheader(page+' · All-customer matrix')
    services=[s['name'] for s in m['services'] if s.get('active',True)]
    customers=m['customers']
    if not customers:st.info('Add customers first on the Customers page.')
    elif not services:st.info('Add active services first in the Service Rate Card.')
    else:
        field='volumes' if page=='Customer Volumes' else 'rates'
        st.caption('Each row is a customer; each service occupies one column. Scroll horizontally for additional services. Blank rate = standard rate; 0 = an explicit zero charge. Storage volumes are average weekly positions; other volumes are annual.')
        rows=[]
        for c in customers:
            row={'Customer':c['name']}
            row.update({name:c.get(field,{}).get(name,None) for name in services})
            row['Customer ID']=c['id'];rows.append(row)
        df=pd.DataFrame(rows)
        ed=editor(df,f'matrix_{field}',disabled=['Customer','Customer ID'],num_rows='fixed',money_cols=services if field=='rates' else [])
        if st.button('Save matrix changes',type='primary'):
            mapping={r['Customer ID']:r for r in ed.to_dict('records')}
            for c in customers:
                old={k:v for k,v in c.get(field,{}).items() if k not in services}
                old.update({k:float(mapping[c['id']][k]) for k in services if pd.notna(mapping[c['id']][k])})
                c[field]=old
            st.rerun()
        st.caption(f'{len(customers)} customers × {len(services)} active services')
elif page=='Cost-to-Serve':
    c,d,s,x=calc();st.subheader('Customer cost-to-serve')
    view(c)
    if not c.empty:
        ids={f"{r['Customer']} · {r['Customer ID'][:8]}":r['Customer ID'] for _,r in c.iterrows()}
        selected=st.selectbox('Select customer',list(ids))
        cust=c[c['Customer ID']==ids[selected]].iloc[0]
        cols=st.columns(4)
        for col,(k,v) in zip(cols,[('Revenue',money(cust['Revenue'])),('Cost-to-serve',money(cust['Cost-to-serve'])),('Gross profit',money(cust['Gross profit'])),('Gross margin',f"{cust['Gross margin']:.2%}")]):col.metric(k,v)
        detail=d[d['Customer']==cust['Customer']] if not d.empty else pd.DataFrame()
        if not detail.empty:
            a,b=st.columns(2)
            with a:
                pie=pd.DataFrame([{'Type':k,'Amount':cust[k]} for k in ['Storage cost','Activity cost','Overhead cost','Pass-through cost']])
                st.plotly_chart(px.pie(pie,names='Type',values='Amount',title='Cost composition',hole=.53,color_discrete_sequence=['#315e48','#ca863b','#84a993','#b9c8bc']),width='stretch')
            with b:
                cat=detail.groupby('Category',as_index=False)[['Revenue','Cost','Profit']].sum()
                chart=cat.melt(id_vars='Category',value_vars=['Revenue','Cost','Profit'],var_name='Measure',value_name='AUD')
                st.plotly_chart(px.bar(chart,x='Category',y='AUD',color='Measure',barmode='group',title='Revenue, cost and profit by service category',color_discrete_sequence=['#315e48','#ca863b','#95b2a0']),width='stretch')
            st.subheader('Service profitability detail');view(detail)
        st.caption(f"Customer ID: {cust['Customer ID']}")
    st.warning(f"Activity reconciliation: modelled customer costs {money(x['modelled_activity'])}; P&L pool {money(x['pools']['Activity'])}; gap {money(x['activity_pnl_gap'])}. This is a reconciliation gap, not an additional customer charge.")
elif page=='Rate Card Analysis':
    c,d,s,x=calc();st.subheader('Rate Card Analysis')
    if d.empty:st.info('Enter customer service volumes before analysing the rate card.')
    else:
        g=d.groupby('Service',as_index=False).agg(Volume=('Volume','sum'),Revenue=('Revenue','sum'),Cost=('Cost','sum'))
        g['Weighted rate']=g['Revenue']/g['Volume'].replace(0,float('nan'))
        ss=s.drop_duplicates('name').set_index('name')
        g['Unit cost']=g['Service'].map(ss['cost']);g['Target rate']=g['Service'].map(ss['standard_rate'])
        g['Rate gap']=g['Target rate']-g['Weighted rate']
        g['Status']=g.apply(lambda r:'Below cost' if r['Weighted rate']<r['Unit cost'] else 'Below target' if r['Weighted rate']<r['Target rate'] else 'On / above target',axis=1)
        view(g,money_cols=['Weighted rate','Unit cost','Target rate','Rate gap','Revenue','Cost'])
        if st.button('AI review: add commentary for each service',type='primary'):
            try:
                from openai import OpenAI
                api_key=st.secrets.get('OPENAI_API_KEY','')
                if not api_key:st.warning('AI review is not configured. Add OPENAI_API_KEY to Streamlit app secrets. No data has been sent.')
                else:
                    input_rows=g[['Service','Volume','Weighted rate','Unit cost','Target rate','Rate gap','Status']].round(2).to_dict('records')
                    prompt='Review this warehouse 3PL pricing data and return a concise Markdown table with columns Service | Assessment | Suggested action. Cover EVERY row, flag below-cost prices and rates below target, and state OK where pricing is adequate. Do not fabricate costs or volumes. Data: '+json.dumps(input_rows)
                    with st.spinner('Reviewing service pricing...'):
                        response=OpenAI(api_key=api_key).responses.create(model='gpt-4.1-mini',input=prompt)
                    st.session_state.rate_ai_commentary=response.output_text
            except Exception as exc:st.error(f'AI review failed: {exc}')
        if st.session_state.get('rate_ai_commentary'):
            st.subheader('AI pricing commentary');st.markdown(st.session_state.rate_ai_commentary)
            st.caption('AI commentary is advisory and should be checked before commercial decisions.')
elif page=='New Customer Modelling':
    st.subheader('Prospective customer modelling')
    st.caption('Proposal is a separate calculation and will not affect your active customer register until approved.')
    if not m['services']:st.info('Add services first in Service Rate Card.')
    else:
        name=st.text_input('Prospect name','Prospective customer')
        data=pd.DataFrame([{'Service':z['name'],'Annual volume / average storage positions':0.,'Proposed rate (blank uses standard)':None} for z in m['services'] if z.get('active',True)])
        edited=editor(data,'prospect',disabled=['Service'],money_cols=['Proposed rate (blank uses standard)'])
        if st.button('Calculate prospect'):
            prospect={'id':uuid.uuid4().hex,'name':name,'active':True,'volumes':{z['Service']:z['Annual volume / average storage positions'] for z in edited.to_dict('records')},'rates':{z['Service']:z['Proposed rate (blank uses standard)'] for z in edited.to_dict('records') if pd.notna(z['Proposed rate (blank uses standard)'])}}
            clone=json.loads(json.dumps(m));clone['customers'].append(prospect)
            future,_,_,_=compute(clone)
            result=future[future['Customer ID']==prospect['id']].iloc[0]
            a,b,c=st.columns(3);a.metric('Annual revenue',money(result['Revenue']));b.metric('Fully loaded gross profit',money(result['Gross profit']));c.metric('Gross margin',f"{result['Gross margin']:.2%}")
            st.session_state.prospect=prospect
            st.caption('Incremental profitability is not independently verified; dedicated resource and step-fixed costs require additional assumptions.')
        if 'prospect' in st.session_state and st.button('Approve and add customer'):
            m['customers'].append(st.session_state.prospect);del st.session_state.prospect;st.rerun()
elif page=='Scenarios':
    st.subheader('Rate scenarios')
    base,_,_,_=calc();uplift=st.slider('Change all standard and negotiated rates (%)',-50,100,10)
    clone=json.loads(json.dumps(m))
    for service in clone['services']:
        if service.get('standard_rate') is not None:service['standard_rate']*=1+uplift/100
        else:service['markup']=(1+service.get('markup',clone['assumptions'].get('Default cost markup',.25)))*(1+uplift/100)-1
    for cust in clone['customers']:cust['rates']={k:v*(1+uplift/100) for k,v in cust.get('rates',{}).items() if v is not None}
    scenario,_,_,_=compute(clone)
    if not base.empty:
        a,b=st.columns(2);a.metric('Baseline profit',money(base['Gross profit'].sum()));b.metric('Scenario profit',money(scenario['Gross profit'].sum()),delta=money(scenario['Gross profit'].sum()-base['Gross profit'].sum()))
        view(scenario)
    if st.button('Save scenario as a new model'):
        clone['name']=m['name']+f' | Rates {uplift:+d}%';save(clone);st.success('Scenario saved separately.')
elif page=='Reports & Exports':
    st.subheader('Reports and exports');c,d,s,x=calc();out=io.BytesIO()
    with pd.ExcelWriter(out,engine='xlsxwriter') as writer:
        for title,df in [('Customers',c),('Activity Detail',d),('Service Rates',s),('P&L',pd.DataFrame(m['pnl'])),('Assumptions',pd.DataFrame([{'Assumption':k,'Value':v} for k,v in m['assumptions'].items()]))]:
            df.to_excel(writer,sheet_name=title,index=False)
            sheet=writer.sheets[title];sheet.freeze_panes(1,0);sheet.set_row(0,None,writer.book.add_format({'bold':True,'bg_color':'#315e48','font_color':'white','align':'center'}))
            for i,col in enumerate(df.columns):
                kind='$#,##0.00' if col in MONEY or col=='amount' else '#,##0.00'
                fmt=writer.book.add_format({'num_format':kind,'align':'center'})
                sheet.set_column(i,i,min(max(16,len(str(col))+3),33),fmt)
    st.download_button('Download formatted financial workbook',out.getvalue(),file_name='extolla_cost_to_serve.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    st.download_button('Download model JSON',json.dumps(m,indent=2),file_name='extolla_cost_to_serve.json')
    st.info('Professional PDF reporting and direct import of the supplied legacy Excel workbook are not implemented in this version.')
