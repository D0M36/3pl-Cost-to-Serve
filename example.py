"""Synthetic illustrative case. No actual customer records, amounts or negotiated rates."""
import random,uuid

def blank():
    return {'name':'New warehouse','assumptions':{'General pallet positions':0,'Target chargeable occupancy':.9,'Weeks per year':52,'Warehouse direct labour rate incl. on-costs':45,'Supervisor / admin rate incl. on-costs':80,'MHE operating cost':12,'Default cost markup':.25,'Base Overhead Weighting':.2,'Transaction Overhead Weighting':.8,'General pallet':1,'Shelf':.25,'IBC':1.1,'High pallet':1.2,'Oversize':2,'Oversize rail':2},'pnl':[],'services':[],'customers':[]}

def example():
    r=random.Random(1704)
    m=blank();m['name']='Example 3PL warehouse (fictional)'
    m['assumptions'].update({'General pallet positions':4200,'Shelf locations':130,'IBC locations':18,'Oversize locations':100,'Oversize rail locations':25,'Target chargeable occupancy':.85})
    pools=[('Warehouse rent',460000,'Storage'),('Property utilities',46000,'Storage'),('Insurance and security',29000,'Storage'),('Warehouse wages',470000,'Activity'),('Equipment hire',61000,'Activity'),('Operations supervision',105000,'Activity'),('Warehouse software',49000,'Customer Overhead'),('Admin support',73000,'Customer Overhead'),('Packaging supply',18000,'Direct Pass-through')]
    m['pnl']=[{'description':d,'amount':a,'pool':p,'allocation':1,'behaviour':'Fixed' if p=='Storage' else 'Variable'} for d,a,p in pools]
    records=[('Inbound','20ft palletised container','Per container',42,24,0,'Activity'),('Inbound','40ft palletised container','Per container',85,42,0,'Activity'),('Inbound','Hand unloaded container','Per container',450,55,0,'Activity'),('Inbound','LCL pallets received','Per pallet',4,2,0,'Activity'),('Inbound','Pallet wrap','Per pallet',3,0,2.5,'Activity'),('Inbound','Pallet putaway','Per pallet',4,3,0,'Activity'),('Outbound','Order processing','Per order',2,0,0,'Activity'),('Outbound','Carton pick','Per carton',2.5,0,0,'Activity'),('Outbound','Pallet dispatch','Per pallet',5,3,0,'Activity'),('Outbound','Heavy item pick','Per item',8,2,0,'Activity'),('Consumables','Dispatch carton','Per carton',0,0,1.4,'Pass-through'),('VAS','Relabelling','Per label',1,0,.1,'Activity'),('Administration','Urgent order administration','Per order',10,0,0,'Activity')]
    m['services']=[{'name':name,'category':cat,'unit':unit,'minutes':minutes,'mhe_minutes':mh,'material':material,'labour':'Direct','markup':.3,'driver':driver,'active':True} for cat,name,unit,minutes,mh,material,driver in records]
    for name in ['General Storage','Shelf','IBC','Oversize','Oversize Rails']:
        m['services'].append({'name':name,'category':'Storage','unit':'Per position / week','minutes':0,'mhe_minutes':0,'material':0,'labour':'None','markup':0,'driver':'Storage','active':True,'standard_rate':{'General Storage':5.8,'Shelf':2.8,'IBC':7.2,'Oversize':12,'Oversize Rails':11}[name]})
    for i in range(16):
        storage=r.randint(40,250)
        volumes={'General Storage':storage,'Shelf':r.randint(0,20),'IBC':r.randint(0,8),'Oversize':r.randint(0,12),'Oversize Rails':r.randint(0,6)}
        for s in m['services']:
            if s['driver']=='Storage':continue
            volumes[s['name']]=r.randint(0,25) if 'container' in s['name'].lower() else r.randint(80,2500)
        m['customers'].append({'id':uuid.uuid5(uuid.NAMESPACE_DNS,f'fictional-client-{i}').hex,'name':f'Example Customer {i+1:02d}','active':True,'volumes':volumes,'rates':{}})
    return m
