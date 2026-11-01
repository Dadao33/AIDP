"""Reproducible two-model training, chronology and held-out metrics."""
import numpy as np
FEATURES=['coverage_days','lead_days','promo_uplift','delay_days','volatility']
def train(rows):
    X=np.array([[float(r[f]) for f in FEATURES] for r in rows]);y=np.array([int(r['not_served_7d']) for r in rows]);split=np.array([r['split'] for r in rows]);tr=split=='train';va=split=='validation';te=split=='test'
    if not all(mask.sum()>0 for mask in (tr,va,te)):raise ValueError('Missing chronological split')
    mean,std=X[tr].mean(0),X[tr].std(0);Z=np.column_stack([np.ones(len(X)),(X-mean)/std]);w=np.zeros(6)
    for _ in range(2200):
        p=1/(1+np.exp(-np.clip(Z[tr]@w,-30,30)));w-=.11*(Z[tr].T@(p-y[tr])/tr.sum()+np.r_[0,w[1:]*.0003])
    prob=1/(1+np.exp(-np.clip(Z@w,-30,30)))
    def metrics(mask,t):
        a=y[mask];p=prob[mask];tp=int(((p>=t)&(a==1)).sum());fp=int(((p>=t)&(a==0)).sum());fn=int(((p<t)&(a==1)).sum());tn=int(((p<t)&(a==0)).sum());ranks=np.empty(len(p));ranks[np.argsort(p)]=np.arange(1,len(p)+1);pos=a.sum();neg=len(a)-pos
        return dict(roc_auc=float((ranks[a==1].sum()-pos*(pos+1)/2)/(pos*neg)),brier=float(np.mean((p-a)**2)),precision=tp/max(tp+fp,1),recall=tp/max(tp+fn,1),rows=len(a),confusion=dict(tp=tp,fp=fp,fn=fn,tn=tn))
    ts=np.arange(.2,.81,.02);ms=[metrics(va,t) for t in ts];threshold=float(ts[np.argmax([2*x['precision']*x['recall']/max(x['precision']+x['recall'],1e-9) for x in ms])])
    daily=np.array([float(r['daily_units_28d']) for r in rows]);season=np.array([float(r['season_index']) for r in rows]);demand=np.array([float(r['demand_next_7d']) for r in rows]);F=np.column_stack([np.ones(len(rows)),np.log(daily*7),X[:,2],np.log(season)]);fw=np.linalg.lstsq(F[tr],np.log(demand[tr]),rcond=None)[0];forecast=np.exp(F@fw)
    return dict(version='bic-service-risk-v2',features=FEATURES,labels=['Available cover','Replenishment lead time','Promotion uplift','Inbound delay','Demand volatility'],mean=mean.tolist(),std=std.tolist(),weights=w.tolist(),threshold=threshold,forecast_weights=fw.tolist(),metrics=metrics(te,threshold),validation=metrics(va,threshold),forecast_wape=float(abs(forecast[te]-demand[te]).sum()/demand[te].sum()),baseline_wape=float(abs(daily[te]*7-demand[te]).sum()/demand[te].sum()),split={k:int((split==k).sum()) for k in ['train','validation','test']},seed=4217,synthetic=True,target='At least one order line not served in full within seven days',limitations='Synthetic outcomes; not BIC production accuracy. Conditional association, not causal proof. Daily shape is a planning allocation of the learned weekly total.')
