"""Independent warehouse CTS engine. Annual volumes; weekly storage positions."""
import pandas as pd

def number(x, default=0.):
    try:
        v=float(x)
        return v if pd.notna(v) else default
    except (ValueError,TypeError): return default

def compute(model):
    assumptions=model.get('assumptions',{})
    direct=number(assumptions.get('Warehouse direct labour rate incl. on-costs',45))
    supervisor=number(assumptions.get('Supervisor / admin rate incl. on-costs',80))
    mhe=number(assumptions.get('MHE operating cost',12))
    weeks=number(assumptions.get('Weeks per year',52),52)
    occupancy=number(assumptions.get('Target chargeable occupancy',.9))
    eq={'General Storage':number(assumptions.get('General pallet',1)), 'Shelf':number(assumptions.get('Shelf',.25)), 'IBC':number(assumptions.get('IBC',1.2)), 'High Pallet':number(assumptions.get('High pallet',1.2)), 'Oversize':number(assumptions.get('Oversize',2)), 'Oversize Rails':number(assumptions.get('Oversize rail',2))}
    cap={'General Storage':number(assumptions.get('General pallet positions',0)), 'Shelf':number(assumptions.get('Shelf locations',0)), 'IBC':number(assumptions.get('IBC locations',0)), 'High Pallet':number(assumptions.get('Super Oversize',0)), 'Oversize':number(assumptions.get('Oversize locations',0)), 'Oversize Rails':number(assumptions.get('Oversize rail locations',0))}
    capacity=sum(cap[k]*eq[k] for k in eq)*occupancy
    pools={'Storage':0.,'Activity':0.,'Customer Overhead':0.,'Direct Pass-through':0.,'Exclude':0.}
    for line in model.get('pnl',[]):
        pool=line.get('pool','Exclude')
        pools[pool]=pools.get(pool,0)+number(line.get('amount'))*number(line.get('allocation',1))
    storage_cost_per_pw=pools['Storage']/max(1,capacity*weeks)
    services={}
    for s in model.get('services',[]):
        if not s.get('active',True):continue
        name=s['name'];driver=s.get('driver','Activity')
        if driver=='Storage':cost=number(s.get('cost_override',0))
        else:
            wage=direct if s.get('labour','Direct')=='Direct' else supervisor if s.get('labour')=='Supervisor' else 0
            cost=(number(s.get('minutes'))*wage+number(s.get('mhe_minutes'))*mhe)/60+number(s.get('material'))
        markup=number(s.get('markup',assumptions.get('Default cost markup',.25)))
        services[name]={**s,'cost':cost,'standard_rate':number(s.get('standard_rate',cost*(1+markup))),'markup':markup,'driver':driver}
    active=[c for c in model.get('customers',[]) if c.get('active',True)]
    weight_equal=number(assumptions.get('Base Overhead Weighting',.2))
    weight_tx=number(assumptions.get('Transaction Overhead Weighting',.8))
    txs={c['id']:sum(max(0,number(v)) for name,v in c.get('volumes',{}).items() if name in services and services[name]['driver']!='Storage') for c in active}
    total_tx=sum(txs.values())
    items=[];details=[]
    for c in active:
        sid=c['id'];volume_map=c.get('volumes',{}); rates=c.get('rates',{})
        pw=sum(number(volume_map.get(k))*eq[k]*weeks for k in eq)
        sc=pw*storage_cost_per_pw
        ac=pc=rev=sr=ar=pr=0.
        for name,s in services.items():
            qty=number(volume_map.get(name));
            if s['driver']=='Storage':qty=number(volume_map.get(name))*weeks
            if qty==0:continue
            rate=number(rates[name]) if name in rates and rates[name] is not None else s['standard_rate']
            revenue=qty*rate
            if s['driver']=='Storage':cost=number(s.get('cost_override',0))*qty;sr+=revenue
            elif s['driver']=='Pass-through':cost=s['cost']*qty;pc+=cost;pr+=revenue
            else:cost=s['cost']*qty;ac+=cost;ar+=revenue
            rev+=revenue
            details.append({'Customer':c['name'],'Service':name,'Category':s.get('category','Other'),'Driver':s['driver'],'Volume':qty,'Unit cost':s['cost'],'Customer rate':rate,'Revenue':revenue,'Cost':cost,'Profit':revenue-cost})
        overhead=pools['Customer Overhead']*(weight_equal/max(1,len(active))+weight_tx*(txs[sid]/total_tx if total_tx else 1/max(1,len(active))))
        overhead=max(overhead,number(assumptions.get('Minimum monthly customer overhead',0))*12)
        total=sc+ac+pc+overhead
        if c.get('revenue_override') is not None:rev=number(c['revenue_override'])
        items.append({'Customer':c['name'],'Customer ID':sid,'Revenue':rev,'Storage cost':sc,'Activity cost':ac,'Overhead cost':overhead,'Pass-through cost':pc,'Cost-to-serve':total,'Gross profit':rev-total,'Gross margin':(rev-total)/rev if rev else 0,'Equivalent pallet weeks':pw,'Transaction activity':txs[sid]})
    customer_df=pd.DataFrame(items)
    detail_df=pd.DataFrame(details)
    storage_used=sum(row['Equivalent pallet weeks'] for row in items)/max(weeks,1)
    stats={'capacity':capacity,'used':storage_used,'utilisation':storage_used/capacity if capacity else 0,'pools':pools,'storage_cost_per_pw':storage_cost_per_pw,'modelled_activity':customer_df['Activity cost'].sum() if len(customer_df) else 0,'activity_pnl_gap':pools['Activity']-(customer_df['Activity cost'].sum() if len(customer_df) else 0)}
    return customer_df,detail_df,pd.DataFrame(services.values()),stats
