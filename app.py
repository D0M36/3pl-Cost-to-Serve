import io,json,uuid
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from engine import compute
from example import blank,example
from store import save,load,all_models

st.set_page_config(page_title='Extolla | Cost-to-Serve',page_icon='📊',layout='wide')
st.markdown('''<style>
[data-testid="stSidebar"]{background:#f6f8f7}h1,h2,h3{color:#40584e}div.stButton>button[kind="primary"]{background:#bf742f;border-color:#bf742f;color:white}div[data-testid="stMetric"]{background:#f6f8f7;border:1px solid #dce6e0;border-radius:10px;padding:12px}
</style>''',unsafe_allow_html=True)
if 'model' not in st.session_state:
    st.session_state.model=blank();st.session_state.model_id=None
m=st.session_state.model
with st.sidebar:
    logo_path = Path(__file__).resolve().parent / 'assets' / 'extolla_logo.png'
    if logo_path.is_file():
        st.image(str(logo_path), width='stretch')
    else:
        st.markdown('## EXTOLLA')
    st.caption('COST-TO-SERVE MODELLER')
    page=st.radio('Navigation',['Dashboard','Business Inputs','P&L Allocation','Service Rate Card','Customers','Customer Volumes','Customer Rates','Cost-to-Serve','Rate Card Analysis','New Customer Modelling','Scenarios','Reports & Exports'],label_visibility='collapsed')
    st.divider();st.markdown('**My models**')
    if st.button('New blank model',width='stretch'):st.session_state.model=blank();st.session_state.model_id=None;st.rerun()
    if st.button('Load fictional example',width='stretch'):st.session_state.model=example();st.session_state.model_id=None;st.rerun()
    models=all_models()
    selected=st.selectbox('Saved models',['Select model']+[x['name']+' • '+x['id'][:8] for x in models])
    if st.button('Open saved model',width='stretch') and selected!='Select model':
        mid=models[['Select model']+[x['name']+' • '+x['id'][:8] for x in models].index(selected)-1]['id']
        st.session_state.model=load(mid);st.session_state.model_id=mid;st.rerun()
    m['name']=st.text_input('Model name',value=m['name'])
    if st.button('Save current model',type='primary',width='stretch'):
        st.session_state.model_id=save(m,st.session_state.model_id);st.success('Saved')
    if st.button('Save as new copy',width='stretch'):
        st.session_state.model_id=save(m);st.success('Copy saved')
    incoming=st.file_uploader('Import model JSON',type='json')
    if incoming and st.button('Import JSON'):
        st.session_state.model=json.load(incoming);st.session_state.model_id=None;st.rerun()
    st.download_button('Export model JSON',json.dumps(m,indent=2),file_name='extolla_model.json',mime='application/json',width='stretch')

st.title('Cost-to-Serve & Profitability')
st.caption(f"Warehouse: {m['name']} | Annualised financial view | AUD")

def edit_records(key,columns=None):
    df=pd.DataFrame(m[key]);edited=st.data_editor(df,num_rows='dynamic',width='stretch',key=f'editor_{key}_{page}',column_config=columns or {})
    if st.button('Apply changes',key=f'apply_{key}_{page}'):
        m[key]=edited.where(pd.notna(edited),None).to_dict('records');st.rerun()

def rowcol():
    cdf,ddf,sdf,stats=compute(m)
    return cdf,ddf,sdf,stats

def show_money(v):return f'${v:,.0f}'

if page=='Dashboard':
    c,d,s,x=rowcol()
    if c.empty:st.info('Your model is blank. Start with Business Inputs, or select “Load fictional example” in the sidebar.');st.stop()
    revenue=c['Revenue'].sum();cost=c['Cost-to-serve'].sum();profit=revenue-cost
    cols=st.columns(5)
    for col,(lab,value) in zip(cols,[('Customers',str(len(c))),('Revenue',show_money(revenue)),('Cost-to-serve',show_money(cost)),('Gross profit',show_money(profit)),('Gross margin',f'{profit/revenue:.1%}' if revenue else '—')]):col.metric(lab,value)
    st.metric('Capacity utilisation',f"{x['utilisation']:.1%}")
    a,b=st.columns(2)
    with a:st.plotly_chart(px.bar(c.sort_values('Gross profit'),x='Customer',y='Gross profit',title='Gross profit by customer'),width='stretch')
    with b:st.plotly_chart(px.bar(c.sort_values('Gross margin'),x='Customer',y='Gross margin',title='Gross margin by customer'),width='stretch')
    st.dataframe(c.style.format({'Revenue':'${:,.0f}','Cost-to-serve':'${:,.0f}','Gross profit':'${:,.0f}','Gross margin':'{:.1%}'}),width='stretch')
elif page=='Business Inputs':
    st.subheader('Operating assumptions');st.caption('Values are editable; all outputs recalculate from this data.')
    a=pd.DataFrame([{'Assumption':k,'Value':v} for k,v in m['assumptions'].items()]);e=st.data_editor(a,num_rows='dynamic',width='stretch')
    if st.button('Apply assumptions'):m['assumptions']={str(x['Assumption']):float(x['Value']) for x in e.to_dict('records') if pd.notna(x['Value'])};st.rerun()
elif page=='P&L Allocation':
    st.subheader('Warehouse P&L allocation');edit_records('pnl')
    _,_,_,x=rowcol();st.write('Annual P&L cost pools');st.dataframe(pd.DataFrame([{'Pool':k,'Cost':v} for k,v in x['pools'].items()]),hide_index=True)
elif page=='Service Rate Card':
    st.subheader('Service definitions & productivity');st.caption('Leave standard_rate blank to calculate automatically from labour, MHE, material and markup. Storage rates are quoted per position-week.')
    edit_records('services');_,_,s,_=rowcol();st.subheader('Calculated rates');st.dataframe(s,width='stretch')
elif page=='Customers':
    st.subheader('Customer register')
    if st.button('Add customer'):
        m['customers'].append({'id':uuid.uuid4().hex,'name':'New customer','active':True,'volumes':{},'rates':{}});st.rerun()
    table=pd.DataFrame([{'id':x['id'],'name':x['name'],'active':x.get('active',True)} for x in m['customers']])
    if not table.empty:
        edited=st.data_editor(table,num_rows='fixed',width='stretch',disabled=['id'])
        if st.button('Apply customer changes'):
            rec=edited.set_index('id').to_dict('index')
            for x in m['customers']:x.update(rec[x['id']])
            st.rerun()
    else:st.info('No customers yet.')
elif page in ('Customer Volumes','Customer Rates'):
    st.subheader(page)
    if not m['customers']:st.info('Add a customer first on Customers.');st.stop()
    chosen=st.selectbox('Customer',[c['name'] for c in m['customers']]);cust=next(c for c in m['customers'] if c['name']==chosen)
    names=[s['name'] for s in m['services'] if s.get('active',True)]
    field='volumes' if page=='Customer Volumes' else 'rates'
    data=pd.DataFrame([{'Service':n,'Value':cust.get(field,{}).get(n,None)} for n in names]);edited=st.data_editor(data,disabled=['Service'],width='stretch')
    if st.button('Apply values'):
        cust[field]={z['Service']:float(z['Value']) for z in edited.to_dict('records') if pd.notna(z['Value'])};st.rerun()
    st.caption('Volume inputs are annual, except storage positions (average positions used per week). Blank rate = standard rate; zero = intentional free service.')
elif page=='Cost-to-Serve':
    c,d,s,x=rowcol();st.subheader('Customer profitability');st.dataframe(c,width='stretch')
    if not d.empty:
        chosen=st.selectbox('Customer activity detail',sorted(d['Customer'].unique()));st.dataframe(d[d.Customer==chosen],width='stretch')
    st.warning(f"Reconciliation: modelled customer activity cost {show_money(x['modelled_activity'])}; allocated P&L activity pool {show_money(x['pools']['Activity'])}; difference {show_money(x['activity_pnl_gap'])}. This is a reconciliation difference, not an additional customer charge.")
elif page=='Rate Card Analysis':
    c,d,s,x=rowcol();st.subheader('Commercial pricing opportunities')
    if d.empty:st.info('Enter customer activity volumes first.');st.stop()
    g=d.groupby('Service').agg(Volume=('Volume','sum'),Revenue=('Revenue','sum'),Cost=('Cost','sum')).reset_index()
    g['Weighted rate']=g['Revenue']/g['Volume'].where(g['Volume']!=0,1)
    rates=s.set_index('name')['cost'];g['Unit cost']=g['Service'].map(rates);g['Target rate']=g['Service'].map(s.set_index('name')['standard_rate'])
    g['Annual repricing opportunity']=(g['Target rate']*g['Volume']-g['Revenue']).clip(lower=0)
    st.dataframe(g.sort_values('Annual repricing opportunity',ascending=False),width='stretch')
elif page=='New Customer Modelling':
    st.subheader('Prospective customer simulation')
    st.caption('The proposal is modelled separately: it will not change your live customer register unless you explicitly approve it.')
    if not m['services']:st.info('Set up services before modelling a new customer.');st.stop()
    name=st.text_input('Prospect name','Prospective customer')
    data=pd.DataFrame([{'Service':z['name'],'Annual volume / average storage positions':0.,'Proposed rate (blank uses standard)':None} for z in m['services'] if z.get('active',True)])
    edited=st.data_editor(data,width='stretch',disabled=['Service'])
    if st.button('Calculate prospect'):
        prospect={'id':uuid.uuid4().hex,'name':name,'active':True,'volumes':{z['Service']:z['Annual volume / average storage positions'] for z in edited.to_dict('records')},'rates':{z['Service']:z['Proposed rate (blank uses standard)'] for z in edited.to_dict('records') if pd.notna(z['Proposed rate (blank uses standard)'])}}
        copy=json.loads(json.dumps(m));copy['customers'].append(prospect)
        new,_,_,_=compute(copy);old,_,_,_=compute(m)
        result=new[new['Customer ID']==prospect['id']].iloc[0];st.metric('Estimated annual revenue',show_money(result['Revenue']));st.metric('Fully loaded gross profit',show_money(result['Gross profit']));st.metric('Fully loaded margin',f"{result['Gross margin']:.1%}")
        st.caption('Incremental profitability is not reported as verified: fixed/step-fixed capacity triggers and incremental resources require separate cost inputs.')
        st.session_state.prospect=prospect
    if 'prospect' in st.session_state and st.button('Approve and add prospect to customer register'):
        m['customers'].append(st.session_state.prospect);del st.session_state.prospect;st.rerun()
elif page=='Scenarios':
    st.subheader('Scenario sandbox')
    base,_,_,_=compute(m)
    uplift=st.slider('Apply rate increase (%) to all standard and negotiated rates',-50,100,10)
    clone=json.loads(json.dumps(m))
    for s in clone['services']:
        if s.get('standard_rate') is not None:s['standard_rate']*=1+uplift/100
        else:
            # For auto rate, raise calculated markup to deliver proportional rate uplift
            s['markup']=(1+s.get('markup',clone['assumptions'].get('Default cost markup',.25)))*(1+uplift/100)-1
    for cust in clone['customers']:
        cust['rates']={k:v*(1+uplift/100) for k,v in cust.get('rates',{}).items() if v is not None}
    scenario,_,_,_=compute(clone)
    if not base.empty:
        a,b=st.columns(2)
        a.metric('Baseline gross profit',show_money(base['Gross profit'].sum()))
        b.metric('Scenario gross profit',show_money(scenario['Gross profit'].sum()),delta=show_money(scenario['Gross profit'].sum()-base['Gross profit'].sum()))
    if st.button('Save scenario as new model'):
        clone['name']=m['name']+f' | Rates {uplift:+d}%';save(clone);st.success('Scenario saved as separate model')
elif page=='Reports & Exports':
    c,d,s,x=rowcol();st.subheader('Download reports')
    out=io.BytesIO()
    with pd.ExcelWriter(out,engine='xlsxwriter') as writer:
        for name,df in [('Customers',c),('Activity Detail',d),('Service Rates',s),('P&L',pd.DataFrame(m['pnl'])),('Assumptions',pd.DataFrame([{'Assumption':k,'Value':v} for k,v in m['assumptions'].items()]))]:df.to_excel(writer,sheet_name=name,index=False)
    st.download_button('Download financial workbook',out.getvalue(),file_name='extolla_cost_to_serve.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    st.download_button('Download JSON model',json.dumps(m,indent=2),file_name='extolla_cost_to_serve.json')
    st.info('PDF reporting and direct import of the supplied legacy Excel workbook are not implemented in this initial release.')
